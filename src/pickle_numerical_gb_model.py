'''
This script pickles the Gradient Boosting model trained on the categorical and 
continuous values for bills that have moved beyond bill_status Introduced. The 
predicted probabilities will be used in feature-weighted linear stacking with the
probabilities calculated in the nlp model to improve predictions on those.
'''
import pandas as pd
import numpy as np
from my_tools import get_bill_data
import os
import matplotlib.pyplot as plt
plt.style.use('ggplot')

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from sklearn.ensemble import GradientBoostingClassifier

from sklearn.metrics import recall_score, precision_score, accuracy_score, f1_score, confusion_matrix, log_loss, roc_curve, roc_auc_score

from sklearn.externals import joblib


data, in_progress = get_bill_data()

# fit to bills that have moved beyond bill_status Introduced
data = data[data['bill_status'] != 'Introduced']

# oversample the minority class to balance the classes
count_class_0, count_class_1 = data.labels.value_counts()

class_0 = data[data['labels'] == 0]
class_1 = data[data['labels'] == 1]

class_1 = class_1.sample(count_class_0, replace=True)

data = pd.concat([class_0, class_1], axis = 0, ignore_index=True)

print('------------------')
print('Limiting dataset to significant numerical and categorical features...')

cols_to_use = [
#             'sponsor',
            'num_of_cosponsors', 
#             'sponsor_party', 
#             'sponsor_state', 
            'num_of_amendments',
            'bill_char_counts', 
            'intro_month', 
            'session', 
            'labels'
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

data_features = data.loc[:, cols_to_use]

# get dummies for intro_month, sponsor_party, sponsor_state, session
data_dumm = pd.get_dummies(data_features, columns = dummy_columns, drop_first=False)


# drop last dummy column for each feature to avoid dummy trap
cols_to_drop = ['intro_month_12', 'session_2']
for col in cols_to_drop: 
    data_dumm.drop(col, axis = 1, inplace = True)

# y = data_features.pop('labels').values.astype(int)
y = data_dumm.pop('labels').values.astype(int)

print('------------------')
print('Performing train-test split...')
X_train, X_test, y_train, y_test = train_test_split(data_dumm, y, stratify = y)
# X_train, X_test, y_train, y_test = train_test_split(data_features, y, stratify = y)

print('------------------')
print('Scaling the data...')
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)



print('-------------------')
print('Training Gradient Boosting Classifier with oversampled continuous and categorical data...')
gb = GradientBoostingClassifier(loss= 'deviance',             # default value
                                max_features = None,          # default value
                                learning_rate = .05,
                                n_estimators = 200,           # default value
                                criterion = 'friedman_mse',   # default value
                                min_samples_split = 2,        # default value
                                min_samples_leaf = 1,         # default value
                                max_depth = 8,
                                max_leaf_nodes = None)        # default value

gb.fit(X_train, y_train)

print('-------------------')
print('Getting predictions...')
gb_y_pred = gb.predict(X_test)
gb_y_pred_proba = gb.predict_proba(X_test)[:, 1]

print('-------------------')
print('F1 Score:\t\t{:.4f}'.format(f1_score(y_test, gb_y_pred)))
print('Recall Score:\t\t{:.4f}'.format(recall_score(y_test, gb_y_pred)))
print('Precision Score:\t{:.4f}'.format(precision_score(y_test, gb_y_pred)))
print('Accuracy Score:\t\t{:.4f}'.format(accuracy_score(y_test, gb_y_pred)))
print(confusion_matrix(y_test, gb_y_pred))

gb_fprs, gb_tprs, gb_thresh = roc_curve(y_test, gb_y_pred_proba)


print('-------------------')
print('Pickling the scaler and GradientBoost model...')
gb_pickle_path = 'pickle_files/num_gradientBoost.pkl'
sc_pickle_path = 'pickle_files/num_scaler.pkl'

if os.path.exists(gb_pickle_path):
    os.remove(gb_pickle_path)
joblib.dump(gb, gb_pickle_path)

if os.path.exists(sc_pickle_path):
    os.remove(sc_pickle_path)
joblib.dump(sc, sc_pickle_path)

print('All Pickling comlete. DATA SCIENCE!!!')