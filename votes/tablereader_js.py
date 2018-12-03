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

import warnings

warnings.filterwarnings('ignore')



def site_table_reader():
    # send GET request using selenium and check status
    option = webdriver.ChromeOptions()
    option.add_argument(' - incognito')

    browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=option)
    site_url = 'https://www.congress.gov/search?q=%7B%22source%22%3A%22legislation%22%7D'
    
    req = requests.get(site_url)
    print('_______________')
    print('Request Status Code: {}'.format(req.status_code))
    
    browser.get(site_url)
    
    # # save html into mongo
    # client = MongoClient('mongodb://localhost:27017/')
    # db = client.bills
    # pages = db.pages
    # pages.insert_one({'html': req.content})

    # parse the html with BeautifulSoup
    soup = bs(browser.page_source, 'lxml')
    print('--------------')
    print('--------------')
    print(soup.title)
    print('--------------')
    # print(soup.prettify())

    # navigate to find bill info
    div = soup.find('div', {'class':'search-column-main'})
    tab = div.find('ol')
    # print(tab)

    all_rows = []

    # # # store each row in a dictionary
    empty_row = {'bill_id': None, 
                'bill_url': None, 
                'congress_id': None,
                'desc': None,
                'sponsor': None, 
                'committee': None, 
                'body': None
                }

    #  need to iterate though each li class to find the above
    rows = tab.find_all('li')
    # pprint.pprint(rows)

    for row in rows[1:]:
        columns = row.find_all('span', {'class': 'result-heading'})
        if len(columns) > 0:
            print(len(columns))
            print(len(columns))
            print(len(columns))

            for col in columns:
                pprint.pprint(col)
                print(len(col))
                # heading = col.find_all('span', {'class': 'result-heading'})
                print('~~~~~~~~~~~~~~~')
                print(col[0])
                print(col[1])
                # if len(col) == 2:
                #     print('111111111: {}'.format(col[0]))
                #     print('222222222: {}'.format(col[1]))
                print ('vvvvvvvvvvvvv')
                print ('vvvvvvvvvvvvv')
                print ('vvvvvvvvvvvvv')
                # row = row.find_all('span', {'class': 'result_heading'})
            # pprint.pprint(columns)



    # # # initialize iterator over the rows in the table
    # rows = tab.find_all('span')


    # for row in rows[1:]:
    #     new_row = copy.copy(empty_row)

    #     # a list of all he entries in the row
    #     columns = row.find_all('td')
        # print(columns)
    #     # new_row['bill_id'] = columns[0].text.strip())
    #     # new_row['bill_desc'] = columns[0].text.strip())
    #     # new_row['intro_date'] = columns[0].text.strip())
    #     # new_row['bill_url'] = columns[0].text.strip())
    #     # new_row['body'] = columns[0].text.strip())




if __name__ == '__main__':
    site_table_reader()