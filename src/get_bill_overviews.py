import pandas as pd
from pymongo import MongoClient
import copy
from bs4 import BeautifulSoup
import requests
from random import randint
from time import sleep
import threading

def get_soup(url):
    '''
    Get soup object from url to be parsed out in another function. If status code != 200, 
    prints out error message.
    
    Parameters: url
    
    Returns: BeautifulSoup object
    '''
    # included sleep time to attempt human user mimicking
    sleep_time = randint(0, 6)
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
    

def soup_details_to_mongo(soup, collection):
    '''
    Parses out the details from the soup object and inserts the details into 
    Mongo database collection row by row.
    
    Parameters: soup - a soup object with table within 'ol' class
                collection - collection name of Mongo database
                
    Returns:    None
    '''
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
            
                collection.insert_one(new_row)


            
def get_amendment_count(url):
    '''
    Returns amendment counts for a bill at the url
    
    Parameters: url - url that gives access to bill details
    
    Return: Integer - count of amendments
    '''
    soup = get_soup(url)
    
    # iterate through tabs to find Amendments and get count
    tabs = soup.find('nav', {'id': 'tabs'})
    info = tabs.find_all('a')
    for i in info:
        if 'Amendment' in i.text.split()[0]:        
            return i.text.split()[1].strip('()')
        
        
        
def initiate_process(page):
    client = MongoClient()
    db = client.bills
    bill_info = db.bill_info

    url_root = 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D&pageSize=250&page='
    
    site_url = '{}{}'.format(url_root, page)

#     print(site_url)
    soup = get_soup(site_url)
    soup_details_to_mongo(soup, bill_info)
    
        
        
        

if __name__ == '__main__':
    # begin by populating Mongo with general info for bills and joint resolutions using threading

    # the 110th Congress ends on page 444 with 250 results on page
    # https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D&pageSize=250&page=2
    page_range = range(1, 445)

    for p in page_range[::4]:
        t1 = threading.Thread(target=initiate_process, args=[p])
        t2 = threading.Thread(target=initiate_process, args=[p+1])
        t3 = threading.Thread(target=initiate_process, args=[p+2])
        t4 = threading.Thread(target=initiate_process, args=[p+3])

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
    print('Initial data collection complete!... DATA SCIENCE!!!')

    
    
    
    # once mongo data is populated, retrieve data from mongo to fill in additional details
    
    
    