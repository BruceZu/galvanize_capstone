'''
Once data has been populated into Mongo database, this script will populate the amendment
count in the 'num_of_amendments' field if it doesn't already exist. 
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
    contains the amendments of the bill.
    
    Parameters: url from a the leg_url field in a mongo record
    
    Returns:    url to the amendment of the mongo record
    '''
    url_root = record_url.split('?')[0]
    url_tail = record_url.split('?')[1]
    url_s = url_tail.split('&')[0]
    url_r = url_tail.split('&')[1]
    return '{}/amendments?{}&{}'.format(url_root, url_r, url_s)


def get_soup(url):
    '''
    Get soup object from url to be parsed out in another function. If status code != 200, 
    prints out error message.
    
    Parameters: url
    
    Returns: BeautifulSoup object
    '''
    # included sleep time to mimick human user 
    sleep_time = randint(2, 5)
    sleep(sleep_time)
    req = requests.get(url)
    stat_code = req.status_code

    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('')
        print('\t{}'.format(site_url))
        print('\t\tError in retrieving amendment count. Logging...')
        print('\t\tRequest Status Code: {}'.format(stat_code))
        errored_line = {'url': site_url, 'error': stat_code, 'process': 'amendment count'}
        write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')

    if stat_code == 200:
        soup = BeautifulSoup(req.content, 'lxml')
        
        return soup
    

def get_num_of_amendments(soup): 
    '''
    Returns the number of amendments for the specific bill referenced in the soup object.
    '''
    tabs = soup.find('ul', {'class': 'tabs_links'})
    titles = tabs.find_all('a')
    for t in titles:
        if 'Amendment' in t.text:
            return t.text.split()[1].strip('()')

        
def update_mongo_num_of_amendments(leg_id, cong_id, amend_count, collection):
    '''
    Updates the num_of_amendments field in the mongo record specified by bill_issue (leg_id) 
    and cong_id (congress_id) from db.collection with amend_count.
    
    Parameters: leg_id - value to filter on for key leg_id
                cong_id - value to filter on for key congress_id
                amend_count - number of amendments
                collection - the name of the mongo collection
                
    Returns:    None
    '''
    collection.update_one({'leg_id': leg_id, 'congress_id': cong_id}, {'$set': {'num_of_amendments': amend_count}})


def initiate_process(year, collection):
    '''
    Initiates threads.
    '''
    print('--------------------')
    print('Cleaning up year {}'.format(year))
    year_str = str(year)
    records_to_populate = collection.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'num_of_amendments': None})
    record_count = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'num_of_amendments': None})
    print('--> Number of records with no amendment counts for year {}: {}'.format(year, record_count))
    
    if record_count > 0:
        for rec in records_to_populate:
            # get complete url using url_builder
            url = url_builder(rec['leg_url'])
            # scrape url
            soup = get_soup(url)
            # get amendment count
            amendment_count = get_num_of_amendments(soup)

            # update mongo record with bill text
            bill_issue = rec['leg_id']
            cong_id = rec['congress_id']
            update_mongo_num_of_amendments(bill_issue, cong_id, amendment_count, collection)

            
            r = collection.count_documents({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': year_str}, 'num_of_amendments': None})
            if r%100 == 0:
                print('+++++++++')
                print('Year {}: {} records remaining with no amendment counts'.format(year, r))

                
                
if __name__ == '__main__':
    print('****************')
    print('This script is populating amendment counts into Mongo threading four years at a time where needed.')
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_info = db.bill_info

    # iterate through date range in reverse
    year_range = range(2007, 2019)[::-1]

    for y in year_range[::3]:
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
    print('Amendment count populating complete!... DATA SCIENCE!!!')
    