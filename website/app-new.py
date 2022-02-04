from flask import Flask, render_template, request
import json


app = Flask(__name__)

@app.route('/')
def index():

    return render_template('index.html', lang_1="", rules_lang_1="", lang_2="", rules_lang_2="")

    #linguistic_analysis/extracted_rules

    #English  Finnish  German  Karelian  Mezquital_otomi  Swedish

def route_print(dic):
    text = ""
    #text += '<details><summary>DEBUT</summary><details><summary>FIN</summary>BONJOUR</details><details><summary>FIN2</summary>BONJOUR</details></details>'

    #text = "<details><summary>Details</summary><details><summary>second</summary>hi</details><details><summary>second</summary>hi</details></details>"

    for key, val in dic.items():
        if type(val) == type(dict()):
            text += '<details><summary>' + key + '</summary>' + route_print(val) + '</details>'
        else:
            text += "<p>" + key + ": " + val +  "</p>"

    return text


def route_print2(language, dic, tabs=0, num=0):

    text = ""

    for key, val in dic.items():
        #text += "\t" * tabs + '<t style="color:blue;">' + key + '</t>' #background-color:yellow;
        if type(val) == type(dict()):
            text += '<details class="btn btn-link"><summary>' + key + '</summary><p>' +  + '</p></details>'
            #text += '<details class="btn btn-link"' + f"#section{num}" +\
             #("\t" * tabs) + '<t style="color:blue;">' + key + "</t>" + "</details>" #+ 'aria-expanded="true" aria-controls="'+ f"section{num}"+

            #text += "\n" + f'<div class="collapse" id="' + f"section{num}" + '">'
            num += 1
            out_text, num = route_print(language, val, tabs+1, num)
            text += "\n" + out_text
            text += "</div>"
        else:
            text += "<p>" + "\t" * tabs + '<t style="color:blue;">' + key + '</t>'
            text += ": " + val +  "</p>" + "\n"
        if tabs == 0:
            text += "\n"
    return text, num

    """
     <a data-target="#demo" data-toggle="collapse">
    CLICKABLE TEXT WOULD GO HERE INSTEAD OF BUTTON
</a>
    """


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
    bla = "\u001B[35m"
    res = "\u001B[0m"
    with open(rel_path + dic_langs[language1], 'r') as f:
        if dic_langs[language1].endswith(".json"):
            dic_1 = json.load(f)
        else:
            rules1 = f.read()
    if not rules1:
        #rules1, _ = route_print(language1, dic_1, tabs=0)
        rules1 = route_print(dic_1)
    with open(rel_path + dic_langs[language2], 'r') as f:
        if dic_langs[language2].endswith(".json"):
            dic_2 = json.load(f)
        else:
            rules2 = f.read()
    if not rules2:
        #   rules2, _ = route_print(language2, dic_2, tabs=0)
        rules2 = route_print(dic_2)
    print(rules1)


    return render_template('index.html', lang_1 = language1.capitalize(), rules_lang_1=rules1, lang_2 = language2.capitalize(), rules_lang_2=rules2)
