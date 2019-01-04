from pymongo import MongoClient
import copy
import os

from bs4 import BeautifulSoup
import requests
from random import randint
from time import sleep
import threading

from my_tools import write_json_file


def get_soup(url):
    '''
    ---------------------------------------
    Get soup object from url to be parsed out in another function. If status code != 200, 
    prints out error message.
    
    ---------------------------------------
    Parameters: url
    
    ---------------------------------------
    Returns:    BeautifulSoup object
    
    ---------------------------------------
    '''
    # included sleep time to attempt human user mimicking
    sleep_time = randint(0, 11)
    sleep(sleep_time)
    req = requests.get(url)
    stat_code = req.status_code

    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('Error requesting {}'.format(url))
        print('Request Status Code: {}'.format(stat_code))

    if stat_code == 200:            
        print('_______________')
        print('_______________')
        print('\tRetrieving soup from {}'.format(url))
        soup = BeautifulSoup(req.content, 'lxml')
        
        return soup
    

    
def soup_details_to_list(soup):
    '''
    ---------------------------------------
    Parses out the details from the soup object and inserts the details into list. Each 
    item in the list will be compared to the data that already exists in Mongo.
    
    ---------------------------------------
    Parameters: soup - a soup object with table within 'ol' class
                collection - collection name of Mongo database
                
    ---------------------------------------
    Returns:    list of bill details to compare to what is already in Mongo
    
    ---------------------------------------
    '''
    # initialize empty list to temporarily store data.
    # each item will be checked against Mongo data to see if anything has changed since the last load.
    all_rows = []
    
    # initialize empty row to populate data
    empty_row = {'leg_id': None, 
                'leg_type': None,
                'leg_url': None,
                'intro_date': None,
                'congress_id': None,
                'desc': None,
                'sponsor': None, 
                'sponsor_party': None, 
                'sponsor_state': None,
                'sponsor_district': None,  #senators don't have districts
                'num_of_cosponsors': None,
                'cosponsors_url': None,
                'cosponsors': None,        #requires navigation to another url and extracting names from table
                'num_of_amendments': None,  #requires navigation to another url
                'committee': None, 
                'bill_status': None,
                'body': None               #requires navigation to another url
                }


    # table of bills are in ol class
    div = soup.find('div', {'class':'search-column-main'})
    table = div.find('ol')

    # iterate though each li class expanded to get rows
    rows = table.find_all('li', {'class':'expanded'})
   
    for row in rows:
        new_row = copy.copy(empty_row)
        
#         # debugging
#         columns = row.find_all('a')
#         if columns[0].text.strip() != '':
#             print(columns[0].text.strip().replace('.', ' '))
        
        # parse items within 'span' tag
        columns = row.find_all('span')
        if len(columns) > 3:
            # we only want bills and joint resolutions
            legislation_type = columns[0].text.strip()

            if (legislation_type == 'BILL') |  (legislation_type == 'JOINT RESOLUTION') | (legislation_type == 'LAW'):
                if columns[0].text != '':
                    new_row['leg_type'] = legislation_type
                if columns[1].text.strip().split()[2] != '':
                    new_row['congress_id'] = columns[1].text.strip().split()[2][:3]
                if columns[2].text != '':
                    new_row['desc'] = columns[2].text
                if ('Committee' in columns[4].text):
                    new_row['committee'] = columns[4].text.strip()[12:]

                dt = columns[3].text.strip().split()
                if '(Introduced' in dt:
                    new_row['intro_date'] = dt[dt.index('(Introduced') + 1][:-1]


                # bill_status is within 'p' tag
                columns = row.find_all('p')
                if columns[0].text.strip()[25:] != '':
                    new_row['bill_status'] = columns[0].text.strip()[25:]


                # parse info within 'a' tag
                columns = row.find_all('a')
                if columns[0].text.strip() != '':
                    new_row['leg_id'] = columns[0].text.strip().replace('.', ' ')

                # also within 'a' tag, reserved bill numbers will not have the information below
                if (len(columns) > 2):    
                    if columns[0]['href'].strip() != '':
                        new_row['leg_url'] = columns[0]['href'].strip()
                    if columns[2].text.strip() != '':
                        new_row['num_of_cosponsors'] = columns[2].text.strip()
                        if new_row['num_of_cosponsors'] != '0':
                            new_row['cosponsors_url'] = columns[2]['href']

                # party, state, and district (for house reps) need to be stripped out of sponsor info
                    for c in range(len(columns)):
                        if '[' in columns[c].text.strip():
                            rep = columns[c].text.strip()
                            new_row['sponsor'] = rep.rsplit('[', 1)[0][:-1][5:]
                            party_dist = rep.rsplit('[', 1)[1][: -1]
                            party_dist_split = party_dist.split('-')
                            new_row['sponsor_state'] = party_dist_split[1]
                            new_row['sponsor_party'] = party_dist_split[0]
                            if len(party_dist_split) == 3:
                                new_row['sponsor_district'] = party_dist_split[2]

                all_rows.append(new_row)
            
    return all_rows



def mongo_check(leg_id, cong_id, collection):
    '''
    ---------------------------------------
    Checks to see if a record from web scrape is in Mongo by querying the leg_id and
    cong_id. Returns True if present, else returns False.
    
    ---------------------------------------
    Parameters: leg_id - the bill identifier
                cong_id - the congress id the bill was introduced in
                collection - Mongo collection
                
    ---------------------------------------
    Returns:    boolean - False if record is not present in Mongo, else True
    
    ---------------------------------------
    '''
    mongo_record = collection.find_one({'leg_id': leg_id, 'congress_id': cong_id})
    if mongo_record is None: 
        print('Congress ID {}, Bill {} not in Mongo'.format(cong_id, leg_id))
        return False
    else: 
        return True

    

def update_mongo_value(leg_id, cong_id, key_to_update, new_value, collection):  
    '''
    ---------------------------------------
    Updates the value for a single key in a mongo record specified by leg_id and
    cong_id (congress_id) from db.collection with new_value.
    
    ---------------------------------------
    Parameters: leg_id - value to filter on for key leg_id
                cong_id - value to filter on for key congress_id
                key_to_update - key from document that needs to be updated
                new_value - new value to be inserted into mongo document
                collection - the name of the mongo collection
                
    ---------------------------------------
    Returns:    None
    
    ---------------------------------------
    '''
    collection.update_one({'leg_id': leg_id, 'congress_id': cong_id}, {'$set': {key_to_update: new_value}})


    
def update_mongo_with_list_values(bill_list, collection):
    '''
    ---------------------------------------
    Compares each item in bill_list (scraped data) to documents in Mongo collection. 
    
    If the item is not in Mongo, it inserts it.

    If the item is in Mongo collection, it updates values if they do not match by 
    calling function update_mongo_value.
    
    ---------------------------------------
    Parameters: bill_list - list of bills created from web scrape (soup_details_to_list)
                collection - Mongo collection to query and update, if needed.
                 
    ---------------------------------------
    Returns:    None
    
    ---------------------------------------
    '''
    keys_to_check = ['leg_type', 'desc', 'num_of_cosponsors', 'committee', 'bill_status']

    for i in range(len(bill_list)): 

        list_record = bill_list[i]

        leg_id = list_record['leg_id']
        cong_id = list_record['congress_id']
        
        # check to see if list_record is in Mongo collection and update values
        mongo_document = collection.find_one({'leg_id': leg_id, 'congress_id': cong_id})

        if mongo_check(leg_id, cong_id, collection):
            for k in keys_to_check:
                if list_record[k] != mongo_document[k]:
                    print('\tLogging and updating {} {}... \n\t\t...from {} \n\t\t...to {}'.format(leg_id, k, mongo_document[k], list_record[k]))

                    line_to_log = {'congress_id': cong_id, 'leg_id': leg_id, k: {'old_value': mongo_document[k], 'new_value': list_record[k]}}
                    write_json_file(line_to_log, '/home/ubuntu/galvanize_capstone/data/logs/mongo_updates.jsonl')
                    update_mongo_value(leg_id, cong_id, k, list_record[k], collection)
        
        # if list_record not in Mongo, insert it
        else:
            print('\tInserting new bill {}'.format(leg_id))
            collection.insert_one(list_record)
                


def min_cong_id_in_soup(soup):
    '''
    ---------------------------------------
    Returns the min of congress_id scraped from a soup object. Used to limit web scraping.
    ---------------------------------------
    '''
    cong_ids = []

    # table of bills are in ol class
    div = soup.find('div', {'class':'search-column-main'})
    table = div.find('ol')

    # iterate though each li class expanded to get rows
    rows = table.find_all('li', {'class':'expanded'})
   
    for row in rows:
        # parse items within 'span' tag
        columns = row.find_all('span')

        if columns[1].text.strip().split()[2] != '':
            cong_id = columns[1].text.strip().split()[-3][:3]

            cong_ids.append(int(cong_id))

    return min(cong_ids)




if __name__ == '__main__':
    print('*****************')
    print('This script is scraping to update bill info in Mongo.')
    
    log_path = '/home/ubuntu/galvanize_capstone/data/logs/mongo_updates.jsonl'
    print('Results of this update will be logged in {}'.format(log_path))
    
    # initialize Mongo client
    client = MongoClient()
    db = client.bills
    bill_info = db.bill_info

    # reset log
    if os.path.exists(log_path):
        os.remove(log_path)

    # 110th Congress ends at page 444, but break will limit scraping
    page_range = range(1, 500)
    
    min_cong_id = 115

    url_root = 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D&pageSize=250&page='

    for p in page_range:
        # update Mongo with site contents where necessary
        site_url = '{}{}'.format(url_root, p)
        soup = get_soup(site_url)
        bill_list = soup_details_to_list(soup)
        update_mongo_with_list_values(bill_list, bill_info)

        # break out of loop if the min congress id limit has been reached
        min_cong_id_on_page = min_cong_id_in_soup(soup)
        if min_cong_id_on_page < min_cong_id:
            break