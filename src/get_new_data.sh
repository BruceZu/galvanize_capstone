#!/bin/bash

LOG_FILE="/tmp/get_new_data.sh.log"
echo "Logging operations to '$LOG_FILE'"

PROJECT_HOME=`pwd`

echo "" | tee -a $LOG_FILE
echo "Running script get_new_bill_info.py to scrape Congress.gov for bill overview data." | tee -a $LOG_FILE
python $PROJECT_HOME/get_new_bill_info.py

echo "" | tee -a $LOG_FILE
echo "Running script get_bill_text.py to populate bill text into new Mongo documents" | tee -a $LOG_FILE
python $PROJECT_HOME/get_bill_text.py

echo "" | tee -a $LOG_FILE
echo "Running get_amendment_count.py to populate amendment counts into new Mongo documents" | tee -a $LOG_FILE
python $PROJECT_HOME/get_amendment_count.py

echo "" | tee -a $LOG_FILE
echo "Running truncate_bill_text.py to truncate bill texts on Mongo documents" | tee -a $LOG_FILE
python $PROJECT_HOME/truncate_bill_text.py

echo "" | tee -a $LOG_FILE
echo "Running nlp_pipeline.py to process new text" | tee -a $LOG_FILE
python $PROJECT_HOME/nlp_pipline.py

echo "" | tee -a $LOG_FILE
echo "Running script make_predictions.py to predict on new data and load it into Mongo for Flask app" | tee -a $LOG_FILE
python $PROJECT_HOME/make_predictions.py
