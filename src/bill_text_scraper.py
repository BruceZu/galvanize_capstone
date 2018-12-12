
# this script pulls the necessary data from the vote_results jsonl files to create urls to scrape bill text
# for example: https://www.congress.gov/bill/103rd-congress/house-bill/3400/text


import codecs
import json
import os
import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
import requests
import copy



def read_jsonl_file(path):
    '''turn a jsonl file into an array of objects'''
    arr = []
    f = codecs.open(path, 'r', 'utf-8')
    for line in f:
        record = json.loads(line.rstrip('\n|\r'))
        arr.append(record)
    return arr


def write_json_file(obj, path):
    '''Dump an object and write it out as json to a file'''
    f = codecs.open(path, 'a', 'utf-8')
    json_record = json.dumps(obj, ensure_ascii = False)
    f.write(json_record + '\n')
    f.close
    


# create a dataframe of unique bills. Bill_ids will duplicate year over year.
# exclude items that do not pretain to bill info
print('----------------')
print('... importing vote results data...')

bill_list = []

for filename in os.listdir('../data'):
    if filename.startswith('vote_results'):
#         print('\tImporting {}'.format(filename))
        file = read_jsonl_file('../data/{}'.format(filename))
        
        for line in file:
            if (('QUORUM' not in line['issue']) & 
                ('JOURNAL' not in line['issue']) & 
                ('MOTION' not in line['issue']) & 
                ('ADJOURN' not in line['issue'])& 
                (line['issue'] != '')):
                bill_list.append([line['year'], line['issue']])
        
        
# convert bill_list to dataframe
print('----------------')
print('... creating dataframe of unique bills...')
cols = ['year', 'issue']
bills = pd.DataFrame(bill_list, columns = cols)


# drop duplicates and nas
bills.drop_duplicates(inplace = True)
bills.dropna(inplace = True)


# create congress ids for url crawl. One congress_id spans two years
cong_id_list = []

for y in range(101, 117):
    if (y - 1)%10 == 0:
        congress_id = '{}st-congress'.format(y)
        cong_id_list.append(congress_id)

    elif (y - 2)%10 == 0:
        congress_id = '{}nd-congress'.format(y)
        cong_id_list.append(congress_id)
    
    elif (y - 3)%10 == 0:
        congress_id = '{}rd-congress'.format(y)
        cong_id_list.append(congress_id)

    else:
        congress_id = '{}th-congress'.format(y)
        cong_id_list.append(congress_id)

years_odd = []
for y in range(1989, 2019, 2):
    years_odd.append(y)

years_even = []
for y in range(1990, 2020, 2):
    years_even.append(y)

    
    
# create dictionary of years (key) and congress_ids (value)
print('----------------')
print('... creating dictionaries of congress ids and available bill types... ')
congress_ids = {}

for y, i in zip(years_odd, cong_id_list):
    congress_ids.update({y:i})

for y, i in zip(years_even, cong_id_list):
    congress_ids.update({y:i})

    
# append congress_ids to dataframe
bills['congress_id'] = None
for i in range(len(bills)):
    bills.iloc[i, 2] = congress_ids[bills.iloc[i, 0]]

    

# create dictionary of bill_types to join to dataframe
bill_types = {
    'H R': 'house-bill',
    'H RES': 'house-resolution', 
    'H J RES': 'house-joint-resolution',
    'H CON RES': 'house-concurrent-resolution',
    'S': 'senate-bill', 
    'S RES': 'senate-resolution', 
    'S J RES': 'senate-joint-resolution',
    'S CON RES': 'senate-concurrent-resolution'    
}


# create columns for bill_type and bill_num
print('----------------')
print('... appending these to dataframe... ')
bills['bill_type'] = None
for i in range(len(bills)):
    bills.iloc[i, 3] = bill_types[bills.iloc[i, 1].rsplit(' ', 1)[0]]
    
bills['bill_num'] = None
for i in range(len(bills)):
    bills.iloc[i, 4] = bills.iloc[i, 1].rsplit(' ', 1)[1]

    

# iterate through dataframe to build url and scrape bill text
# example: https://www.congress.gov/bill/103rd-congress/house-bill/3400/text
print('----------------')
print('... finally... scraping bill texts... ')

bills['bill_text'] = None

root_url = 'https://www.congress.gov/bill'

empty_row = {
    'year': None, 
    'issue': None, 
    'congress_id': None, 
    'bill_type': None, 
    'bill_num': None, 
    'bill_text':None    
}

def to_jsonl_by_year(df, yr_list):
    for y in yr_list:
        print('Year: {}'.format(y))
        bills = df[df['year'] == y]
        for i in range(len(bills)):
            issue = bills.iloc[i, 1]
            c_id = bills.iloc[i, 2]
            b_type = bills.iloc[i, 3]
            b_num = bills.iloc[i, 4]

            site_url = '{}/{}/{}/{}/text?format=txt'.format(root_url, c_id, b_type, b_num)
#             print(site_url)

            if i%50 == 0:
                pct = 100 * i / len(bills)
                print('\t{:.2f} complete'.format(pct))

            req = requests.get(site_url)
            stat_code = req.status_code

            # if error in getting url, print and log the error
            if stat_code != 200:
                print('_______________')
                print('_______________')
                print('\t\tError in retrieving bill text from {}'.format(site_url))
                print('\t\tRequest Status Code: {}'.format(stat_code))
                errored_line = {'url': site_url, 'error': stat_code}
                write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')
                print('Error logged in ../data/logs/bill_text_errors.jsonl')

            if stat_code == 200:
                req = requests.get(site_url)
                soup = BeautifulSoup(req.content, 'lxml')
                # print(soup.prettify())
                
                # if there is no text, print and log the error
                if soup.find('pre') is None:
                    print('_______________')
                    print('_______________')
                    print('\t\tError in retrieving bill text from {}'.format(site_url))
                    print('\t\tNo text available for scraping.')
                    errored_line = {'url': site_url, 'error': 'no text available'}
                    write_json_file(errored_line, '../data/logs/bill_text_errors.jsonl')
                    print('Error logged in ../data/logs/bill_text_errors.jsonl')
                    
    
                # else scrape the text
                else:
                    bill_txt = soup.find('pre').text
                    bill_txt = ' '.join(bill_txt.split())

                    new_row = copy.copy(empty_row)
                    new_row['year'] = str(bills.iloc[i, 0])
                    new_row['issue'] = str(bills.iloc[i, 1])
                    new_row['congress_id'] = str(bills.iloc[i, 2])
                    new_row['bill_type'] = str(bills.iloc[i, 3])
                    new_row['bill_num'] = str(bills.iloc[i, 4])
                    new_row['bill_text'] = bill_txt

                    outfile = '../data/bill_texts_{}.jsonl'.format(y)

                    write_json_file(new_row, outfile)

        i += 1

        if i == len(bills) - 1:
            print('\t100.00 complete')
            print('\tYear {} complete.'.format(y))
            print('------------------------')
            print('------------------------')

# year_list = range(1990, 2019)
# 1991 is 89% incomplete
# year_list = range(1992, 2019)
# 2007 is 90% complete
# year_list = range(2008, 2019)
# 2013 83% complete
# year_list = range(2013, 2019)

# year_list = [1991, 2007, 2013]
year_list = [1991]


for y in year_list:
    to_jsonl_by_year(bills, year_list)


print('----------------')
print('Script complete. Check results in ../data/bill_texts.jsonl. DATA SCIENCE!!!')


