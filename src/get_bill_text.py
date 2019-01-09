'''
----------------------------------------------
Once data has been populated into Mongo database, this script will populate the bill text
in the 'body' field if text doesn't already exist. 

----------------------------------------------
'''
from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests
import threading
from random import randint
from time import sleep
from datetime import date

from my_tools import write_json_file


def url_builder(record_url):
    '''
    ----------------------------------------------
    Builds endpoint url from leg_url in mongo. Endpoint url should be the site that 
    contains the text version of the bill.
    
    ----------------------------------------------
    Parameters: a mongo record
    
    ----------------------------------------------
    Returns:    url

    ----------------------------------------------
    '''
    url_root = record_url.rsplit('?')[0]
    return '{}/text?format=txt&r=1'.format(url_root)


def get_bill_text(site_url):
    '''
    ----------------------------------------------
    Scrapes the page at url to return the text of the bill.
    
    ----------------------------------------------
    Parameters: url
    
    ----------------------------------------------
    Returns:    bill text, if it exists
    
    ----------------------------------------------
    '''
    # included sleep time to mimick human user 
    sleep_time = randint(2, 5)
    sleep(sleep_time)

    req = requests.get(site_url)
    stat_code = req.status_code
    
    log_path = '/home/ubuntu/galvanize_capstone/data/logs/bill_text_errors.jsonl'

    # if error in getting url, print and log the error
    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('')
        print('\t{}'.format(site_url))
        print('\t\tError in retrieving bill text.')
        print('\t\tRequest Status Code: {}'.format(stat_code))
        errored_line = {'url': site_url, 'error': stat_code, 'process': 'bill text'}
        write_json_file(errored_line, log_path)
        print('Error logged in {}'.format(log_path))

    if stat_code == 200:
        soup = BeautifulSoup(req.content, 'lxml')
        # print(soup.prettify())

        # if there is no text, print and log the error
        if soup.find('pre') is None:
            print('_______________')
            print('_______________')
            print('\t{}'.format(site_url))
            print('\t\tNo text available for scraping. Logging...')
            errored_line = {'url': site_url, 'error': 'no text available', 'process': 'bill text'}
            write_json_file(errored_line, log_path)
            
            return None


        # else scrape the text
        else:
            bill_txt = soup.find('pre').text
            bill_txt = ' '.join(bill_txt.split())

            return bill_txt


def update_mongo_body(txt, bill_issue, cong_id, collection):  
    '''
    ----------------------------------------------
    Updates the body field in the mongo record specified by bill_issue (leg_id) and
    cong_id (congress_id) from db.collection with txt.
    
    ----------------------------------------------
    Parameters: txt - the text of the bill
                bill_issue - value to filter on for key leg_id
                cong_id - value to filter on for key congress_id
                collection - the name of the mongo collection
                
    ----------------------------------------------
    Returns:    None
    
    ----------------------------------------------
    '''
    collection.update_one({'leg_id': bill_issue, 'congress_id': cong_id}, {'$set': {'body': txt}})


def initiate_process(year, collection):
    '''
    ----------------------------------------------
    Initiates process from threads.
    ----------------------------------------------
    '''
    print('--------------------')
    print('Cleaning up year {}'.format(year))
    year_str = str(year)
    
# ##################
#     # this version only populates bill text if it doesn't already exist
#     records_to_populate = collection.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
#     record_count = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
#     print('--> Number of records with no text for year {}: {}'.format(year, record_count))
        
#     if record_count > 0:
#         for rec in records_to_populate:
#             # get complete url using url_builder
#             url = url_builder(rec['leg_url'])
#             # get bill text
#             bill_text = get_bill_text(url)

#             # update mongo record with bill text
#             bill_issue = rec['leg_id']
#             cong_id = rec['congress_id']
#             update_mongo_body(bill_text, bill_issue, cong_id, collection)

            
#             r = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
#             if r%100 == 0:
#                 print('+++++++++')
#                 print('Year {}: {} records remaining with no text'.format(year, r))
#                 print('+++++++++')
# ##################    
    
    # this version will populate bill text regardless of whether it changed, notifying user and logging if it has changed
    records_to_populate = collection.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}})
    record_count = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}})
    print('--> Number of documents to update text for year {}: {}'.format(year, record_count))
    
    log_path = '/home/ubuntu/galvanize_capstone/data/logs/mongo_updates.jsonl'
    i = 0
    
    if record_count > 0:
        for rec in records_to_populate:
            # get complete url using url_builder
            url = url_builder(rec['leg_url'])
            # get bill text
            bill_text = get_bill_text(url)

            # update mongo record with bill text
            if bill_text != rec['body']:
                leg_id = rec['leg_id']
                cong_id = rec['congress_id']
                
                print('Bill text for Congress ID {}, {} has changed. Updating...'.format(cong_id, leg_id))
                line_to_log = {'congress_id': cong_id, 'leg_id': leg_id, 'body': {'old_value': rec['body'], 'new_value': bill_text, 'date': str(date.today().isoformat())}}
                write_json_file(line_to_log, log_path)
                update_mongo_body(bill_text, leg_id, cong_id, collection)


            if i%100 == 0:
                print('+++++++++')
                print(rec['leg_id'])
                print('{:.2f}% complete'.format(100 * i / record_count))
                print('+++++++++')
            i += 1
                
                
if __name__ == '__main__':
    print('This script is populating bill text into Mongo threading two years at a time for those records without any text.')
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_info = db.bill_info

#     # iterate through date range in reverse
#     year_range = range(2007, 2020)[::-1]
    # iterate through date range in reverse
    year_range = range(2019, 2020)[::-1]

    for y in year_range[::2]:
        t1 = threading.Thread(target=initiate_process, args=[y, bill_info])
#         t2 = threading.Thread(target=initiate_process, args=[y-1, bill_info])
#         t3 = threading.Thread(target=initiate_process, args=[y-2, bill_info])
#         t4 = threading.Thread(target=initiate_process, args=[y-3, bill_info])
        
        t1.start()
#         t2.start()
#         t3.start()
#         t4.start()

        t1.join()
#         t2.join()
#         t3.join()
#         t4.join()
        
    print('-----------')
    print('-----------')
    print('Bill text populating complete!... DATA SCIENCE!!!')
    