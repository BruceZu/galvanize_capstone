import json
import codecs
import copy

import pandas as pd
from pymongo import MongoClient
import datetime

from nltk.tokenize import word_tokenize, wordpunct_tokenize, RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet  import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.util import ngrams, skipgrams
import string
import re




def read_jsonl_file(path):
    '''turn a jsonl file (carriage returns per record) into an array of objects'''
    arr = []
    f = codecs.open(path, 'r', 'utf-8')
    for line in f:
        record = json.loads(line.rstrip('\n|\r'))
        arr.append(record)
    return arr


def read_json_file(path):
    '''Turn a normal json file (no carriage returns per record) into an object'''
    text = codecs.open(path, 'r', 'utf-8').read()
    return json.loads(text)


def write_jsonl_file(list_of_objects, path):
    '''Dump a list of objects out as a jsonl file'''
    f = codecs.open(path, 'w', 'utf-8')
    for row in list_of_objects:
        json_record = json.dumps(row, ensure_ascii = False)
        f.write(json_record + '\n')
    f.close()

    
def write_json_file(obj, path):
    '''Dump an object and write it out as json to a file'''
    f = codecs.open(path, 'a', 'utf-8')
    json_record = json.dumps(obj, ensure_ascii = False)
    f.write(json_record + '\n')
    f.close
    
    
def get_bill_data():
    '''
    Query data from mongo db bills.bill_details and return a pandas dataframe.
    
    The data relevant to this project is currently set up to be limited to the 
    110th Congress forward.
    --------------------
    Parameters: None.
    --------------------    
    Returns: pandas dataframe with relevant data and corresponding labels.
                
    '''
    # connect to mongodb
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_details = db.bill_details
    
    # get mongoo data and convert mongo query resuls to dataframe
    # need to execute query (.find) everytime i refer to it?
    records_with_text = bill_details.find({'body': {'$regex': 'e'}})
    data = pd.DataFrame(list(records_with_text))

    # filter out simple resolutions, concurrent resolutions, and amendments (for prelim model)
    data = data[(data['leg_type'] != 'RESOLUTION') & (data['leg_type'] != 'CONCURRENT RESOLUTION') & (data['leg_type'] != 'AMENDMENT')]
    
    # create column for character counts of the bill text
    bill_lengths = list(map(lambda x: len(x), data['body']))
    data['bill_char_counts'] = bill_lengths
    
    # convert date column to type datetime
    data['intro_date'] = data['intro_date'].apply(lambda x: datetime.datetime.strptime(x[:10], '%m/%d/%Y'))

    # strip out month from intro date
    data['intro_month'] = data['intro_date'].apply(lambda x: x.month)
    
    # get session from year (odd years are Session 1, even years are Session 2)
    data['session'] = data['congress_id'].apply(lambda x: 2 if int(x[:3])%2 == 0 else 1)
    
    # correction for mislabeled sponsor_state and sponsor_party
    state = copy.copy(data['sponsor_state'])
    party = copy.copy(data['sponsor_party'])
    data['sponsor_state'] = party
    data['sponsor_party'] = state

    
    
    
    
    
    print('------------------')
    print('Creating column \'labels\'...')
    
    # break up dataframe into those that became law and others (did not or still pending)
    became_law = data[(data['bill_status'] == 'Became Law') | (data['bill_status'] == 'Became Private Law')]
    others = data[(data['bill_status'] != 'Became Law') & (data['bill_status'] != 'Became Private Law')]

    became_law.loc[:, 'labels'] = 1



    # break up others into current congress and previous ones. Anything that hasn't been signed into law
    # before current session is dead. Currently, all bills vetoed by the president come from previous congresses
    current_cong = others[others['congress_id'] == '115th']
    prev_cong = others[others['congress_id'] != '115th']

    prev_cong.loc[:, 'labels'] = 0



    # let's label To President and Resolving Differences with 1. Everything else is on the floor
    to_pres = current_cong[(current_cong['bill_status'] == 'To President') | (current_cong['bill_status'] == 'Resolving Differences')]
    on_floor = current_cong[(current_cong['bill_status'] != 'To President') & (current_cong['bill_status'] != 'Resolving Differences')]

    to_pres.loc[:, 'labels'] = 1



    # break up bills on the floor to failed (0) and not failed
    failed = on_floor[on_floor['bill_status'].str.startswith('Failed')]
    not_failed = on_floor[~on_floor['bill_status'].str.startswith('Failed')]

    failed.loc[:, 'labels'] = 0



    # bills that haven't failed yet have either been just introduced or on their way
    # label introduced with 'in_progress'. These will not be a part of our model.
    introduced = not_failed[not_failed['bill_status'] == 'Introduced']
    beyond_intro = not_failed[not_failed['bill_status'] != 'Introduced']

    introduced.loc[:, 'labels'] = 'in_progress'



    # there are bills that started in one chamber and have already passed the other. We'll label
    # these with a 1
    passed_opp_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('S')) | 
                              (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('H'))]

    passed_opp_chamber.loc[:, 'labels'] = 1



    # bills that are still in the chamber they were introduced in are 'in_progress'
    in_orig_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('H')) | 
                              (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('S'))]    

    in_orig_chamber.loc[:, 'labels'] = 'in_progress'



    # bring all the information back together
    data_l = pd.concat([became_law, prev_cong, to_pres, failed, introduced, passed_opp_chamber, in_orig_chamber])

    # filter out those that are still in progress
    df = data_l[data_l['labels'] != 'in_progress']

    # filter for most recent congress_ids
    small_df = df[(df['congress_id'] == '115th') | 
              (df['congress_id'] == '114th') | 
              (df['congress_id'] == '113th')| 
              (df['congress_id'] == '112th')| 
              (df['congress_id'] == '111th')| 
              (df['congress_id'] == '110th')]
    
    print('------------------')
    print('------------------')
    print('Data is from the 110th Congress (2007) to present')
    print('------------------')
    
    return small_df



def process_corpus(df, corpus_col_name, labels_col_name):
    '''
    Processes the text in df[corpus_col_name] to return a corpus (list) and the series of 
    corresponding labels in df[label_col_name].
    
    The intent of this function is to feed the output into a stratified train-test split.
    -------------------
    Parameters: df - pandas dataframe
                col_name - name of column in df that contains the text to be processed.
    -------------------
    Returns: X - a list of documents
             y - a pandas series of corresponding labels
    '''
    # create a corpus
    print('------------------')
    print('Creating corpus...')
    documents = list(df[corpus_col_name])

    # remove numbers
    documents = list(map(lambda x: ' '.join(re.split('[,_\d]+', x)), documents))
    
    # clip the intro of each bill
    documents = list(map(lambda x: x[(x.index('Office]') + 8):], documents))

    # tokenize the corpus
    print('------------------')
    print('Tokenizing...')
    corpus = [word_tokenize(content.lower()) for content in documents]

    # strip out the stop words from each 
    print('------------------')
    print('Stripping out stop words, punctuation, and numbers...')
    stop_words = stopwords.words('english')
    stop_words.extend(['mr', 'ms', 'mrs', 'said', 'year', 'would', 'could', 'also', 'shall', '_______________________________________________________________________'])
    # print(stop_words)
    corpus = [[token for token in doc if token not in stop_words] for doc in corpus]
    # corpus[0]

    # strip out the punctuation
    punc = set(string.punctuation)
    # print(punc)
    corpus = [[token for token in doc if token not in punc] for doc in corpus]
    # corpus[0]

    # strip out the punctuation
    string.digits


    # lemmatize (and maybe stem?)
    print('------------------')
    print('Lemmatizing...')
    lemmer = WordNetLemmatizer()
    corpus = [[lemmer.lemmatize(word) for word in doc] for doc in corpus]
    # corpus[0]

    # build a vocabulary
    print('------------------')
    print('Creating a vocabulary...')
    vocab_set = set()
    [[vocab_set.add(token) for token in tokens] for tokens in corpus]
    vocab = list(vocab_set)
    # vocab[100000:100020]

    # # for later model...
    # # examine n-grams...
    # # bigrams (two words side-by-side)
    # print('------------------')
    # print('Creating lists of bigrams, trigrams, skipgrams, etc...')
    # bigrams = [list(ngrams(sequence = doc, n = 2)) for doc in corpus]
    # trigrams = [list(ngrams(sequence = doc, n = 3)) for doc in corpus]
    # #... more?

    # # skipgrams (n-grams that skip k words)
    # skipgrams = [list(skipgrams(sequence = doc, n = 2, k = 1)) for doc in corpus]


    # rejoin each doc in corpus so each doc is a single string
    corpus = [' '.join(tokens) for tokens in corpus]

    print('------------------')
    print('NLP preprocessing complete ...')

    X = corpus
    y = df[labels_col_name].astype('int')
    
    return X, y