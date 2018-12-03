from pymongo import MongoClient
import pprint 
import pandas as pd 
import copy
from bs4 import BeautifulSoup as bs
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException

from time import sleep
import warnings

warnings.filterwarnings('ignore')


# create function get_page_data(site_url)
def page_to_mongo(site_url, collection_name):
    # send GET request using selenium (sites in javascript) and check status
    option = webdriver.ChromeOptions()
    option.add_argument(' - incognito')

    browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=option)

    req = requests.get(site_url)
    print('_______________')
    print('_______________')
    print('Request Status Code: {}'.format(req.status_code))
    if req.status_code == 200:
        # add page html to mongo
        collection_name.insert_one('lxml': req.content)

    # render in browser and parse the html with BeautifulSoup
    browser.get(site_url)
    soup = bs(browser.page_source, 'lxml')
    print('--------------')
    print(site_url)
    print(soup.title)
    # print(soup.prettify())

    # table of bills are in ol class
    # navigate to find bill info
    div = soup.find('div', {'class':'search-column-main'})
    table = div.find('ol')
    # print(table.prettify())

    # iterate though each li class expanded to get rows
    rows = table.find_all('li', {'class':'expanded'})
#     print(rows[0].prettify())

    return rows


    else: 
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        print('failed to get {}'.format(site_url))
        

# function to add items to mongo
def add_to_mongo(rows):
    


    # store each row as key-value pair in a dictionary
    empty_row = {'bill_id': None, 
                'bill_url': None, 
                'congress_id': None,
                'desc': None,
                'sponsor': None, 
    #             'cosponsors': None,  #requires navigation to another url and extracting names from table
                'committee': None, 
                'bill_status': None,
                'body': None   #requires navigation to another url
                }


    # all_rows = []

    # iterate through each of the 'rows' to fill in the 'columns'
    for row in rows:
        new_row = copy.copy(empty_row)

        columns = row.find_all('a')
        new_row['bill_id'] = columns[0].text.strip()
        new_row['bill_url'] = columns[0]['href'].strip()
        new_row['sponsor'] = columns[1].text.strip()

        columns = row.find_all('span')
        new_row['congress_id'] = columns[1].text.strip().split()[2]
        new_row['desc'] = columns[2].text
        new_row['committee'] = columns[4].text.strip()[12:]

        columns = row.find_all('p')
        new_row['bill_status'] = columns[0].text.strip()[25:]

    #     all_rows.append(new_row)
    
    #     store info in mongo
        pages.insert_one(new_row)

if __name__ == '__main__':
    # initialize mongo driver to add items as we iterate through them
    client = MongoClient('mongodb://localhost:27017/')
    db = client.bills
    pages = db.pages

    # the 101st Congress (1989 - 1990) starts on pg 1011 for pageSize=250
    site_url_root = 'https://www.congress.gov/search?q={%22source%22:%22legislation%22}&pageSize=250'
    for i in range(1, 1011):
        site_url = site_url_root + '&page={}'.format(i)
#         print(site_url)
        sleep(20)
        rows = page_to_mongo(site_url, pages)
#         add_to_mongo(rows)

    # all_rows[-5:]

    print('Count of lines loaded: {}'.format(pages.find().count()))