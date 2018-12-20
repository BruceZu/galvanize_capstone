'''
Pull S3 files into mongo database
'''

from pymongo import MongoClient
import bson.json_util
import os
import boto
from boto.s3.connection import S3Connection, Location
from boto.s3.key import Key
from my_tools import read_jsonl_file


def mongo_import(filename_start, collection_name):
    '''
    Imports files from S3 bucket gavcap-leg with filenames that start with filename_start,
    temporarily puts them in the data folder. The data is then loaded into Mongo 
    collection collection_name and the files are deleted from data folder.
    
    Parameters: filename_start - the start of the filename
                collection_name - Mongo collection in database bills
                
    Returns: None
    '''
    # create an AWS S3 connection
    conn = boto.s3.connect_to_region('us-west-2', host = 's3-us-west-2.amazonaws.com')

    legislation_bucket = conn.get_bucket('galvcap-leg')

    print('Pulling {} files from S3...'.format(filename_start))
    print('-------------------')
    for k in legislation_bucket:
        filename = k.key
        if filename.startswith(filename_start):
            k.get_contents_to_filename('../data/{}'.format(filename))
    

    for filename in os.listdir('../data'):
        if filename.startswith(filename_start):
            print('Loading {} into mongo'.format(filename))
            data = read_jsonl_file('../data/{}'.format(filename))
            for record in data:
                collection_name.insert_one(record)

            # remove file from data folder once mongo load completes
            os.remove('../data/{}'.format(filename))
    print('------------------')
    print('Mongo load and data folder cleanup complete.')
    


if __name__ == '__main__':
    # intialize mongo client
    client = MongoClient() # defaults to localhost
    db = client.bills
    
    bill_details = db.bill_details    
    mongo_import('bill_details', bill_details)

    vote_results = db.vote_results    
    mongo_import('vote_results', vote_results)


        