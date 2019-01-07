'''
----------------------------------------------
This script loads the data and pickled models to make predictions on the bills that are still
in progress. It is currently using sklearn's TfidfVectorizer and Random Forest to vectorize
the text and make the predictions. The results are then loaded into Mongo collection predictions
for use in the Flask app.

----------------------------------------------
'''
from pymongo import MongoClient
from my_tools import get_bill_data, process_corpus
from sklearn.externals import joblib

import matplotlib.pyplot as plt

# initialize Mongo client
client = MongoClient()
db = client.bills
predictions = db.predictions

print('---------------')
print('---------------')
print('---------------')
print('Loading new data to make predictions...')
data, in_progress = get_bill_data()


# Load pickled TfidfVectorizer and Random Forest Classifier
print('---------------')
print('Loading pickled vectorizer and classifier...')
vectorizer = joblib.load('pickle_files/tfidfVectorizer.pkl')
# classifier = joblib.load('pickle_files/nlp_gradientBoost.pkl')
classifier = joblib.load('pickle_files/nlp_randomForest.pkl')
print('Pickled models loaded.')


# Put bill text from bills still in progress through the nlp pipeline
print('---------------')
print('Preprocessing bill text...')
corpus = process_corpus(in_progress, 'bill_text')


# Vectorize the text for modeling
print('')
print('---------------')
print('Vectorizing bill text...')
corpus_vec = vectorizer.transform(corpus)



print('---------------')
print('Calculating predicted probabilities...')
y_pred = classifier.predict(corpus_vec)
y_pred_proba = classifier.predict_proba(corpus_vec)



# add probabilities to dataframe and load dataframe to Mongo collection predictions
in_progress['probability'] = y_pred_proba[:, 1]

# drop id_, new collection will add a new id_
in_progress.drop('_id', axis = 1, inplace = True)

# reset collection and insert new data
db.predictions.drop()
predictions.insert_many(in_progress.to_dict('records'))