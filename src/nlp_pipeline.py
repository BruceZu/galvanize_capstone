'''
This script pull the bill data from Mongo and processes the text through the nlp pipeline. 
It then writes out the corpus and labels to ../data/nlp/corpus_with_labels.jsonl
'''

from my_tools import get_bill_data, process_corpus, write_json_file
import os

print('----------------')
print('----------------')
print('Running script nlp_pipeline.py...')

print('----------------')
print('Retrieving bill data from Mongo...')
data, _ = get_bill_data()
y = data['labels']

print('----------------')
print('Processing bill text through nlp pipeline... ')
X = process_corpus(data, 'bill_text')

# output corpus to eliminate multiple preprocessing events.
outfile_path = '/home/ubuntu/galvanize_capstone/data/nlp/corpus_with_labels.jsonl'

#reset file if it exists
if os.path.exists(outfile_path):
    os.remove(outfile_path)

for i in range(len(X)):
    output = {'document': X[i], 'label': str(y[i])}
    write_json_file(output, outfile_path)