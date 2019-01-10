'''
This script truncates the 'body' in each Mongo document to store the actual bill text in key bill_text
'''
from pymongo import MongoClient
from my_tools import read_jsonl_file
from datetime import date

def update_mongo_bill_text(leg_id, cong_id, bill_text_trunc, collection):
    '''
    ------------------------------------------
    Updates the bill_text field in the mongo record specified by bill_issue (leg_id) 
    and cong_id (congress_id) from db.collection with bill_text_trunc.
    
    ------------------------------------------
    Parameters: leg_id - value to filter on for key leg_id
                cong_id - value to filter on for key congress_id
                bill_text - truncated text in 'body'
                collection - the name of the mongo collection
                
    ------------------------------------------
    Returns:    None
    
    ------------------------------------------
    '''
    collection.update_one({'leg_id': leg_id, 'congress_id': cong_id}, {'$set': {'bill_text': bill_text_trunc}})


def truncate_bill_body(bill_text):
    '''
    ------------------------------------------
    Clips the header and footer of bill_text to eliminate (or just reduce?) data leakage.
    
    
    ------------------------------------------
    Parameters: bill_text - 'body' field in Mongo documents
    
    
    ------------------------------------------
    Returns:    bill_text_trunc - clipped text
    
    ------------------------------------------
    '''
    # search through headers to get index
    if ('A BILL' in bill_text[:5000]):
        header_text = 'A BILL'

    elif ('A Bill' in bill_text[:5000]):
        header_text = 'A Bill'            

    elif ('JOINT RESOLUTION' in bill_text[:5000]): 
        header_text = 'JOINT RESOLUTION'

    elif ('Joint Resolution' in bill_text[:5000]):
        header_text = 'Joint Resolution'

    elif ('An Act' in bill_text[:5000]): 
        header_text = 'An Act'

    elif ('AN ACT' in bill_text[:5000]): 
        header_text = 'AN ACT'

    else: 
        header_text = 'ing Office'

    text_start = bill_text.find(header_text)

    # truncate the bill_text to remove header
    bill_text_trunc = bill_text[text_start:].split(' ', 2)[2]


    # truncate bill text to remove footer
    if 'LEGISLATIVE HISTORY' in bill_text_trunc:
        text_end = bill_text_trunc.find('LEGISLATIVE HISTORY')
        bill_text_trunc = bill_text_trunc[:text_end].rsplit('Approved')[0]

    return bill_text_trunc    
    
    
    

if __name__ == '__main__':
    client = MongoClient()
    db = client.bills
    bill_info = db.bill_info
    
    # retrieve logs where the bill text has changed when get_bill_text was run
    log_path = '/home/ubuntu/galvanize_capstone/data/logs/mongo_updates.jsonl'
    logs = read_jsonl_file(log_path)
    
    today = date.today().isoformat()

    for log in logs:
        # check to see if the body was updated with get_bill_text today
        if 'body' in log.keys():
            if log['body']['date'] == today:
                cong_id = log['congress_id']
                leg_id = log['leg_id'] 
                print('\t\tThe bills text for Congress ID {}, {} has changed. Updating truncated text'.format(cong_id, leg_id))

                # use cong_id and leg_id in log to pull bill text from Mongo and clip it
                doc = bill_info.find_one({'congress_id': cong_id, 'leg_id': leg_id})
                bill_text_clipped = truncate_bill_body(doc['body'])

                # update Mongo
                update_mongo_bill_text(leg_id, cong_id, bill_text_clipped, bill_info)     

            
            
            