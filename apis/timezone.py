import json
import sys
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo, db_str_mongo_old
import mongo_methods


def timezone(data_dict):
    cust = data_dict.get("cust", "")
    subs = data_dict.get("subs", "")
    #get hostpool region for cust
    region_list = mongo_methods.get_hostpool_regions(db_str_mongo, subs)
  
    res_list = [] 
    with open("all_timezones.json",'r') as f:
        data = json.load(f)
    default=data.get("default", "")
    res_list.append(default)
    for region in region_list:
        region = region.lower()
        timezone=data.get(region, "")
        if timezone:
            res_list.append(timezone)
    return {"tz_list":res_list}     

if __name__=='__main__':
    region={"cust":"ABSLI - AVD", "subs":["555d9f6a-7414-4df4-a94d-c7a6d6ded077"]}
    print(timezone(region))
    


