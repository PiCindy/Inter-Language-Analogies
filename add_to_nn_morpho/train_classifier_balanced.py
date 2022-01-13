import click
import torch, torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Subset
import random as rd
from functools import partial
from statistics import mean
from sklearn.model_selection import train_test_split
from copy import copy
from utils import elapsed_timer, collate
from newdata import Task0Dataset, LANGUAGE_CODES, enrich, generate_negative
from analogy_classif import Classification
from cnn_embeddings import CNNEmbedding
#from classification import Classification
#from cnnEmbedding import CNNEmbedding

#CUDA_LAUNCH_BLOCKING="1"

# to run from the terminal
@click.command()

@click.option('--language', default="eng", prompt='The language', help='The language to train the model on.', show_default=True)
@click.option('--nb_analogies', default=50000, prompt='The number of analogies',
             help='The maximum number of analogies (before augmentation) we train the model on. If the number is greater than the number of analogies in the dataset, then all the analogies will be used.', show_default=True)
@click.option('--epochs', default=20, prompt='The number of epochs',
              help='The number of epochs we train the model for.', show_default=True)
def train_classifier(language, nb_analogies, epochs):
    '''Trains a classifier and a word embedding model for a given language.

    Arguments:
    language -- The language of the data to use for the training.
    nb_analogies -- The number of analogies to use (before augmentation) for the training.
    epochs -- The number of epochs we train the model for.'''
    device = "cuda" if torch.cuda.is_available() else "cpu"

 # compares results what we got and what we should have (we don't use it in this file but in evaluation)
    def get_accuracy(y_true, y_prob):
        assert y_true.size() == y_prob.size()
        y_prob = y_prob > 0.5
        if y_prob.ndim > 1:
            return (y_true == y_prob).sum().item() / y_true.size(0)
        else:
            return (y_true == y_prob).sum().item()

    # --- Prepare data ---

    ## Train and test dataset
    train_dataset = Task0Dataset(language=language, mode="trn", word_encoding="char")

    voc = train_dataset.word_voc_id
    BOS_ID = len(voc) # (max value + 1) is used for the beginning of sequence value
    EOS_ID = len(voc) + 1 # (max value + 2) is used for the end of sequence value

    # Get subsets
    # sample of datasets to work with, if data has more than a certain no, it selects randomly
    if len(train_dataset) > nb_analogies:
        train_indices = list(range(len(train_dataset)))
        train_sub_indices = rd.sample(train_indices, nb_analogies)
        train_subset = Subset(train_dataset, train_sub_indices)
    else:
        train_subset = train_dataset

    # Load data
    #parameter?
    train_dataloader = DataLoader(train_subset, shuffle = True, collate_fn = partial(collate, bos_id = BOS_ID, eos_id = EOS_ID))

    # --- Training models ---
    emb_size = 64

    classification_model = Classification(emb_size=16*5) # 16 because 16 filters of each size, 5 because 5 sizes
    embedding_model = CNNEmbedding(emb_size=emb_size, voc_size = len(voc) + 2)

    # --- Training Loop ---
    #when working with grid or any other file, we should tell it where should it work, push to the device we want to work on
    classification_model.to(device)
    embedding_model.to(device)
    
    #give parameters to ADAM
    optimizer = torch.optim.Adam(list(classification_model.parameters()) + list(embedding_model.parameters()))

    criterion = nn.BCELoss()

    losses_list = []
    times_list = []

    print("Data loaded, start training.")

    for epoch in range(epochs):

        losses = []
        with elapsed_timer() as elapsed:
            for a, b, c, d in train_dataloader:

                
               # print("!")
                optimizer.zero_grad()

                # compute the embeddings
                a = embedding_model(a.to(device))
                b = embedding_model(b.to(device))
                c = embedding_model(c.to(device))
                d = embedding_model(d.to(device))

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
                
                data = torch.stack([a, b, c, d], dim = 1)

                #print("Start enriching")

                for a, b, c, d in enrich(data):
                    #these are the expected results in the get_accuracy function
                    # positive example, target is 1 
                    #unsqueeze --> modifies the shape of the tensors and adds the useless ones (empty dim)
                    #print(a.size(), b.size(), c.size(), d.size())
                    a = torch.unsqueeze(torch.unsqueeze(a, 0), 0)
                    b = torch.unsqueeze(torch.unsqueeze(b, 0), 0)
                    c = torch.unsqueeze(torch.unsqueeze(c, 0), 0)
                    d = torch.unsqueeze(torch.unsqueeze(d, 0), 0)

                    is_analogy = classification_model(a, b, c, d)

                    expected = torch.ones(is_analogy.size(), device=is_analogy.device)
                    #compare the results with what we wanted
                    loss += criterion(is_analogy, expected)

                #print("Start negative")
                
                #create a list
                list_of_forms=[]
                for a, b, c, d in generate_negative(data):
                    # negative examples, target is 0
                    a = torch.unsqueeze(a, 0)
                    b = torch.unsqueeze(b, 0)
                    c = torch.unsqueeze(c, 0)
                    d = torch.unsqueeze(d, 0)
                    data = torch.stack([a, b, c, d], dim = 1) #build an object with a suitable format for enrich
                    #create the second loop with enrich
                        
                    for a, b, c, d in enrich(data):
                        # negative examples, target is 0
                        a = torch.unsqueeze(torch.unsqueeze(a, 0), 0)
                        b = torch.unsqueeze(torch.unsqueeze(b, 0), 0)
                        c = torch.unsqueeze(torch.unsqueeze(c, 0), 0)
                        d = torch.unsqueeze(torch.unsqueeze(d, 0), 0)
                        
                        analogy_form=(a,b,c,d)
                        list_of_forms.append(analogy_form)
                #print(list_of_forms)                   
                #print("Done negative")
                #random sampling
                #print("List of forms len", len(list_of_forms))
                list_of_forms=rd.sample(list_of_forms,8)
                    #loop over the tuples to get them
                    #each element of the list get a,b,c,d and apply the function
                for a,b,c,d in list_of_forms:                      
                    is_analogy = classification_model(a, b, c, d)

                    expected = torch.zeros(is_analogy.size(), device=is_analogy.device)

                    loss += criterion(is_analogy, expected) # take into account all modification u should do

                    #print(is_analogy, expected, loss)
                # once we have all the losses for one set of embeddings, we can backpropagate
                # adds modification where needed
                loss.backward()
                #print("Backwards done")
                optimizer.step()
                #print("Optmizer step done")
                losses.append(loss.cpu().item())

        #print("bla", losses)
        losses_list.append(mean(losses))
        times_list.append(elapsed())
        print(f"Epoch: {epoch}, Run time: {times_list[-1]:4.5}s, Loss: {losses_list[-1]}")
    #name of the file were it will be saved :3
    torch.save({"state_dict_classification": classification_model.cpu().state_dict(), "state_dict_embeddings": embedding_model.cpu().state_dict(), "losses": losses_list, "times": times_list}, f"classification_balanced_CNN_{language}_{epochs}e.pth")

if __name__ == '__main__':
    train_classifier()




