#!/bin/bash

LOG_FILE="/tmp/get_new_data.sh.log"
echo "Logging operations to '$LOG_FILE'"

PROJECT_HOME=`pwd`

echo "" | tee -a $LOG_FILE
echo "Running script get_new_bill_info.py to scrape Congress.gov for bill overview data." | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Running script get_bill_text.py to populate bill text into new Mongo documents" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Running get_amendment_count.py to populate amendment counts into new Mongo documents" | tee -a $LOG_FILE
python $PROJECT_HOME/get_amendment_count.py
