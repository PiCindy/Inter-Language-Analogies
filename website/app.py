from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    
    return render_template('index.html', rules_lang_1="abbsj", rules_lang_2="lang 2 rules")
    
    #linguistic_analysis/extracted_rules
    
    #English  Finnish  German  Karelian  Mezquital_otomi  Swedish

@app.route('/publish_rules',  methods=['POST'])
def publish_rules():
    language1 = request.form.get('language1')
    language2 = request.form.get('language2')
    
    dic_langs = {'english': 'English',
                 'german': 'German',
                 'swedish': 'Swedish',
                 'finnish': 'Finnish',
                 'karelian': 'Karelian',
                 'otomi': 'Mezquital_otomi'}
    rel_path = "../linguistic_analysis/extracted_rules/"
    rules1 = ""
    rules2 = ""
    with open(rel_path + dic_langs[language1], 'r') as f:
        rules1 = f.read()
        
    with open(rel_path + dic_langs[language2], 'r') as f:
        rules2 = f.read()
    
    return render_template('index.html', rules_lang_1=rules1, rules_lang_2=rules2)
    
