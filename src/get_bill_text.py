'''
Once data has been populated into Mongo database, this script will populate the bill text
in the 'body' field if text doesn't already exist. 
'''
from pymongo import MongoClient
from bs4 import BeautifulSoup
import requests
import threading
from random import randint
from time import sleep

from my_tools import write_json_file


def url_builder(record_url):
    '''
    Builds endpoint url from leg_url in mongo. Endpoint url should be the site that 
    contains the text version of the bill.
    
    Parameters: a mongo record
    
    Returns:    url
    '''
    url_root = record_url.rsplit('?')[0]
    return '{}/text?format=txt&r=1'.format(url_root)


def get_bill_text(site_url):
    '''
    Scrapes the page at url to return the text of the bill.
    
    Parameters: url
    
    Returns:    bill text, if it exists
    '''
    # included sleep time to mimick human user 
    sleep_time = randint(2, 5)
    sleep(sleep_time)

    req = requests.get(site_url)
    stat_code = req.status_code

    # if error in getting url, print and log the error
    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('')
        print('\t{}'.format(site_url))
        print('\t\tError in retrieving bill text.')
        print('\t\tRequest Status Code: {}'.format(stat_code))
        errored_line = {'url': site_url, 'error': stat_code}
        write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')
        print('Error logged in ../data/logs/bill_text_errors.jsonl')

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
            write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')
            
            return None


        # else scrape the text
        else:
            bill_txt = soup.find('pre').text
            bill_txt = ' '.join(bill_txt.split())

            return bill_txt


def update_mongo_body(txt, bill_issue, cong_id, collection):  
    '''
    Updates the body field in the mongo record specified by bill_issue (leg_id) and
    cong_id (congress_id) from db.collection with txt.
    
    Parameters: txt - the text of the bill
                bill_issue - value to filter on for key leg_id
                cong_id - value to filter on for key congress_id
                collection - the name of the mongo collection
                
    Returns:    None
    '''
    collection.update_one({'leg_id': bill_issue, 'congress_id': cong_id}, {'$set': {'body': txt}})


def initiate_process(year, collection):
    '''
    Initiates process from threads.
    '''
#     client = MongoClient() # defaults to localhost
#     db = client.bills
#     bill_info = db.bill_info

    print('--------------------')
    print('Cleaning up year {}'.format(year))
    year_str = str(year)
    records_to_populate = collection.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
    record_count = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
    print('--> Number of records with no text for year {}: {}'.format(year, record_count))
    
    if record_count > 0:
        for rec in records_to_populate:
            # get complete url using url_builder
            url = url_builder(rec['leg_url'])
            # get bill text
            bill_text = get_bill_text(url)

            # update mongo record with bill text
            bill_issue = rec['leg_id']
            cong_id = rec['congress_id']
            update_mongo_body(bill_text, bill_issue, cong_id, collection)

            
            r = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'body': None})
            if r%100 == 0:
                print('+++++++++')
                print('Year {}: {} records remaining with no text'.format(year, r))
                print('+++++++++')
    
                
if __name__ == '__main__':
    print('This script is populating bill text into Mongo threading four years at a time for those records without any text.')
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_info = db.bill_info

    # iterate through date range in reverse
    year_range = range(2007, 2019)[::-1]

    for y in year_range[::4]:
        t1 = threading.Thread(target=initiate_process, args=[y, bill_info])
        t2 = threading.Thread(target=initiate_process, args=[y-1, bill_info])
        t3 = threading.Thread(target=initiate_process, args=[y-2, bill_info])
        t4 = threading.Thread(target=initiate_process, args=[y-3, bill_info])
        
        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()
        
    print('-----------')
    print('-----------')
    print('Bill text populating complete!... DATA SCIENCE!!!')
    