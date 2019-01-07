import json
import codecs
import copy
import numpy as np

import pandas as pd
from pymongo import MongoClient
import datetime

import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
from nltk.tokenize import word_tokenize, wordpunct_tokenize, RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet  import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.util import ngrams, skipgrams
import string
import re

import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from scipy import interp
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler




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
    
    
def collection_to_df(collection):
    '''
    --------------------
    Returns a dataframe from a mongo collection.
    --------------------
    '''
    data = pd.DataFrame
    for i in range(collection.count()):
        data = data.append(pd.DataFrame.from_dict(collection[i], orient='index').T, ignore_index=True)
    return data


def get_bill_data():
    '''
    --------------------
    Query data from mongo db bills.bill_details and return a pandas dataframe.
    
    The data relevant to this project is currently set up to be limited to the 
    110th Congress forward.
    --------------------
    Parameters: None.
    --------------------    
    Returns:    Dataframe with relevant data and corresponding labels, 0 or 1.
                Dataframe with records labeled 'in progress'
    --------------------
    '''
    current_congress = '116'
    
    # connect to mongodb
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_info = db.bill_info
    
    # get mongoo data and convert mongo query resuls to dataframe
    # need to execute query (.find) everytime i refer to it?
    records_with_text = bill_info.find({'bill_text': {'$regex': '(.+)'}})
    data = pd.DataFrame(list(records_with_text))
#     documents = bill_info.find()
#     data = pd.DataFrame(list(documents))
    
    
    
    # DATA CLEANUP
#     # filter out simple resolutions, concurrent resolutions, and amendments (for prelim model)
#     data = data[(data['leg_type'] != 'RESOLUTION') & (data['leg_type'] != 'CONCURRENT RESOLUTION') & (data['leg_type'] != 'AMENDMENT')].copy()
    
    # create column for character counts of the bill text
    bill_lengths = list(map(lambda x: len(x), data['bill_text']))
    data['bill_char_counts'] = bill_lengths
    
    # convert date column to type datetime
    data['intro_date'] = data['intro_date'].apply(lambda x: datetime.datetime.strptime(x[:10], '%m/%d/%Y'))

    # strip out month from intro date
    data['intro_month'] = data['intro_date'].apply(lambda x: x.month)
    
    # strip out month from intro date
    data['intro_year'] = data['intro_date'].apply(lambda x: x.year)

    # get session from year (odd years are Session 1, even years are Session 2)
    data['session'] = data['intro_year'].apply(lambda x: 2 if int(x)%2 == 0 else 1)
    
    # filter out non-numeric num_of_cosponsors: S. Rept. 110-184, TXT, All Actions
    data = data[(data['num_of_cosponsors'] != 'S. Rept. 110-184') &
               (data['num_of_cosponsors'] != 'TXT') &
               (data['num_of_cosponsors'] != 'All Actions')].copy()
    
    # convert num_of_cosponsors and num_of_amendments to numeric
    data['num_of_cosponsors'] = data['num_of_cosponsors'].apply(pd.to_numeric)
    data['num_of_amendments'] = data['num_of_amendments'].apply(pd.to_numeric)
    
#     # correction for mislabeled sponsor_state and sponsor_party
#     state = copy.copy(data['sponsor_state'])
#     party = copy.copy(data['sponsor_party'])
#     data['sponsor_state'] = party
#     data['sponsor_party'] = state
    
    # create column for getting char_counts into buckets
    data['char_count_bucket'] = None

    d_0 = data[data['bill_char_counts'] <= 1000].copy()
    d_1000 = data[(data['bill_char_counts'] > 1000) & (data['bill_char_counts'] <= 2000)].copy()
    d_2000 = data[(data['bill_char_counts'] > 2000) & (data['bill_char_counts'] <= 3000)].copy()
    d_3000 = data[(data['bill_char_counts'] > 3000) & (data['bill_char_counts'] <= 4000)].copy()
    d_4000 = data[(data['bill_char_counts'] > 4000) & (data['bill_char_counts'] <= 5000)].copy()
    d_5000 = data[(data['bill_char_counts'] > 5000) & (data['bill_char_counts'] <= 6000)].copy()
    d_6000 = data[(data['bill_char_counts'] > 6000) & (data['bill_char_counts'] <= 7000)].copy()
    d_7000 = data[(data['bill_char_counts'] > 7000) & (data['bill_char_counts'] <= 8000)].copy()
    d_8000 = data[(data['bill_char_counts'] > 8000) & (data['bill_char_counts'] <= 9000)].copy()
    d_9000 = data[(data['bill_char_counts'] > 9000) & (data['bill_char_counts'] <= 10000)].copy()
    d_10000 = data[data['bill_char_counts'] > 10000].copy()


    d_0['char_count_bucket'] = 'less than 1000'
    d_1000['char_count_bucket'] = '1001 - 2000'
    d_2000['char_count_bucket'] = '2001 - 3000'
    d_3000['char_count_bucket'] = '3001 - 4000'
    d_4000['char_count_bucket'] = '4001 - 5000'
    d_5000['char_count_bucket'] = '5001 - 6000'
    d_6000['char_count_bucket'] = '6001 - 7000'
    d_7000['char_count_bucket'] = '7001 - 8000'
    d_8000['char_count_bucket'] = '8001 - 9000'
    d_9000['char_count_bucket'] = '9001 - 10000'
    d_10000['char_count_bucket'] = 'greater than 10000'

    data = pd.concat([d_0, d_1000, d_2000, d_3000, d_4000, d_5000, 
                      d_6000, d_7000, d_8000, d_9000, d_10000])


    
    
    
    # LABELING
    # break up dataframe into those that became law and others (did not or still pending)
    became_law = data[(data['bill_status'] == 'Became Law') | (data['bill_status'] == 'Became Private Law')].copy()
    others = data[(data['bill_status'] != 'Became Law') & (data['bill_status'] != 'Became Private Law')].copy()

    became_law.loc[:, 'labels'] = 1



    # break up others into current congress and previous ones. Anything that hasn't been signed into law
    # before current session is dead. Currently, all bills vetoed by the president come from previous congresses
    current_cong = others[others['congress_id'] == current_congress].copy()
    prev_cong = others[others['congress_id'] != current_congress].copy()

    prev_cong.loc[:, 'labels'] = 0



    # let's label To President and Resolving Differences with 1. Everything else is on the floor
    to_pres = current_cong[(current_cong['bill_status'] == 'To President') | (current_cong['bill_status'] == 'Resolving Differences')].copy()
    on_floor = current_cong[(current_cong['bill_status'] != 'To President') & (current_cong['bill_status'] != 'Resolving Differences')].copy()

    if len(to_pres) > 0:
        to_pres.loc[:, 'labels'] = 1


    # break up bills on the floor to failed (0) and not failed
    failed = on_floor[on_floor['bill_status'].str.startswith('Failed')].copy()
    not_failed = on_floor[~on_floor['bill_status'].str.startswith('Failed')].copy()

    if len(failed) > 0:
        failed.loc[:, 'labels'] = 0



    # bills that haven't failed yet have either been just introduced or on their way
    # label introduced with 'in_progress'. These will not be a part of our model.
    introduced = not_failed[not_failed['bill_status'] == 'Introduced'].copy()
    beyond_intro = not_failed[not_failed['bill_status'] != 'Introduced'].copy()

    if len(introduced) > 0:
        introduced.loc[:, 'labels'] = 'in_progress'



    # there are bills that started in one chamber and have already passed the other. We'll label
    # these with a 1
    passed_opp_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('S')) | 
                              (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('H'))].copy()

    if len(passed_opp_chamber) > 0:
        passed_opp_chamber.loc[:, 'labels'] = 1



    # bills that are still in the chamber they were introduced in are 'in_progress'
    in_orig_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('H')) | 
                              (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('S'))].copy()

    if len(in_orig_chamber) > 0:
        in_orig_chamber.loc[:, 'labels'] = 'in_progress'



    # bring all the information back together
    df_list = [became_law, prev_cong, to_pres, failed, introduced, passed_opp_chamber, in_orig_chamber]

    dfs_to_concat = []
    for df in df_list:
        if df.shape[0] > 0:
            dfs_to_concat.append(df)

    data_l = pd.concat(dfs_to_concat)

    
    # filter out those that are still in progress
    df_in_progress = data_l[data_l['labels'] == 'in_progress'].copy()
    df = data_l[data_l['labels'] != 'in_progress'].copy()


    # filter for most recent congress_ids
    small_df = df[(df['congress_id'] == '115') | 
                  (df['congress_id'] == '114') | 
                  (df['congress_id'] == '113') | 
                  (df['congress_id'] == '112') | 
                  (df['congress_id'] == '111') | 
                  (df['congress_id'] == '110')].copy()
    
    # sort by date
    small_df.sort_values('intro_date', ascending = False, inplace=True)
    df_in_progress.sort_values('intro_date', ascending = False, inplace=True)

    
    print('------------------')
    print('------------------')
    print('Data includes bills, joints resolutions, and laws with text from the 110th Congress (2007) to present')
    print('Make changes in my_tools.get_bill_data to modify the data set.')
    print('------------------')

    
    return small_df.reset_index(drop = True), df_in_progress.reset_index(drop=True)



def process_corpus(df, corpus_col_name):
    '''
    --------------------
    Processes the text in df[corpus_col_name] to return a corpus (list) and the series of 
    corresponding labels.
    
    The intent of this function is to feed the output into a stratified train-test split.
    
    -------------------
    Parameters: df - pandas dataframe
                corpus_col_name - name of column in df that contains the text to be processed.
    -------------------
    Returns:    corpus - a list of documents
    
    --------------------
    '''
    # create a corpus
    print('------------------')
    print('Step 1 of 4: Creating corpus...')
    documents = list(df[corpus_col_name])

    # remove numbers
    # consider removing only single digit numbers in stop_words
    documents = list(map(lambda x: ' '.join(re.split('[,_\d]+', x)), documents))
    
#     # clip the intro of each bill
#     documents = list(map(lambda x: x[(x.index('Office]') + 8):], documents))

    # tokenize the corpus
    print('------------------')
    print('Step 2 of 4: Tokenizing...')
    corpus = [word_tokenize(content.lower()) for content in documents]

    # strip out the stop words from each 
    print('------------------')
    print('Step 3 of 4: Stripping out stop words, punctuation, and numbers...')
    stop_words = stopwords.words('english')
    stop_words.extend(['considered', 'passed', 'passage', 'house', 'senate', 'session', 'proposing'])
    stop_words.extend(['speaker', 'representatives', 'vice', 'president'])
    stop_words.extend(['mr', 'mr.', 'ms', 'ms.', 'mrs', 'mrs.', 'said', 'year', 'would', 'could', 'also', 'shall', '``', '_______________________________________________________________________'])
    stop_words.extend(['th', 'st', 'nd', 'h.r', 'h.', 'r.', 'h.j', 'j.', 'ih', 'eh', 's.', 's.j', 'introduced', 'engrossed', 'page', 'stat', '--'])
    stop_words.extend(['one', 'hundred', 'sixteenth', 'fifteenth', 'fourteenth', 'thirteenth', 'twelfth', 'eleventh', 'tenth'])
    stop_words.extend(['two', 'thousand', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'])
#     consider only removing single-digit numbers
#     stop_words.extend([])
    # print(stop_words)
    corpus = [[token for token in doc if token not in stop_words] for doc in corpus]
    # corpus[0]

    # strip out the punctuation
    punc = set(string.punctuation)
    # print(punc)
    corpus = [[token for token in doc if token not in punc] for doc in corpus]
    # corpus[0]

    # lemmatize (and maybe stem?)
    print('------------------')
    print('Step 4 of 4: Lemmatizing...')
    lemmer = WordNetLemmatizer()
    corpus = [[lemmer.lemmatize(word) for word in doc] for doc in corpus]
    # corpus[0]

#     # build a vocabulary
#     print('------------------')
#     print('Creating a vocabulary...')
#     vocab_set = set()
#     [[vocab_set.add(token) for token in tokens] for tokens in corpus]
#     vocab = list(vocab_set)
#     # vocab[100000:100020]

    # # for later model...
    # # n-grams fitted in TfidfVectorizer
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
    
    return corpus



def plot_roc(X, y, clf_class, plot_name, **kwargs):
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    n_splits=5
    kf = KFold(n_splits=n_splits, shuffle=True)
    y_prob = np.zeros((len(y),2))
    mean_tpr = 0.0
    mean_fpr = np.linspace(0, 1, 100)
    all_tpr = []
    for i, (train_index, test_index) in enumerate(kf.split(X)):
        X_train, X_test = X[train_index], X[test_index]
        y_train = y[train_index]
        clf = clf_class(**kwargs)
        clf.fit(X_train,y_train)
        # Predict probabilities, not classes
        y_prob[test_index] = clf.predict_proba(X_test)
        fpr, tpr, thresholds = roc_curve(y[test_index], y_prob[test_index, 1])
        mean_tpr += interp(mean_fpr, fpr, tpr)
        mean_tpr[0] = 0.0
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, lw=1, label='ROC fold %d (area = %0.2f)' % (i, roc_auc))
    mean_tpr /= n_splits
    mean_tpr[-1] = 1.0
    mean_auc = auc(mean_fpr, mean_tpr)
    plt.plot(mean_fpr, mean_tpr, 'k--',label='Mean ROC (area = %0.2f)' % mean_auc, lw=2)
    
    plt.plot([0, 1], [0, 1], '--', color=(0.6, 0.6, 0.6), label='Random')
    plt.xlim([-0.05, 1.05])
    plt.ylim([-0.05, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver operating characteristic')
    plt.legend(loc="lower right")
    plt.savefig('17_' + plot_name + '.png')
    plt.close()