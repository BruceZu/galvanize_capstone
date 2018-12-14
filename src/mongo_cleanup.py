'''
This script attempts to populate the bill text for each record in mongo database 
bills.bill_details if it doesn't already exist.
'''
from pymongo import MongoClient
import bson.json_util
from bs4 import BeautifulSoup
import requests
import json
import codecs


def write_json_file(obj, path):
    '''Dump an object and write it out as json to a file'''
    f = codecs.open(path, 'a', 'utf-8')
    json_record = json.dumps(obj, ensure_ascii = False)
    f.write(json_record + '\n')
    f.close


def url_builder(record_url):
    '''
    Builds endpoint url from leg_url in mongo. Endpoint url should be the site that 
    contains the text version of the bill.
    
    Parameters: a mongo record
    
    Returns:    url
    '''
    url_root = record_url.rsplit('?')[0]
    return '{}/text?format=txt&r=1'.format(url_root)


def get_bill_text(url):
    '''
    Scrapes the page at url to return the text of the bill.
    
    Parameters: url
    
    Returns: bill text, if it exists
    '''
    site_url = url

    req = requests.get(site_url)
    stat_code = req.status_code
#     print(stat_code)

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
            print('\t\tError in retrieving bill text.')
            print('\t\tNo text available for scraping.')
            errored_line = {'url': site_url, 'error': 'no text available'}
            write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')
            print('\t\tReturned None and error logged in ../data/logs/bill_text_errors.jsonl')
            
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
                
    Returns: None
    '''
    
    collection.update({'leg_id': bill_issue, 'congress_id': cong_id}, {'$set': {'body': txt}})

    

  

  

if __name__ == '__main__':
    client = MongoClient() # defaults to localhost
    db = client.bills
    bill_details = db.bill_details

    # print out record counts
    print('--------------------')
    print('--------------------')
    print('Number of records in database: {}'.format(bill_details.find().count()))
    print('Ignoring RESOLUTIONS, CONCURRENT RESOLUTIONS, and AMENDMENTS for populating bills text.')
    
    # iterate through date range in reverse
    date_range = range(1990, 2019)[::-1]

    for d in date_range:
        print('--------------------')
        print('Cleaning up year {}'.format(d))
        date_str = str(d)
        records_to_pop = bill_details.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': date_str}, 'body': None})
        record_count = records_to_pop.count()
        print('--> Number of records with no text for year {}: {}'.format(d, record_count))


        i = 0
        for rec in records_to_pop:
            # ignore concurrent resolution and simple resolution
            if (rec['leg_type'] != 'CONCURRENT RESOLUTION') & (rec['leg_type'] != 'RESOLUTION') & (rec['leg_type'] != 'AMENDMENT'):
                url = url_builder(rec['leg_url'])
                # get bill text
                bill_text = get_bill_text(url)

                # update mongo record with bill text
                bill_issue = rec['leg_id']
                cong_id = rec['congress_id']
                update_mongo_body(bill_text, bill_issue, cong_id, bill_details)

            i += 1
            if i%200 == 0:
                print('\t{:.2f}% complete'.format(100 * i / record_count))