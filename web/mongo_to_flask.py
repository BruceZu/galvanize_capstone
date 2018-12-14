from flask import Flask, render_template
from pymongo import MongoClient
import bson.json_util

# Set up Flask
app = Flask(__name__)

# Set up Mongo
client = MongoClient() # defaults to localhost
db = client.bills

# Fetch from/to totals, given a pair of email addresses
@app.route("/leg_id/<id>")
def leg_id(id):
  row = db.bill_details.find({"leg_id": id})
  return render_template('table.html', rows=list(row))


# Fetch from/to totals, given a pair of email addresses
@app.route("/congress_id/<id>")
def congress_id(id):
  row = db.bill_details.find({"congress_id": id})
  return render_template('table.html', rows=list(row))


if __name__ == "__main__": app.run(debug=True, host='0.0.0.0')