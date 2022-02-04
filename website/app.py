from flask import Flask, render_template, request
import json
import pandas as pd
import random


app = Flask(__name__)

SHORT_NAME = {'english':'eng',
              'german': 'deu',
              'swedish': 'swe',
              'finnish': 'fin',
              'karelian': 'krl',
              'otomi': 'ote'}
              
LONG_NAME = {v:k for k, v in SHORT_NAME.items()}

@app.route('/')
def index():

    return render_template('index.html', lang_1="", rules_lang_1="", lang_2="", rules_lang_2="", rules_percent="", analogies_examples=[])


def route_print(dic):
    text = ""
    if type(dic) == type(dict()):
        for key, val in dic.items():
            if key.capitalize() != key and type(val) == type(dict()):
                text += '<details><summary>' + key + '</summary>' + route_print(val) + '</details>'
            elif type(val) == type(dict()):
                text += "<p style='font-weight: bold;'>" + key + "</p>" + route_print(val)
            else:
                text += "<p>" + "\t" + key + ": " + val +  "</p>"
    return text


def iterate_through_rules(el, keys):
    if type(el) != type(dict()):
        yield keys, el
        return
    for key, val in el.items():
        yield from iterate_through_rules(val, keys + [key])


def change_values(lang1, keys, rules):
    for k in keys:
        if not (k in lang1):
            print("ERRROROROORORORO")
        elif type(lang1[k]) != type(dict()):
            lang1[k] = rules
        else:
            lang1 = lang1[k]

def process_similarities(lang1, lang2):
    for keys1, rules1 in iterate_through_rules(lang1, []):
        for keys2, rules2 in iterate_through_rules(lang2, []):
            if set(keys1) <= set(keys2) or set(keys2) <= set(keys1):
                rules1 = rules1.split("|")
                rules2 = rules2.split("|")
                new_rules1 = []
                new_rules2 = []
                for r1 in rules1:
                    if r1 in rules2:
                        new_rules1.append('<t style="color:blue">' + r1 + '</t>')
                    else:
                        new_rules1.append(r1)
                for r2 in rules2:
                    if r2 in rules1:
                        new_rules2.append('<t style="color:blue">' + r2 + '</t>')
                    else:
                        new_rules2.append(r2)
                rules1 = "|".join(new_rules1)
                rules2 = "|".join(new_rules2)
                change_values(lang1, keys1, rules1)
                change_values(lang2, keys2, rules2)
                

def count_similarity_percent(lang):
    if type(lang) != type(dict()):
        return (1 if "<t" in lang else 0, 1)
    num_changed = 0
    num_total = 0
    for key in lang:
        changed, total = count_similarity_percent(lang[key])
        num_changed += changed
        num_total += total
    return num_changed, num_total


@app.route('/publish_rules',  methods=['POST'])
def publish_rules():
    language1 = request.form.get('language1')
    language2 = request.form.get('language2')

    dic_langs = {'english': 'english.json',
                 'german': 'german.json',
                 'swedish': 'swedish.json',
                 'finnish': 'finnish.json',
                 'karelian': 'karelian.json',
                 'otomi': 'otomi.json'}
    rel_path = "../linguistic_analysis/extracted_rules/"
    rules1 = ""
    rules2 = ""
    
    with open(rel_path + dic_langs[language1], 'r') as f:
        dic_1 = json.load(f)
        
    with open(rel_path + dic_langs[language2], 'r') as f:
        dic_2 = json.load(f)
    process_similarities(dic_1, dic_2)
    rules1 = route_print(dic_1)
    rules2 = route_print(dic_2)

    same, total = count_similarity_percent(dic_2)
    rules_similarity = round(100 * same / total)
    
    similarity_message = f"{rules_similarity}% of rules in {language2.capitalize()} are similar to rules in {language1.capitalize()}."
    
    csv_path = "../results/6langs_fscore.csv"
    
    df = pd.read_csv(csv_path, index_col=0)
    
    transfer_result = round(1000 * df.loc[language1, language2]) / 10
    
    similarity_message += f"\nModel transfer score from {language1.capitalize()} to {language2.capitalize()} is {transfer_result}%."
    
    with open("../guessed_analogies/guessed_analogies-" + SHORT_NAME[language1] + ".json", 'r') as f:
        analogies = json.load(f)
    
    analogies_examples = random.choices(analogies[SHORT_NAME[language2]], k=10)
    return render_template('index.html', lang_1 = language1.capitalize(), rules_lang_1=rules1, lang_2 = language2.capitalize(), 
                           rules_lang_2=rules2, rules_percent=similarity_message, analogies_examples=analogies_examples)
