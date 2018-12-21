from flask import Flask, render_template, request
from pymongo import MongoClient
import bson.json_util


def convert_yr_to_congid(yr):
    # create dictionaries to get year from cong_id and session
    cong_ids = range(101, 116)
    years_odd = range(1989, 2019, 2)
    years_even = range(1990, 2019, 2)

    odd_yr_dict = {}
    for i, j in zip(years_odd, cong_ids):
        odd_yr_dict.update({i:j})

    even_yr_dict = {}
    for i, j in zip(years_even, cong_ids):
        even_yr_dict.update({i:j})
        
    if int(yr)%2 == 0:
        return even_yr_dict[yr]
    else:
        return odd_yr_dict[yr]

        
# Set up Flask
app = Flask(__name__)

# Set up Mongo
client = MongoClient() # defaults to localhost
db = client.bills


#Controller: Fetch all 


# Fetch bills/laws by leg_id
@app.route("/leg_id/<id>")
def leg_id(id):
    # return search results sorted by most recent
    row = db.bill_details.find({'$query': {"leg_id": id}, 
                                '$orderby': {'congress_id': -1}})
    
    return render_template('table.html', rows=list(row))


# Fetch bills/laws by congress_id
@app.route("/congress_id/<id>")
def congress_id(id):
    row = db.bill_details.find({'$query': {"congress_id": id}, 
                                '$orderby': {'intro_date': -1}})
    
    return render_template('table.html', rows=list(row))





# Fetch bill in current congress that originated in the House
@app.route("/house_bills")
def house_bills():
    bills = db.bill_details.find({'leg_id': {'$regex': '^H'}, 'congress_id': '115th'}, 
                                 sort = [('intro_date', -1)])  
    
    bill_count = bills.count()
    return render_template('bills.html', bills=bills, origin='House', bill_count=bill_count)
    
    
    
    
    
# Fetch bill in current congress that originated in the House
@app.route("/senate_bills")
def senate_bills():
    bills = db.bill_details.find({'leg_id': {'$regex': '^S'}, 'congress_id': '115th'}, 
                                 sort = [('intro_date', -1)])  
    
    bill_count = bills.count()
    return render_template('bills.html', bills=bills, origin='Senate', bill_count=bill_count)


# Fetch an atomic record
@app.route("/bill_info")
def bill_info():
    
    bill_id = request.args.get('leg_id')
    cong_id = request.args.get('congress_id')
    
    
    bill = db.bill_details.find_one({'leg_id': bill_id, 'congress_id': cong_id})

    return render_template('bill.html', bill=bill)





if __name__ == "__main__": 
    app.run(debug=True, host='0.0.0.0')