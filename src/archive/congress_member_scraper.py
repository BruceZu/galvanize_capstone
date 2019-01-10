from pymongo import MongoClient
import pprint 
import pandas as pd 
import copy
from bs4 import BeautifulSoup
import pprint
import requests
import datetime
import re
import os
from random import randint
import datetime
from time import sleep




def get_soup(url):
    '''
    Get soup object from url to be parsed out in another function. If status code != 200, 
    prints out error message.
    
    Parameters: url
    
    Returns: BeautifulSoup object
    '''
    req = requests.get(url)
    sleep_time = randint(0, 11)
    sleep(sleep_time)
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
    
    

def soup_details_to_mongo(cong_id, soup, collection):
    # initialize emtpy_row to populate info
    empty_row = {
        'congress_id': cong_id,
        'name': None,
        'chamber': None,
        'state': None,
        'party': None
    }
    
    table = soup.find('div', {'id': 'main'})

    # house members have district, senate members do not
    for content in table.find_all('li', {'class': 'expanded'}):
        new_row = copy.copy(empty_row)
        details = content.find_all('span')

        # split title from name
        title_name = details[1].text
        title = title_name.split(' ', 1)[0]
        rep_name = title_name.split(' ', 1)[1]
        new_row['name'] = rep_name

        # get state
        new_row['state'] = details[3].text

        # house and senate details are in different spans 
        if 'Representative' in title:
            new_row['chamber'] = 'House'

        if 'Senator' in title:
            new_row['chamber'] = 'Senate'

        # party info in different locations throughout body, iterate through to find
        for i in range(len(details[2:])):
            if 'Party' in details[i].text:
                new_row['party'] = details[i + 1].text

        collection.insert_one(new_row)
    
    


if __name__ == '__main__':
    #initialize Mongo database and collection
    client = MongoClient()
    db = client.bills
    members = db.members

    cong_ids = range(110, 116)
    pages = range(1, 4)
    url_root = 'https://www.congress.gov/members?q=%7B%22congress%22%3A%22'

    for i in cong_ids[::-1]:
        for p in pages:
            url_tail = '{}%22%7D&pageSize=250&page={}'.format(i, p)
            site_url = '{}{}'.format(url_root, url_tail)
            print('Attempting to retrieve members from Congress {}, page {}'.format(i, p))
            soup = get_soup(site_url)
            soup_details_to_mongo(i, soup, members)