import torch, torch.nn as nn
import random
from pathlib import Path
import json

PATH = "task0-data/"
with open("language_codes.json", 'r') as f:
    LANGUAGE_CODES = json.load(f)
MODES = ["trn", "dev", "tst"]
CATEGORIES = ["DEVELOPMENT-LANGUAGES", "GOLD-TEST", "SURPRISE-LANGUAGES"]
MAX_ANALOGY_CLASS_LEN = 1000000

def load_data(language="deu", mode="dev", category="DEVELOPMENT-LANGUAGES"):
    '''Load the data from the sigmorphon files in the form of a list of triples (lemma, target_features, target_word).'''
    assert language in LANGUAGE_CODES, f"Language '{language}' is unkown, allowed languages are {LANGUAGE_CODES}"
    assert mode in MODES, f"Mode '{mode}' is unkown, allowed modes are {MODES}"
    assert category in CATEGORIES, f"Category '{category}' is unkown, allowed categories are {CATEGORIES}"
    family = LANGUAGE_CODES[language][0]
    filename = f"{category}/{family}/{language}.{mode}"
    with open(PATH + filename, "r", encoding="utf-8") as f:
        return [line.strip().split('\t') for line in f]


def enrich(data):
    """Apply the example generation process from 'Solving Word Analogies: a Machine Learning Perspective'."""
    for a, b, c, d in data:
        yield a, b, c, d
        yield c, d, a, b
        yield c, a, d, b
        yield d, b, c, a
        yield d, c, b, a
        yield b, a, d, c
        yield b, d, a, c
        yield a, c, b, d

def generate_negative(positive_data):
    """Apply the negative example generation process from 'Solving Word Analogies: a Machine Learning Perspective'."""
    for a, b, c, d in positive_data:
        yield b, a, c, d
        yield c, b, a, d
        yield a, a, c, d



class Task0Dataset(torch.utils.data.Dataset):

    def __init__(self, language="deu", mode="trn", word_encoding="none"):
        super(Task0Dataset).__init__()
        self.language = language
        self.mode = mode
        self.word_encoding = word_encoding
        self.raw_data = load_data(language = language, mode = mode)

        self.prepare_data()
        self.set_analogy_classes()

    def prepare_data(self):
        """Generate embeddings for the 4 elements.
        There are 2 modes to encode the words:
        - 'glove': [only for German] pre-trained GloVe embedding of the word;
        - 'char': sequence of ids of characters, wrt. a dictioanry of values;
        - 'none' or None: no encoding, particularly useful when coupled with BERT encodings.
        """
        if self.word_encoding == "char":
            # generate character vocabulary
            voc = set()
            for word_a, word_b, feature_b in self.raw_data:
                voc.update(word_a)
                voc.update(word_b)
            self.word_voc = list(voc)
            self.word_voc.sort()
            self.word_voc_id = {character: i for i, character in enumerate(self.word_voc)}


        if self.word_encoding == "none" or self.word_encoding is None:
            pass

        else:
            print(f"Unsupported word encoding: {self.word_encoding}")

    def set_analogy_classes(self):
        self.analogies = []
        self.all_words = set()
        by_feature = {}
        for i, (word_a_i, word_b_i, feature_b_i) in enumerate(self.raw_data):
            if not feature_b_i in by_feature:
                 by_feature[feature_b_i] = [] 
            by_feature[feature_b_i].append(i)
            
        for feature, similar in by_feature.items():
            print(feature, len(similar))
            max_len = MAX_ANALOGY_CLASS_LEN // len(similar)
            print(max_len)
            for i in range(len(similar)):
                for j in range(i, min(len(similar), i + max_len)):
                    self.analogies.append((similar[i], similar[j]))
                    
    def encode_word(self, word):
        if self.word_encoding == "char":
            return torch.LongTensor([self.word_voc_id[c] if c in self.word_voc_id.keys() else -1 for c in word])
            #return torch.LongTensor([self.word_voc_id[c] if c in self.word_voc_id.keys() else random.choice(list(self.word_voc_id.values())) for c in word])
        elif self.word_encoding == "none" or self.word_encoding is None:
            return word
        else:
            raise ValueError(f"Unsupported word encoding: {self.word_encoding}")
    def encode(self, a, b, c, d):
        return self.encode_word(a), self.encode_word(b), self.encode_word(c), self.encode_word(d)

    def decode_word(self, word):
        if self.word_encoding == "char":
            return "".join([self.word_voc[char.item()] for char in word])
        elif self.word_encoding == "none" or self.word_encoding is None:
            print("Word decoding not necessary when using 'none' encoding.")
            return word
        else:
            print(f"Unsupported word encoding: {self.word_encoding}")

    def __len__(self):
        return len(self.analogies)
    def __getitem__(self, index):
        ab_index, cd_index = self.analogies[index]
        a, b, feature_b = self.raw_data[ab_index]
        c, d, feature_d = self.raw_data[cd_index]
        return self.encode(a, b, c, d)

if __name__ == "__main__":
    data = Task0Dataset()
    print(len(data.analogies))
    print(data[2500])
