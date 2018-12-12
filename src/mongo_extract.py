from pymongo import MongoClient
import bson.json_util
import copy
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException

import codecs
import json


def write_json_file(obj, path):
    '''Dump an object and write it out as json to a file'''
    f = codecs.open(path, 'a', 'utf-8')
    json_record = json.dumps(obj, ensure_ascii = False)
    f.write(json_record + '\n')
    f.close
    
    
def soup_to_mongo(soup, collection_name):
    '''There are 250 items in each soup object'''
    # table of bills are in ol class
    div = soup.find('div', {'class':'search-column-main'})
    table = div.find('ol')

    # iterate though each li class expanded to get rows
    rows = table.find_all('li', {'class':'expanded'})
    print('\tThere are {} rows to iterate through on this pass.'.format(len(rows)))
    

    # store each row as key-value pair in a dictionary
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
#                 'cosponsors_url': None,
                'cosponsors': None,  #requires navigation to another url and extracting names from table
                'committee': None, 
                'bill_status': None,
                'body': None   #requires navigation to another url
                }


    # for eyeball examination/debugging
    # columns = rows[9].find_all('a')
    # columns

#     all_rows = []
    i = 0

    # iterate through each of the 'rows' to fill in the 'columns'
    for row in rows:
        new_row = copy.copy(empty_row)

        # parse items within 'a' tag
        columns = row.find_all('a')
        if columns[0].text.strip() != '':
            new_row['leg_id'] = columns[0].text.strip().replace('.', ' ')
        if columns[0]['href'].strip() != '':
            new_row['leg_url'] = columns[0]['href'].strip()
        if columns[2].text.strip() != '':
            new_row['num_of_cosponsors'] = columns[2].text.strip()
            if new_row['num_of_cosponsors'] != '0':
                # call function to get cosponsors table from url
                cosponsors_url = columns[2]['href']
                new_row['cosponsors'] = get_cosponsors(cosponsors_url)

        # party, state, and district (for house reps) need to be stripped out of sponsor info
        if columns[1].text.strip() != '':
            rep = columns[1].text.strip()
    #         print(rep)
            new_row['sponsor'] = rep.rsplit('[', 1)[0][:-1]
            party_dist = rep.rsplit('[', 1)[1][: -1]
            party_dist_split = party_dist.split('-')
            new_row['sponsor_state'] = party_dist_split[0]
            new_row['sponsor_party'] = party_dist_split[1]
            if len(party_dist_split) == 3:
                new_row['sponsor_district'] = party_dist_split[2]

        # parse items within 'span' tag
        columns = row.find_all('span')
        if columns[0].text != '':
            new_row['leg_type'] = columns[0].text.strip()
        if columns[1].text.strip().split()[2] != '':
            new_row['congress_id'] = columns[1].text.strip().split()[2]
        if columns[2].text != '':
            new_row['desc'] = columns[2].text
        if columns[4].text.strip()[12:] != '':
            new_row['committee'] = columns[4].text.strip()[12:]
        # date was a little tricky
        dt = columns[3].text.strip().split()
        if '(Introduced' in dt:
            new_row['intro_date'] = dt[dt.index('(Introduced') + 1][:-1]

        # parse items within p tag
        columns = row.find_all('p')
        if columns[0].text.strip()[25:] != '':
            new_row['bill_status'] = columns[0].text.strip()[25:]

#         all_rows.append(new_row)
        collection_name.insert_one(new_row)
        
        i += 1
        if i%20 == 0:
            print('\t\t{:.2f}% complete'.format(100 * i / len(rows)))
        
#     return all_rows



def get_cosponsors(site_url):
    url = site_url

    # send GET request using selenium (sites in javascript)
    option = webdriver.ChromeOptions()
    option.add_argument(' - incognito')
    option.add_argument('--headless')

    browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=option)

    req = requests.get(url)
    
    if req.status_code == 200:
        soup = BeautifulSoup(req.content, 'lxml')
        div = soup.find('div', {'id':'main'})
        table = div.find('table')
        rows = table.find_all('a')

        empty_row = {
            'cosponsor_name': None, 
            'cosponsor_party': None, 
            'cosponsor_state': None,
            'cosponsor_district': None
        }

        all_rows = []

        for row in rows:
            new_row = copy.copy(empty_row)
            rep = row.text.strip()

            new_row['cosponsor_name'] = rep.rsplit('[', 1)[0][:-1]
            party_dist = rep.rsplit('[', 1)[1][: -1]
            party_dist_split = party_dist.split('-')
            new_row['cosponsor_state'] = party_dist_split[0]
            new_row['cosponsor_party'] = party_dist_split[1]
            if len(party_dist_split) == 3:
                new_row['cosponsor_district'] = party_dist_split[2][:-1]

            all_rows.append(new_row)

        return all_rows
    
    else:
        output = {'url': url, 'error': req.status_code}
        outpath = '../data/logs/cosponsor_errors.jsonl'
        write_json_file(outpath, output)

        
if __name__ == '__main__':
    # Set up Mongo for raw data and prettified data
    client = MongoClient() # defaults to localhost
    db = client.bills

    # collection 'pages' is where the raw data is at
    # collection 'bill_details' is where the prettified data will go 
    pages = db.pages

    bill_details = db.bill_details

    num_items = pages.find().count()
    print('There are {} items in this collection.'.format(num_items))
    
    items = pages.find()

    x = 0
    
    for i in items:
        mongo_id = str(i['_id'])
        mongo_log = '../data/logs/mongo_updates.jsonl'
        soup = BeautifulSoup(i['lxml'], 'lxml')
        soup_to_mongo(soup, bill_details)
        write_json_file(mongo_id, mongo_log)

        x += 1
        if x%10 == 0:
            print('Overall, {:.2f}% complete.'.format(100 * x / num_items))