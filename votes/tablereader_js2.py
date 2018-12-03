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
print(tab.prettify())