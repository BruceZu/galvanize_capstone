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


if __name__ == '__main__':
    client = MongoClient()
    db = client.bills
    bill_info = db.bill_info
    
    # retrieve logs where the bill text has changed when get_bill_text was run
    log_path = '/home/ubuntu/galvanize_capstone/data/logs/mongo_updates.jsonl'
    logs = read_jsonl_file(log_path)

    for log in logs:
        if 'body' in log.keys():
            print('----------------------')
            print('----------------------')
            cong_id = log['congress_id']
            leg_id = log['leg_id'] 
            print('The bills text for Congress ID {}, {} has changed. Updating truncated text'.format(cong_id, leg_id))


    # get doc count to show status
    doc_count = bill_info.count_documents({'body': {'$regex': '(.+)'}, 'bill_text': None})
    print('-------------------')
    print('There are {} bills needing truncated text'.format(doc_count))
    
    # retrieve Mongo documents
    documents = bill_info.find({'body': {'$regex': '(.+)'}, 'bill_text': None})

    i = 0
    
    for doc in documents:
        leg_id = doc['leg_id']
        cong_id = doc['congress_id']
        bill_text = doc['body']

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

        # update Mongo
        update_mongo_bill_text(leg_id, cong_id, bill_text_trunc, bill_info)     
        
        # show status
        if i%20 == 0:
            print('{:.2f}% complete truncating bill text'.format(i / doc_count))
        i += 1