'''
----------------------------------------------
This script loads the data and pickled models to make predictions on the bills that are still
in progress. It is currently using sklearn's TfidfVectorizer and Random Forest to vectorize
the text and make the predictions. The results are then loaded into Mongo collection predictions
for use in the Flask app.

----------------------------------------------
'''
import numpy as np
import pandas as pd
from pymongo import MongoClient
from my_tools import get_bill_data, process_corpus
from sklearn.externals import joblib

from datetime import datetime, date
import matplotlib.pyplot as plt

# specify weight of nlp portion of model
nlp_weight = .5

# initialize Mongo client and collections
client = MongoClient()
db = client.bills
predictions = db.predictions
prev_predictions = db.prev_predictions

print('---------------')
print('---------------')
print('Loading new data to make predictions...')
data, in_progress = get_bill_data()


# Load pickled TfidfVectorizer and Random Forest Classifier
print('---------------')
print('Loading pickled models...')
print('---------------')
print('\t... Vectorizer for NLP...')
vectorizer = joblib.load('pickle_files/tfidfVectorizer.pkl')
print('---------------')
print('\t... Classifier for NLP...')
rf = joblib.load('pickle_files/nlp_randomForest.pkl')
print('---------------')
print('\t... Scaler for numerical model...')
sc = joblib.load('pickle_files/num_scaler.pkl')
print('---------------')
print('\t... Classifier for numerical model including Introduced bills...')
gb_intro = joblib.load('pickle_files/num_all_gradientBoost.pkl')
print('---------------')
print('\t... Classifier for numerical model for after bill passes one chamber...')
gb_passed_one = joblib.load('pickle_files/num_gradientBoost.pkl')
print('Pickled models loaded.')



# Put bill text from bills in progress through the nlp pipeline
print('---------------')
print('Preprocessing bill text...')
corpus = process_corpus(in_progress, 'bill_text')



# Vectorize the text for modeling
print('---------------')
print('Vectorizing bill text...')
corpus_vec = vectorizer.transform(corpus)

print('---------------')
print('Calculating predicted probabilities for nlp portion of model...')
nlp_pred_proba = rf.predict_proba(corpus_vec)[:, 1]

# add probabilities to dataframe 
in_progress['nlp_pred_proba'] = nlp_pred_proba


print('------------------')
print('Fitting numerical data...')
# the numerical model was trained on bills that progressed beyond the introduction stage
# break this data out of the dataframe and merge them after predictions are made
intro = in_progress[in_progress['bill_status'] == 'Introduced']
beyond_intro = in_progress[in_progress['bill_status'] != 'Introduced']

# data to fit must have the same features as the data used to train the model
model_cols = [
            'num_of_cosponsors', 
            'num_of_amendments', 
            'bill_char_counts',
            'intro_month_1', 
            'intro_month_2', 
            'intro_month_3', 
            'intro_month_4', 
            'intro_month_5', 
            'intro_month_6', 
            'intro_month_7', 
            'intro_month_8', 
            'intro_month_9', 
            'intro_month_10', 
            'intro_month_11',
            'session_1'
            ]

cols_to_use = [
#             'sponsor',
            'num_of_cosponsors', 
#             'sponsor_party', 
#             'sponsor_state', 
            'num_of_amendments',
            'bill_char_counts', 
            'intro_month', 
            'session'
            ]

dummy_columns = [
            'intro_month', 
#             'num_of_amendments', 
#             'num_of_cosponsors',
#             'sponsor',
#             'sponsor_party', 
#             'sponsor_state', 
            'session'
            ]

data_feats_intro = intro.loc[:, cols_to_use]
data_feats_passed_one = beyond_intro.loc[:, cols_to_use]

# get dummies for intro_month, sponsor_party, sponsor_state, session
data_dumm_intro = pd.get_dummies(data_feats_intro, columns = dummy_columns, drop_first=False)
data_dumm_passed_one = pd.get_dummies(data_feats_passed_one, columns = dummy_columns, drop_first=False)

# modify columns to fit model
for col in model_cols:
    if col not in data_dumm_intro.columns:
        data_dumm_intro[col] = 0
    if col not in data_dumm_passed_one.columns:
        data_dumm_passed_one[col] = 0



print('-------------------')
print('Scaling and getting predictions...')
data_dumm_intro = sc.transform(data_dumm_intro)
gb_intro_pred_proba = gb_intro.predict_proba(data_dumm_intro)[:, 1]

data_dumm_passed_one = sc.transform(data_dumm_passed_one)
gb_passed_one_pred_proba = gb_passed_one.predict_proba(data_dumm_passed_one)[:, 1]


intro['num_pred_proba'] = gb_intro_pred_proba
beyond_intro['num_pred_proba'] = gb_passed_one_pred_proba



pred_df = pd.concat([intro, beyond_intro], axis = 0)

pred_df['pred_proba'] = nlp_weight * pred_df['nlp_pred_proba'] + (1 - nlp_weight) * pred_df['num_pred_proba']

pred_df['pred_date'] = date.today().strftime('%m/%d/%Y')

print('---------------')
print('Formatting and inserting the predicted probabilities into Mongo...')
# format columns for flask app
pred_df['intro_date'] = pred_df['intro_date'].apply(lambda x: x.strftime('%m/%d/%Y'))
pred_df['nlp_pred_proba'] = pred_df['nlp_pred_proba'].round(5)
pred_df['num_pred_proba'] = pred_df['num_pred_proba'].round(5)
pred_df['pred_proba'] = pred_df['pred_proba'].round(5)

# drop id_, new collection will add a new id_
pred_df.drop('_id', axis = 1, inplace = True)

# db.prev_predictions.drop()

# move previous predictions to prev_predictions
priors = predictions.find()

# db.prev_predictions.drop()
for p in priors:
    prev_predictions.insert_one(p)

# replace old predictions with new ones for Flask app
db.predictions.drop()
predictions.insert_many(pred_df.to_dict('records'))

print('---------------')
print('Loaded {} predictions. Script complete. DATA SCIENCE!!!'.format(len(pred_df)))