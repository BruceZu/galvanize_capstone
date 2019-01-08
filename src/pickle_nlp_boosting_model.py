from pymongo import MongoClient
import numpy as np
import pandas as pd
from my_tools import get_bill_data, read_jsonl_file
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier

from sklearn.metrics import recall_score, precision_score, accuracy_score, f1_score, confusion_matrix

from sklearn.externals import joblib


print('-------------------')
print('Loading original and preprocessed data for vectorizing and modeling...')
data, in_progress = get_bill_data()

# drop bill text column from data and retrieve preprocessed text from corpus_with_labels.jsonl
data.drop('body', axis = 1, inplace = True)

corpus_with_labels = read_jsonl_file('/home/ubuntu/galvanize_capstone/data/nlp/corpus_with_labels.jsonl')
corpus_df = pd.DataFrame(list(corpus_with_labels))

X = corpus_df['document']
y = corpus_df['label'].astype(int)


# create stratified train-test split
print('-------------------')
print('Performing train-test split...')
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify = y)#, random_state = 123)

# vectorizing 6M of ~30M dimensions with n-grams, l1 norm (simple avg) or l2 norm (avg**2)
# use_idf=True gives more weight to words, n_grams that appear less frequently in the corpus
# sublinear_tf=True reduces the bias of length
print('-------------------')
print('Vectorizing...')
tfvect = TfidfVectorizer(ngram_range=(1, 4), 
                         max_features = 15000000,
                         norm = 'l2',              #default value
                         use_idf = True,           #default value
                         sublinear_tf = True)

X_train_vec = tfvect.fit_transform(X_train)
X_test_vec = tfvect.transform(X_test)

print('-------------------')
print('Getting Features...')
features = tfvect.get_feature_names()



# dump the TfidfVectorizer
print('-------------------')
print('Pickling the TfidfVectorizer...')
pickle_path = 'pickle_files/tfidfVectorizer.pkl'
if os.path.exists(pickle_path):
    os.remove(pickle_path)
joblib.dump(tfvect, pickle_path)
print('Pickling complete.')


# # load the TfidfVectorizer if memory fails
# print('-------------------')
# print('Loading the pickled TfidfVectorizer...')
# pickle_path = 'pickle_files/tfidfVectorizer.pkl'
# tfvect = joblib.load(pickle_path)
# print('Pickled vectorizer loaded.')



print('-------------------')
print('Training Gradient Boosting Classifier with vectorized results...')
gb = GradientBoostingClassifier(loss= 'deviance', 
#                                 max_features = 6000000, 
                                learning_rate = .1, 
                                n_estimators = 100, 
                                criterion = 'friedman_mse', 
                                min_samples_split = 2, 
                                min_samples_leaf = 15, 
                                max_depth = 3, 
                                max_leaf_nodes = None)

gb.fit(X_train_vec, y_train)

print('-------------------')
print('Getting predictions...')
gb_y_pred = gb.predict(X_test_vec)
gb_y_pred_proba = gb.predict_proba(X_test_vec)[:,1]

print('-------------------')
print('F1 Score:\t\t{:.4f}'.format(f1_score(y_test, gb_y_pred)))
print('Recall Score:\t\t{:.4f}'.format(recall_score(y_test, gb_y_pred)))
print('Precision Score:\t{:.4f}'.format(precision_score(y_test, gb_y_pred)))
print('Accuracy Score:\t\t{:.4f}'.format(accuracy_score(y_test, gb_y_pred)))
print(confusion_matrix(y_test, gb_y_pred))



# dump the Gradient Boosting Model
print('-------------------')
print('Pickling the Gradient Boosting Model...')
pickle_path = 'pickle_files/nlp_gradientBoost.pkl'
if os.path.exists(pickle_path):
    os.remove(pickle_path)
joblib.dump(gb, pickle_path)
print('All Pickling Complete.  DATA SCIENCE!!!')