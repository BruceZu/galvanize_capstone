import boto

# create an AWS S3 connection
conn = boto.connect_s3()
# print(conn)

conn.get_all_buckets()

# create a bucket for all of our project data
# not needed after creation
# legislation_bucket = conn.create_bucket('galvcap-legislation')

legislation_bucket.get_all_keys()

# write data to S3
roll_summary_file = legislation_bucket.new_key('roll_summaries.txt')