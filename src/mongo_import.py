'''
script used to pull s3 files into mongo database
'''

from pymongo import MongoClient
import bson.json_util
import os
import boto
from boto.s3.connection import S3Connection, Location
from boto.s3.key import Key
from my_tools import read_jsonl_file

# intialize mongo client
client = MongoClient() # defaults to localhost
db = client.bills
bill_details = db.bill_details


# create an AWS S3 connection
conn = boto.s3.connect_to_region('us-west-2', host = 's3-us-west-2.amazonaws.com')

legislation_bucket = conn.get_bucket('galvcap-leg')

# print('Keys currently in bucket galvcap-leg: {}'.format(legislation_bucket.get_all_keys()))


print('Pulling bill_details files from S3...')
print('-------------------')
for k in legislation_bucket:
    filename = k.key
    if filename.startswith('bill_details'):
        k.get_contents_to_filename('../data/{}'.format(filename))

for filename in os.listdir('../data'):
    if filename.startswith('bill_details'):
        print('Loading {} into mongo'.format(filename))
        data = read_jsonl_file('../data/{}'.format(filename))
        for record in data:
            bill_details.insert_one(record)
            
        