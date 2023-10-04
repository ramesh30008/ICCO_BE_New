import json
import sys
from datetime import datetime
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo, db_str_mongo_old
import mongo_methods

def get_hostpool_regions(subs):
    today = datetime.today()
    month = str(today.month)
    year = str(today.year)
    if len(month) == 1:
        month = "0%s"%month
    region_dict = {}
    for sub in subs:
        sub = sub.replace("-", "")
        collection_name = "%s_%s_%s"%(sub, month, year)
        temp_dict = mongo_methods.get_regions_by_rgroup(db_str_mongo, collection_name) 
        region_dict.update(temp_dict)
    rg_dict = mongo_methods.get_all_rgroups(db_str_mongo, subs)
    res_list = []
    for v in list(rg_dict.keys()):
        if region_dict.get(v):
            temp_list = region_dict.get(v)
            res_list += temp_list
    return list(set(res_list))

def get_timezone(data_dict):
    cust = data_dict.get("cust", "")
    subs = data_dict.get("subs", "")
    #get hostpool region for cust
    region_list = get_hostpool_regions(subs)
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
    region={
    "cust": "HGS CES",
    "subs": [
        "a24d81d4-940f-4503-95d7-46748219b4d8"
    ]
}
    #print(get_timezone(region))
    get_hostpool_regions(region["subs"])
    


