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


from my_tools import write_json_file, read_jsonl_file

# https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu_101_1.htm
# can I employ multithreading to get these quicker?

def get_session_summaries(cong_id, session):
    root_url = 'https://www.senate.gov/legislative/LIS/roll_call_lists/vote_menu'

    site_url = '{}_{}_{}.htm'.format(root_url, cong_id, session)

    sleep_time = randint(0, 5)
    sleep(sleep_time)
    
    req = requests.get(site_url)
    tstamp = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    stat_code = req.status_code
    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('Error requesting summary {}'.format(site_url))
        print('Request Status Code: {}, {}'.format(stat_code, tstamp))

    if stat_code == 200:            
        # use BeautifulSoup to find the data we need.
        soup = BeautifulSoup(req.content, 'lxml')
        table = soup.find('table')
        rows = table.find_all('tr')
        
        outfile = '../data/senate_vote_results_{}_{}.jsonl'.format(cong_id, session)
        append_rows_to_file(cong_id, session, rows, outfile)

        
    print('\tIterations through rolls for cong_id {}, session {} complete.'.format(cong_id, session))
    print('\tLast url: {}'.format(site_url))
    print("\tExamine output above for occurrences in request errors, if any.")
    print('_______________')


def append_rows_to_file(cong_id, session, rows, filename):
    # create dictionaries to get year from cong_id and session
    cong_ids = range(101, 116)
    years_odd = range(1989, 2019, 2)
    years_even = range(1990, 2019, 2)

    s1_congid_dict = {}
    for i, j in zip(cong_ids, years_odd):
        s1_congid_dict.update({i:j})

    s2_congid_dict = {}
    for i, j in zip(cong_ids, years_even):
        s2_congid_dict.update({i:j})
    
    if session%2 == 0:
        yr = s2_congid_dict[cong_id]
    else:
        yr = s1_congid_dict[cong_id]
    

    
    # create an empty row to append to all_records with info filled in
    empty_row = {
        'congress_id': None,
        'session': None,
        'vote_id': None, 
        'issue': None, 
        'result': None, 
        'question': None, 
        'desc': None, 
        'date': None,
        'year': None, 
        'vote_results': None
    }

    
    for i in range(len(rows)):
        columns = rows[i].find_all('td')
        if len(columns) > 0:
            leg_id = columns[3].text

            if ((leg_id.startswith('S. ')) | 
                (leg_id.startswith('S.J.Res')) | 
                (leg_id.startswith('H.R ')) |  
                (leg_id.startswith('H.J.Res'))):
                leg_id = leg_id.replace('.', ' ').replace('  ', ' ').upper().strip()
#                 print('---------')
#                 print(leg_id)
#                 print('---------')


                new_row = copy.copy(empty_row)
                columns = rows[i].find_all('td')
                new_row['congress_id'] = cong_id
                new_row['session'] = session
                new_row['vote_id'] = re.sub(r'[^\x00-\x7F]+', ' ' ,columns[0].text).strip().split(' ')[0]
                new_row['issue'] = leg_id
                new_row['result'] = columns[1].text
                new_row['question'] = columns[2].text.split(':', 1)[0]
                new_row['desc'] = columns[2].text.split(':', 1)[1][1:]
                new_row['date'] = re.sub(r'[^\x00-\x7F]+', ' ' ,columns[4].text).strip()
                new_row['year'] = yr
                new_row['vote_results'] = get_vote_results(cong_id, session, new_row['vote_id'])


                write_json_file(new_row, filename)


def get_vote_results(cong_id, session, vote_id):
    '''
    Gets the votes from individual Senators
    
    Parameters: cong_id - congress id
                session - 1 or 2
                vote_id - the id# of the vote or roll call
                
    Returns: dictionary with keys name, party, state, and vote
    '''
    # convert vote_id to 5-digit string for url
    vote_id_ext = '{}'.format(str(vote_id).zfill(5))
    
    url_root = 'https://www.senate.gov/legislative/LIS/roll_call_lists/roll_call_vote_cfm.cfm?'
    url_tail = 'congress={}&session={}&vote={}'.format(cong_id, session, vote_id_ext)
    site_url = '{}{}'.format(url_root, url_tail)
    
    sleep_time = randint(0, 5)
    sleep(sleep_time)

    req = requests.get(site_url)
    tstamp = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
    stat_code = req.status_code

    # print verification that iterator is working
    if int(vote_id)%50 == 0:
        print('\t\t... getting results for Roll ID {}'.format(vote_id))
        print('\t\t... working backwards ... ... ... ... ... ...')

    if stat_code != 200:
        print('_______________')
        print('_______________')
        print('\t\tError in retrieving vote results for {}'.format(site_url))
        print('\t\tRequest Status Code: {}, {}'.format(stat_code, tstamp))

    if stat_code == 200:
        # use BeautifulSoup to find the data we need.
        soup = BeautifulSoup(req.content, 'lxml')
        recorded_votes = soup.find('span', {'class': 'contenttext'})

        for br in recorded_votes.find_all('br'):
            br.replace_with('\n' + br.text)

        all_rows = []
        
        empty_vote = {
                    'name': None,
                    'party': None,
                    'state': None,
                    'vote': None
                    }
        
        for line in recorded_votes.text.split('\n\n'):
            new_row = copy.copy(empty_vote)
            if ',' in line:
                vote = line.rsplit(', ', 1)[1]
                senator = line.rsplit(', ', 1)[0]
                new_row['vote'] = line.rsplit(', ', 1)[1]
                new_row['name'] = senator.split(' (')[0]

                rep = senator.split(' (')[1].strip(')')
                new_row['party'] = rep.split('-')[0]
                new_row['state'] = rep.split('-')[1]     
                
                all_rows.append(new_row)
                
        return(all_rows)

    
    
if __name__ == '__main__':
    cong_ids = range(101, 116)
    for cong_id in cong_ids[::-1]:
        for session in range(1, 3):
            print('Getting vote data for the Congress ID {}, Session {}'.format(cong_id, session))
            get_session_summaries(cong_id, session)