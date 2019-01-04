from pymongo import MongoClient
from my_tools import get_bill_data, process_corpus, write_json_file, write_jsonl_file

print('----------------')
print('Retrieving bill data from Mongo...')
data = get_bill_data()

print('----------------')
print('Processing bill text through nlp pipeline... ')
X, y = process_corpus(data, 'body')

# output corpus to eliminate multiple preprocessing events.
outfile_path = '../data/nlp/corpus_with_labels.jsonl'

#reset file
write_jsonl_file([''], outfile_path)

for i in range(len(X)):
    output = {'document': X[i], 'label': str(y[i])}
    write_json_file(output, outfile_path)