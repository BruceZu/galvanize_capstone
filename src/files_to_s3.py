import boto
from boto.s3.connection import S3Connection, Location
import os
import codecs
import json

# create an AWS S3 connection
conn = boto.s3.connect_to_region('us-west-2', host = 's3-us-west-2.amazonaws.com')

print('Buckets available: {}'.format(conn.get_all_buckets()))

# create a bucket for all of our project data
# not needed after creation
# had trouble creating a bucket in USWest2 this way. Used UI to do so
# legislation_bucket = conn.create_bucket('galvcap-legislation', location = Location.USWest2)

legislation_bucket = conn.get_bucket('galvcap-leg')

print('Keys currently in bucket galvcap-leg: {}'.format(legislation_bucket.get_all_keys()))

for f in os.listdir('../data'):
    if f.startswith('vote_results'):
        print('Loading {} to s3'.format(f))
        # create new key in s3
        file_ = legislation_bucket.new_key(f)

        # copy one local file to s3
        filepath = '../data/{}'.format(f)
        file_.set_contents_from_filename(filepath)
        file_.get_contents_to_filename(f)
        
print('Upload to s3 complete!')
