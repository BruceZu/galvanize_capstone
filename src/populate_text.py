from pymongo import MongoClient
import bson.json_util
from bs4 import BeautifulSoup
from bson.objectid import ObjectId
import pprint
import os
import json
import codecs



def read_jsonl_file(path):
    '''turn a jsonl file into an array of objects'''
    arr = []
    f = codecs.open(path, 'r', 'utf-8')
    for line in f:
        record = json.loads(line.rstrip('\n|\r'))
        arr.append(record)
    return arr



def update_bill_text(row, collection_name):
    bill_issue = row['issue']
    cong_id = row['congress_id'][:5]
    bill_text = row['bill_text']
    
    collection_name.update({'leg_id': bill_issue, 'congress_id': cong_id}, {'$set': {'body': bill_text}})

    
    
if __name__ == '__main__':
    client = MongoClient() # defaults to localhost
    db = client.bills

    bill_details = db.bill_details

    for filename in os.listdir('../data'):
        if filename.startswith('bill_text'):
            print(filename)
            rows = read_jsonl_file('../data/{}'.format(filename))
            for row in rows:
                update_bill_text(row, bill_details)
        