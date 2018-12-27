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
from random import randint
from time import sleep
import datetime
import copy
import pandas as pd



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


def update_mongo_body(txt, bill_issue, cong_id, collection):  #this function is missing session 
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

    
    
    
def update_mongo_votes(collection, cong_id, session, vote_id, votes):
    '''
    Updates the vote_results field in the mongo record specified by bill_id (leg_id) and
    cong_id (congress_id) from db.collection with votes.
    
    Parameters:
                collection - the name of the mongo collection
                cong_id - value to filter on for key congress_id
                bill_id - value to filter on for key leg_id
                votes - json line of names, votes and other metadata

    Returns: None
    '''
    
    collection.update_one({'congress_id': int(cong_id), 'session': int(session), 'vote_id': str(vote_id)}, {'$set': {'vote_results': votes}})

    
    
    
    
def get_vote_results(cong_id, session, vote_id):
    '''
    Gets the votes from individual Senators
    
    Parameters: cong_id - congress id
                session - 1 or 2
                vote_id - the id# of the vote or roll call
                
    Returns: dictionary with keys name, party, state, and vote
    '''
    # convert vote_id to 5-digit string for url
    vote_id_ext = '{}'.format(str(vote_id).zfill(5))
    
    url_root = 'https://www.senate.gov/legislative/LIS/roll_call_lists/roll_call_vote_cfm.cfm?'
    url_tail = 'congress={}&session={}&vote={}'.format(cong_id, session, vote_id_ext)
    site_url = '{}{}'.format(url_root, url_tail)
    
    req = requests.get(site_url)
    sleep_time = randint(0, 5)
    sleep(sleep_time)

    tstamp = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    stat_code = req.status_code

    # print verification that iterator is working
    if int(vote_id)%50 == 0:
        print('\t\t... getting results for Roll ID {}'.format(vote_id))
        print('\t\t... working backwards ... ... ... ... ... ...')

    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('\t\tError in retrieving vote results for Congress {}, Session {}, Vote Id {}'.format(cong_id, session, vote_id))
        print('\t\tRequest Status Code: {}, {}'.format(stat_code, tstamp))
        
    

    if stat_code == 200:
        # use BeautifulSoup to find the data we need.
        soup = BeautifulSoup(req.content, 'lxml')
        recorded_votes = soup.find('span', {'class': 'contenttext'})

        for br in recorded_votes.find_all('br'):
            br.replace_with('\n' + br.text)

        all_rows = []
        
        empty_vote = {
                    'name': None,
                    'party': None,
                    'state': None,
                    'vote': None
                    }
        
        for line in recorded_votes.text.split('\n\n'):
            new_row = copy.copy(empty_vote)
            if ',' in line:
                vote = line.rsplit(', ', 1)[1]
                senator = line.rsplit(', ', 1)[0]
                new_row['vote'] = line.rsplit(', ', 1)[1]
                new_row['name'] = senator.split(' (')[0]

                rep = senator.split(' (')[1].strip(')')
                new_row['party'] = rep.split('-')[0]
                new_row['state'] = rep.split('-')[1]     
                
                all_rows.append(new_row)
                
        return(all_rows)
    


if __name__ == '__main__':
    client = MongoClient() # defaults to localhost
    db = client.bills
#     bill_details = db.bill_details
    senate_votes = db.senate_votes
    
#     # print out record counts
#     print('--------------------')
#     print('--------------------')
#     print('Number of records in database: {}'.format(bill_details.find().count()))
#     print('Ignoring RESOLUTIONS, CONCURRENT RESOLUTIONS, and AMENDMENTS for populating bills text.')
    
#     # iterate through date range in reverse
#     date_range = range(1990, 2019)[::-1]

#     for d in date_range:
#         print('--------------------')
#         print('Cleaning up year {}'.format(d))
#         date_str = str(d)
#         records_to_pop = bill_details.find({'leg_url': {'$regex': 'http'}, 'intro_date': {'$regex': date_str}, 'body': None})
#         record_count = records_to_pop.count()
#         print('--> Number of records with no text for year {}: {}'.format(d, record_count))


#         i = 0
#         for rec in records_to_pop:
#             # ignore concurrent resolution and simple resolution
#             if (rec['leg_type'] != 'CONCURRENT RESOLUTION') & (rec['leg_type'] != 'RESOLUTION') & (rec['leg_type'] != 'AMENDMENT'):
#                 url = url_builder(rec['leg_url'])
#                 # get bill text
#                 bill_text = get_bill_text(url)

#                 # update mongo record with bill text
#                 bill_issue = rec['leg_id']
#                 cong_id = rec['congress_id']
#                 update_mongo_body(bill_text, bill_issue, cong_id, bill_details)

#             i += 1
#             if i%200 == 0:
#                 print('\t{:.2f}% complete'.format(100 * i / record_count))

    # update senate_votes with vote_results
    missing_votes = senate_votes.find({'vote_results': None})

    cols = ['_id', 
            'congress_id', 
            'session', 
            'vote_id', 
            'issue', 
            'result', 
            'question', 
            'desc', 
            'date', 
            'year', 
            'vote_results']
    df = pd.DataFrame(columns = cols)

    for i in range(missing_votes.count()):
        df = df.append(pd.DataFrame.from_dict(missing_votes[i], orient='index').T, ignore_index=True)

    print('{} records found without vote details'.format(df.shape[0]))
    
    for i in range(df.shape[0]):
        cong_id = df.iloc[i, 1]
        sess = df.iloc[i, 2]
        vote_id = df.iloc[i, 3]

        votes = get_vote_results(cong_id, sess, vote_id)
        print('votes: {}'.format(votes))
        update_mongo_votes(senate_votes, cong_id, sess, vote_id, votes)

        vote_upload = senate_votes.find_one({'congress_id': int(cong_id), 'session': int(sess), 'vote_id': str(vote_id)})
        if vote_upload['vote_results'] is not None: 
            print('Vote upload successful for Congress {}, Session {}, Vote ID {}'.format(cong_id, sess, vote_id))
        else:
            print('\t\tERROR uploading votes for Congress {}, Session {}, Vote ID {}'.format(cong_id, sess, vote_id))
    