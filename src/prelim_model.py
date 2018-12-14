import numpy as np
import pandas as pd
from pymongo import MongoClient
import pprint

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from nltk.tokenize import word_tokenize, wordpunct_tokenize, RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords

from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

# connect to mongodb
client = MongoClient() # defaults to localhost
db = client.bills
bill_details = db.bill_details


# print out record counts with text
print('--> Number of records in database: {}'.format(bill_details.find().count()))

records_with_text = bill_details.find({'body': {'$regex': 'e'}})
record_count = records_with_text.count()

print('--> Current number of records with text: {}'.format(record_count))


# convert mongo query resuls to dataframe
# need to execute query (.find) everytime i refer to it?
records_with_text = bill_details.find({'body': {'$regex': 'e'}})
data = pd.DataFrame(list(records_with_text))

# filter out simple resolutions, concurrent resolutions, and amendments (for prelim model)
data = data[(data['leg_type'] != 'RESOLUTION') & (data['leg_type'] != 'CONCURRENT RESOLUTION') & (data['leg_type'] != 'AMENDMENT')]


# LABELS

# Every record that doesn't have status Became Law will have label 0 if before current (115th) congress.
# plan is to use one label ('passed') initially.
# Try this out with 3 labels.

#  

#                             Whole     House     Senate
# Introduced:                 None      None      None
# Became Law:                 1         1         1
# Passed House:               None      1         None
# To President:               1         1         1
# Resolving Differences:      1         1         1
# Failed House:               0         0         1 if S
# Became Private Law:         1         1         1
# Passed Senate:              None      None      1
# Failed to pass over veto:   1         1         1
# Vetoed by President:        1         1         1
# Passed over veto:           1         1         1     #stronger support for this one???
# Pocket vetoed by President: 1         1         1
# Failed Senate:              0         1 if H    0


# check numbers for each status
print('\tCount for each bill_status: ')
for i in data.bill_status.unique():
    num = len(data[data['bill_status'] == i])
    print('{}: \t\t{}'.format(i, num))

# create columns for labels
# data['house_label'] = None
# data['senate_label'] = None
# data['president_label'] = None
data['passed'] = None

orig_shape = data.shape
print('Shape of entire data before labeling: {}'.format(orig_shape))


# break up dataframe into those that became law and others (did not or still pending)
became_law = data[(data['bill_status'] == 'Became Law') | (data['bill_status'] == 'Became Private Law')]
others = data[(data['bill_status'] != 'Became Law') & (data['bill_status'] != 'Became Private Law')]

became_law.loc[:, 'passed'] = 1



# break up others into current congress and previous ones. Anything that hasn't been signed into law
# before current session is dead. Currently, all bills vetoed by the president come from previous congresses
current_cong = others[others['congress_id'] == '115th']
prev_cong = others[others['congress_id'] != '115th']

prev_cong.loc[:, 'passed'] = 0



# let's label To President and Resolving Differences with 1. Everything else is on the floor
to_pres = current_cong[(current_cong['bill_status'] == 'To President') | (current_cong['bill_status'] == 'Resolving Differences')]
on_floor = current_cong[(current_cong['bill_status'] != 'To President') & (current_cong['bill_status'] != 'Resolving Differences')]

to_pres.loc[:, 'passed'] = 1



# break up bills on the floor to failed (0) and not failed
failed = on_floor[on_floor['bill_status'].str.startswith('Failed')]
not_failed = on_floor[~on_floor['bill_status'].str.startswith('Failed')]

failed.loc[:, 'passed'] = 0



# bills that haven't failed yet have either been just introduced or on their way
# label introduced with 'in_progress'. These will not be a part of our model.
introduced = not_failed[not_failed['bill_status'] == 'Introduced']
beyond_intro = not_failed[not_failed['bill_status'] != 'Introduced']

introduced.loc[:, 'passed'] = 'in_progress'



# there are bills that started in one chamber and have already passed the other. We'll label
# these with a 1
passed_opp_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('S')) | 
                          (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('H'))]

passed_opp_chamber.loc[:, 'passed'] = 1



# bills that are still in the chamber they were introduced in are 'in_progress'
in_orig_chamber = beyond_intro[(beyond_intro['bill_status'] == 'Passed House') & (beyond_intro['leg_id'].str.startswith('H')) | 
                          (beyond_intro['bill_status'] == 'Passed Senate') & (beyond_intro['leg_id'].str.startswith('S'))]    

in_orig_chamber.loc[:, 'passed'] = 'in_progress'



# bring all the information back together
data_l = pd.concat([became_law, prev_cong, to_pres, failed, introduced, in_opp_chamber, in_orig_chamber])

labeled_shape = data_l.shape
print('Shape of entire data after labeling: {}'.format(labeled_shape))
print('----------------')

if orig_shape == labeled_shape:
    print('\tNo data loss upon labeling. Continue on your path, Barsen\'thor.')
else:
    print('\tData loss occurred during labeling. You may want to examine your code')    


print(data_l.passed.value_counts())