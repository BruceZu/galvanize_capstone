from pymongo import MongoClient
import pprint 
import pandas as pd 
import copy
from bs4 import BeautifulSoup as bs
import requests

import warnings

warnings.filterwarnings('ignore')



def site_table_reader():
    # send GET request
    site_url = 'https://www.congress.gov/bill-texts-received-today'
    req = requests.get(site_url)
    print('_______________')
    print('Request Status Code: {}'.format(req.status_code))
    
    # save html into mongo
    client = MongoClient('mongodb://localhost:27017/')
    db = client.bills
    pages = db.pages
    pages.insert_one({'html': req.content})

    # parse the html with BeautifulSoup
    soup = bs(req.content, 'lxml')
    print('--------------')
    print('--------------')
    print(soup.title)
    print('--------------')
    print(soup.prettify())

    # navigate to pull table info
    div = soup.find('div', {'class': 'main-wrapper'})
    table = div.find('table')
    print(table)

    # initialize iterator over the rows in the table
    rows = table.find_all('tr')
    all_rows = []

    # # store each row in a dictionary
    empty_row = {'bill_id': None, 
                'bill_desc': None, 
                'intro_date': None, 
                'bill_url': None, 
                'body': None
                }

    for row in rows[1:]:
        new_row = copy.copy(empty_row)

        # a list of all he entries in the row
        columns = row.find_all('td')
        print(columns)
        # new_row['bill_id'] = columns[0].text.strip())
        # new_row['bill_desc'] = columns[0].text.strip())
        # new_row['intro_date'] = columns[0].text.strip())
        # new_row['bill_url'] = columns[0].text.strip())
        # new_row['body'] = columns[0].text.strip())




if __name__ == '__main__':
    site_table_reader()