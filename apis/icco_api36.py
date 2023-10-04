import sys, time
import copy
import time
import cProfile
from datetime import datetime, timedelta
sys.path.insert(0, '/var/www/html/icco_dev/icco_api_dev/')
sys.path.append('/var/www/html/icco_dev/icco_api_dev/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_mongodb
import dbApi
import mongo_methods
import itertools
import pandas as pd

def getTagsFilters(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)
    return {"Hostpools":res_dict["hostpools"], "Subscription":res_dict["sub"], "Region": res_dict["regions"], "Tags": res_dict["tags"]}

