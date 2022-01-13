import os
import click
import torch, torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset, ConcatDataset
import random as rd
from functools import partial
from statistics import mean
from sklearn.model_selection import train_test_split
from copy import copy
from utils1 import elapsed_timer, collate
from data import Task1Dataset, enrich, generate_negative, LANGUAGES
from analogy_classif import Classification
from cnn_embeddings import CNNEmbedding

#from analogy_classif import Classification
#from cnnEmbedding import CNNEmbedding

@click.command()
@click.option('--nb_analogies', '-n', default=550000, 
              help='The maximum number of analogies (before augmentation) we train the model on. If the number is greater than the number of analogies in the dataset, then all the analogies will be used.', show_default=True)
@click.option('--epochs', '-e', default=20,
              help='The number of epochs we train the model for.', show_default=True)
@click.option('--exclude_jap/--use_jap', '-nj/-j', default=False)
@click.option('--original_balance/--our_balance','-B/-b',  default=False)
def train_classifier(nb_analogies, epochs, exclude_jap, original_balance):
    '''Trains a classifier and a word embedding model for a given language.

    Arguments:
    nb_analogies -- The number of analogies to use (before augmentation) for the training.
    epochs -- The number of epochs we train the model for.'''

    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    # --- Prepare data ---

    ## Load train data and unify vocabulary :zD
    train_datasets = dict()
    word_voc = []
    languages = LANGUAGES
    if exclude_jap:
        languages.remove("japanese")
    for lang in languages:
        print(f"Loading data for {lang.capitalize()}...", end="")
        train_datasets[lang] = Task1Dataset(language=lang, mode="train", word_encoding="char")
        print("Done!", end="\n")
        word_voc += train_datasets[lang].word_voc

        if lang == "japanese":
            japanese_train_analogies, japanese_test_analogies = train_test_split(train_datasets[lang].analogies, test_size=0.3, random_state = 42)
            train_datasets[lang].analogies = japanese_train_analogies
    
    word_voc = list(set(word_voc))
    word_voc_id = {character: i for i, character in enumerate(word_voc)}
    for lang in train_datasets.keys():
        train_datasets[lang].word_voc = word_voc
        train_datasets[lang].word_voc_id = word_voc_id

    BOS_ID = len(word_voc_id) # (max value + 1) is used for the beginning of sequence value
    EOS_ID = len(word_voc_id) + 1 # (max value + 2) is used for the end of sequence value
    print("Voc size: ", len(word_voc_id))
    
    # Get subsets
    train_subsets = dict()
    dev_subsets = dict()
    for lang in train_datasets.keys():
        if len(train_datasets[lang]) > nb_analogies//len(train_datasets):
            train_indices = list(range(len(train_datasets[lang])))
            train_sub_indices = rd.sample(train_indices, nb_analogies//len(train_datasets))
            train_subsets[lang] = Subset(train_datasets[lang], train_sub_indices)
        else:
            train_subsets[lang] = train_datasets[lang]

        if len(train_datasets[lang]) > 100:
            dev_indices = list(range(len(train_datasets[lang])))
            dev_sub_indices = rd.sample(dev_indices, 100)
            dev_subsets[lang] = Subset(train_datasets[lang], dev_sub_indices)
        else:
            dev_subsets[lang] = train_datasets[lang]

    # Merge datasets
    train_subset = ConcatDataset(train_subsets.values())
    dev_subset = ConcatDataset(dev_subsets.values())

    # Load data
    train_dataloader = DataLoader(train_subset, shuffle = True, collate_fn = partial(collate, bos_id = BOS_ID, eos_id = EOS_ID), batch_size=16, num_workers=8, pin_memory=True)
    dev_dataloader = DataLoader(dev_subset, collate_fn = partial(collate, bos_id = BOS_ID, eos_id = EOS_ID), batch_size=16, num_workers=8, pin_memory=True)


    # --- Training models ---

    if exclude_jap:
        char_emb_size=64
    else:
        char_emb_size=512

    classification_model = Classification(emb_size=16*5) # 16 because 16 filters of each size, 5 because 5 sizes
    embedding_model = CNNEmbedding(emb_size=char_emb_size, voc_size = len(word_voc_id) + 2) # emb_size is the size of the intermediate character embedding

    # Data paralelism must be done before putting device on CUDA
    if torch.cuda.device_count() > 1:
        print(f"Using DataParallel on {torch.cuda.device_count()} GPUs")
        # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
        classification_model = nn.DataParallel(classification_model, device_ids=list(range(torch.cuda.device_count())))
        embedding_model = nn.DataParallel(embedding_model, device_ids=list(range(torch.cuda.device_count())))
    elif torch.cuda.device_count()==1:
        print(f"Using 1 GPU (no DataParallel)")

    # --- Training Loop ---
    classification_model.to(device)
    embedding_model.to(device)

    optimizer = torch.optim.Adam(list(classification_model.parameters()) + list(embedding_model.parameters()))
    criterion = nn.BCELoss()

    losses_list = []
    dev_losses_list = []
    dev_acc_list = []
    times_list = []

    for epoch in range(epochs):

        losses = []
        with elapsed_timer() as elapsed:
            for a, b, c, d in train_dataloader:

                optimizer.zero_grad()

                # compute the embeddings
                a = embedding_model(a.to(device))
                b = embedding_model(b.to(device))
                c = embedding_model(c.to(device))
                d = embedding_model(d.to(device))

                a = torch.unsqueeze(a, 1)
                b = torch.unsqueeze(b, 1)
                c = torch.unsqueeze(c, 1)
                d = torch.unsqueeze(d, 1)

                # to be able to add other losses, which are tensors, we initialize the loss as a 0 tensor
                loss = torch.tensor(0).to(device).float()
                
                
                if (len(a) == len(b) and torch.all(a == b)) or (len(c) == len(d) and torch.all(c == d)):

                    a = torch.unsqueeze(a, 0)
                    b = torch.unsqueeze(b, 0)
                    c = torch.unsqueeze(c, 0)
                    d = torch.unsqueeze(d, 0)

                    is_analogy = classification_model(a, b, c, d)

                    expected = torch.ones(is_analogy.size(), device=is_analogy.device)
                    #compare the results with what we wanted
                    loss += criterion(is_analogy, expected)

                    loss.backward()
                    optimizer.step()

                    losses.append(loss.cpu().item())

                    continue

                data = [(a, b, c, d)]

                for a, b, c, d in enrich([(a, b, c, d)]):
                    # positive example, target is 1
                    is_analogy = classification_model(a, b, c, d)

                    expected = torch.ones(is_analogy.size(), device=is_analogy.device)

                    loss += criterion(is_analogy, expected)

                    if original_balance:
                        for a, b, c, d in generate_negative([(a, b, c, d)]):

                            # negative examples, target is 0
                            is_analogy = classification_model(a, b, c, d)

                            expected = torch.zeros(is_analogy.size(), device=is_analogy.device)

                            loss += criterion(is_analogy, expected)

                if not original_balance:
                    for a, b, c, d in generate_negative([(a, b, c, d)]):

                        # negative examples, target is 0
                        is_analogy = classification_model(a, b, c, d)

                        expected = torch.zeros(is_analogy.size(), device=is_analogy.device)

                        loss += criterion(is_analogy, expected)

                # once we have all the losses for one set of embeddings, we can backpropagate
                loss.backward()
                optimizer.step()

                losses.append(loss.cpu().item())

        dev_losses = []
        dev_acc = []
        with elapsed_timer() as dev_elapsed:
            with torch.no_grad():
                for a, b, c, d in dev_dataloader:
                    # compute the embeddings
                    a = embedding_model(a.to(device))
                    b = embedding_model(b.to(device))
                    c = embedding_model(c.to(device))
                    d = embedding_model(d.to(device))

                    # positive example, target is 1
                    a = torch.unsqueeze(a, 1)
                    b = torch.unsqueeze(b, 1)
                    c = torch.unsqueeze(c, 1)
                    d = torch.unsqueeze(d, 1)

                    # to be able to add other losses, which are tensors, we initialize the loss as a 0 tensor
                    loss = torch.tensor(0).to(device).float()
                    acc = 0
                    
                    if (len(a) == len(b) and torch.all(a == b)) or (len(c) == len(d) and torch.all(c == d)):

                        a = torch.unsqueeze(a, 0)
                        b = torch.unsqueeze(b, 0)
                        c = torch.unsqueeze(c, 0)
                        d = torch.unsqueeze(d, 0)

                        is_analogy = classification_model(a, b, c, d)

                        expected = torch.ones(is_analogy.size(), device=is_analogy.device)
                        #compare the results with what we wanted
                        loss += criterion(is_analogy, expected)
                        
                        acc += (is_analogy >= 0.5).sum().item()


                        dev_losses.append(loss.cpu().item())
                        dev_acc.append(acc)
                        continue

                    for a, b, c, d in enrich([(a, b, c, d)]):

                        # positive example, target is 1

                        is_analogy = classification_model(a, b, c, d)

                        expected = torch.ones(is_analogy.size(), device=is_analogy.device)

                        loss += criterion(is_analogy, expected)
                        acc += (is_analogy >= 0.5).sum().item()
                        

                        for a, b, c, d in generate_negative([(a, b, c, d)]):

                            is_analogy = classification_model(a, b, c, d)

                            expected = torch.zeros(is_analogy.size(), device=is_analogy.device)

                            loss += criterion(is_analogy, expected)
                            acc += (is_analogy < 0.5).sum().item()
                    dev_losses.append(loss.cpu().item())
                    dev_acc.append(acc/(32*a.size(0)))

        losses_list.append(mean(losses))
        dev_losses_list.append(mean(dev_losses))
        dev_acc_list.append(mean(dev_acc))
        times_list.append(elapsed())
        print(f"Epoch: {epoch}, Run time: {times_list[-1]:4.5}s, Loss: {losses_list[-1]:>2.8f}, Dev run time: {dev_elapsed():4.5}s, Dev loss: {dev_losses_list[-1]:>2.8f}, Dev accuracy: {dev_acc_list[-1]:>3.4%}")
    
    mode = "omni" + ("_nojap" if exclude_jap else "") + ("_augmented" if original_balance else "")
    if not os.path.exists('models'):
        os.makedirs('models')
    if not os.path.exists('models/omni_classification_cnn'):
        os.makedirs('models/omni_classification_cnn')
    torch.save({
        "state_dict_classification": classification_model.cpu().state_dict(),
        "losses": losses_list,
        "times": times_list,
        "state_dict_embeddings": embedding_model.cpu().state_dict(),
        "voc": word_voc,
        "voc_id": word_voc_id
        }, f"models/omni_classification_cnn/classification_CNN_{mode}_{epochs}e.pth")

if __name__ == '__main__':
    train_classifier()
