from pymongo import MongoClient
import pprint 
import pandas as pd 
import copy
from bs4 import BeautifulSoup
import requests
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException

from time import sleep
import warnings

# send GET request using selenium (sites in javascript) and check status
option = webdriver.ChromeOptions()
option.add_argument(' - incognito')
option.add_argument('--headless')

browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', chrome_options=option)

client = MongoClient('mongodb://localhost:27017/')
db = client.bills
vote_records = db.vote_records

# the 101st Congress (1989 - 1990) starts on pg 1011 for pageSize=250
house_url_root = 'http://clerk.house.gov/evs'

date_range = list(range(1990, 2019))
print(date_range)

for yr in date_range:
    site_url = '{}/{}/index.asp'.format(house_url_root, yr)
    req = requests.get(site_url)
    tstamp = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    stat_code = req.status_code
    print('_______________')
    print('_______________')
    print(site_url)
    print('Request Status Code: {}, {}'.format(stat_code, tstamp))