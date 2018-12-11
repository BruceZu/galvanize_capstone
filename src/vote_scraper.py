from pymongo import MongoClient
import pprint 
import pandas as pd 
import copy
from bs4 import BeautifulSoup
import pprint
import requests
import datetime

from time import sleep
import warnings

import codecs
import json

import boto

def write_json_file(obj, path):
    '''Dump an object and write it out as json to a file'''
    f = codecs.open(path, 'a', 'utf-8')
    json_record = json.dumps(obj, ensure_ascii = False)
    f.write(json_record + '\n')
    f.close
    

def get_all_votes(date_range, root_url):
    print('_______________')
    print('Beginning iterations for House summary data for years {} to {}'.format(min(date_range), max(date_range)))
    print('_______________')
    for yr in date_range:
        site_url = '{}/{}/index.asp'.format(root_url, yr)
        req = requests.get(site_url)
        tstamp = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
        stat_code = req.status_code
        if stat_code != 200:
            print('_______________')
            print('_______________')
            print('Error requesting {}'.format(site_url))
            print('Request Status Code: {}, {}'.format(stat_code, tstamp))
            sleep(3)
            
        if stat_code == 200:            
            final_roll = get_final_roll_id(root_url, yr)
            get_table_summary(root_url, yr, final_roll)

    print('_______________')
    print('_______________')
    print('Iterations through years {} to {} of House summary data complete'.format(min(date_range), max(date_range)))
    print('Last url requested: {}'.format(site_url))
    print("Examine output above for occurrences in request errors, if any.")

    
def get_final_roll_id(site_url_root, yr):
    site_url = '{}/{}/index.asp'.format(site_url_root, yr)
    req = requests.get(site_url)
    stat_code = req.status_code

    # use BeautifulSoup to find the data we need.
    soup = BeautifulSoup(req.content, 'lxml')
    table = soup.find('table')
    rows = table.find_all('tr')

    # initial request of webpage will show the final table with the most recent roll call votes
    # get the largest value of roll for iteration
    final_roll = int(rows[1].find_all('a')[0].text.strip())
    print('Year: {}'.format(yr))
    print('\tFinal Roll ID: {}'.format(final_roll))
    
    return final_roll


def get_table_summary(root_url, yr, final_roll_id):
    # get roll summaries from tables from links at index on bottom left
    indx_list = []
    for i in range(0, final_roll_id + 1):
        if i%100 == 0:
            indx_list.append('{}'.format(str(i).zfill(3)))
    
    for indx in indx_list:
        vote_table_url = '{}/{}/ROLL_{}.asp'.format(root_url, yr, indx)
        req = requests.get(vote_table_url)
        stat_code = req.status_code

        if stat_code != 200:
            print('_______________')
            print('_______________')
            print(site_url)
            print('Request Status Code: {}, {}'.format(stat_code, tstamp))

        if stat_code == 200:
            # use BeautifulSoup to find the data we need.
            soup = BeautifulSoup(req.content, 'lxml')
            table = soup.find('table')            
            rows = table.find_all('tr')
            
            outfile = '../data/vote_results_{}.jsonl'.format(yr)
            append_rows_to_file(rows, yr, outfile)

            
    print('\tIterations through rolls for year {} complete.'.format(yr))
    print('\tLast url: {}'.format(vote_table_url))
    print("\tExamine output above for occurrences in request errors, if any.")
    print('_______________')

    

def append_rows_to_file(rows, yr, filename):
    # all_rows = []
    empty_row = {
                "year": None,
                "roll": None, 
                "date": None, 
                "issue": None,
                "question": None,
                "result": None,
                "description": None, 
                "vote_results": None,
                }

    # skip the header when reading table
    for row in rows[1:]:
        new_row = copy.copy(empty_row)
        columns = row.find_all('td')
        new_row['year'] = yr
        new_row['roll'] = columns[0].text.strip()
        new_row['date'] = columns[1].text.strip()
        new_row['issue'] = columns[2].text.strip()
        new_row['question'] = columns[3].text.strip()
        new_row['result'] = columns[4].text.strip()
        new_row['description'] = columns[5].text.strip()
        
        results = get_vote_results(yr, int(new_row['roll']))
        new_row['vote_results'] = results

    #     all_rows.append(new_row)
        write_json_file(new_row, filename)


# this one should get the actual vote results
def get_vote_results(yr, roll_id):
    # get vote results for a single roll id
    root_url = 'http://clerk.house.gov/evs'
    
    # convert roll id to 3-digits for url
    three_digit_roll = '{}'.format(str(roll_id).zfill(3))

    vote_table_url = '{}/{}/roll{}.xml'.format(root_url, yr, three_digit_roll)
    req = requests.get(vote_table_url)
    stat_code = req.status_code

    # print verification that iterator is working
    if roll_id%100 == 0:
        print('\t\t... working ... ... ... ... ... ...')
        print('\t\t... getting results for Roll ID {}'.format(roll_id))

    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('\t\tError in retrieving vote results for {}'.format(site_url))
        print('\t\tRequest Status Code: {}, {}'.format(stat_code, tstamp))

    if stat_code == 200:
        # use BeautifulSoup to find the data we need.
        soup = BeautifulSoup(req.content, 'lxml')
        recorded_votes = soup.find_all('recorded-vote')

        empty_vote = {
                    'name_id': None, 
                    'name': None,
                    'party': None,
                    'state': None,
                    'vote': None
                    }

        vote_info = []

        for line in recorded_votes:
            new_vote = copy.copy(empty_vote)
            legislator = line.find('legislator')
            new_vote['name'] = legislator.text
            new_vote['vote'] = line.find('vote').text

            for k in list(empty_vote.keys()):
                if k in list(legislator.attrs.keys()):
                    new_vote[k] = legislator[k]

            vote_info.append(new_vote)

        return vote_info
    
    
    

if __name__ == '__main__':
    house_url_root = 'http://clerk.house.gov/evs'

    # date_range = list(range(1990, 2019))
    date_range = list(range(1990, 1992))

    get_all_votes(date_range, house_url_root)