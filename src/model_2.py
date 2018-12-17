import numpy as np
import pandas as pd
from pymongo import MongoClient
import pprint
import string
import re
from collections import Counter

from my_tools import get_bill_data, process_corpus


from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import NMF

from sklearn.metrics.pairwise import linear_kernel
from sklearn.preprocessing import normalize
from sklearn.metrics import recall_score, precision_score, accuracy_score, confusion_matrix

from nltk.tokenize import word_tokenize, wordpunct_tokenize, RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.wordnet  import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.util import ngrams, skipgrams


from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB#, ComplementNB unreleased as of 12/14

import matplotlib.pyplot as plt
plt.style.use('ggplot')

data = get_bill_data()