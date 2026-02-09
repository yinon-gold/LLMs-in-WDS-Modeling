import os
import sys
import json
import pandas as pd
from llm_epanet.utils.utils import get_project_root

HOME_DIR = get_project_root()


def read_documentation():
    doc_path = os.path.join(HOME_DIR, 'data', 'epyt_documentation.py')
    with open(doc_path, 'r') as file:
        return file.read().split('class epanet:')[1].split('class epanetapi:')[0].split('def ')[2:]
    

def get_function_name(functext):
    return functext.split('(')[0].replace('\n', '')

def get_function_signature(functext):
    return functext.split('"""')[0].replace('\n', '')

def get_function_description(functext):
    return functext.split('"""')[1]

def get_function_code_no_signature(functext):
    x = functext.split('"""')
    return x[-1]

def get_function_code(functext):
    x = functext.split('"""')
    return x[0] + x[-1]

def get_function_args(functext):
    return functext.split('(')[1].split(')')[0]


def clean_documentation(docs):
    docs = read_documentation()

    docs = [
        (d := doc.replace('see also', 'See also')).split('See also')[0] + '"""' + d.split('"""')[2]
        if 'see also' in doc.lower()
        else doc
        for doc in docs
    ]
    return docs


def save_cleaned_docs(docs):
    df = pd.DataFrame(columns=['func_name', 'func_signature', 'func_args', 'func_description', 'func_code', 'func_code_no_signature', 'func_full_text'])
    for idx, functext in enumerate(docs):
        if len(functext.split('"""')) < 2:
            print('Function', get_function_name(functext), 'is missing description, skipping')
            continue
        if 'msx' in get_function_name(functext).lower():
            continue
        try:
            df = pd.concat([df, pd.DataFrame.from_records([{
                'func_name': get_function_name(functext),
                'func_signature': get_function_signature(functext),
                'func_args': get_function_args(functext),
                'func_description': get_function_description(functext),
                'func_code': get_function_code(functext),
                'func_code_no_signature': get_function_code_no_signature(functext),
                'func_full_text': functext
            }])])
        except:
            print(idx, functext)
            print('Error:', get_function_name(functext))



    save_path = os.path.join(HOME_DIR, 'data', 'epyt_documentation_cleaned.csv')
    df.to_csv(save_path, index=False)
    print(f'Saved {len(df)} cleaned functions')
    return df, save_path


def create_documentation_csv():
    docs = read_documentation()
    cleaned_docs = clean_documentation(docs)
    df, save_path = save_cleaned_docs(cleaned_docs)
    print(f'DataFrame saved to: {save_path}')


if __name__ == "__main__":
    create_documentation_csv()