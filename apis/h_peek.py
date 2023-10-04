import sys, time
import copy
from pytz import timezone, utc
from datetime import datetime, timedelta
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo, db_str_mongo_old
import dbApi_mongodb
import mongo_methods
import itertools
import pandas as pd
import table_paginate

def get_all_dates(date_str_list):
    start_date = datetime.strptime(date_str_list[0].split('T')[0], "%Y-%m-%d")
    end_date = datetime.strptime(date_str_list[1].split('T')[0], "%Y-%m-%d")
    delta = end_date - start_date
    all_dates = []
    all_ui_dates = []
    all_months_years = []
    prev_m_y = ""
    for i in range(delta.days+1):
        dt1 = start_date + timedelta(days=i)
        dt2 = dt1.strftime("%Y-%m-%d")
        date_ui = dt1.strftime("%d-%b")
        m_y = "%s_%s"%(dt2[5:7], dt2[:4])
        if m_y != prev_m_y:
            all_months_years.append(m_y)
            prev_m_y = m_y
        dt3 = dt1.strftime("%d-%m-%Y")
        all_dates.append(dt3)
        all_ui_dates.append(date_ui)
    return all_dates, all_ui_dates, all_months_years

def validateFilters(data_key, data_key_cat, filters_cat, filters_val):
    for n, cat in enumerate(filters_cat):
        i = data_key_cat.index(cat)
        if data_key[i] not in filters_val[n]:  
            return False
    return True 

def filter_data(filter_ip_dict, data_dict, data_key_cat, p_index):
    active_filters = filter_ip_dict.get('filter', [])
    my_filters = []
    filters_options = []
    ykeys = {}
    for cat in active_filters:
        if cat not in ["subscriptions"]:
            my_filters.append(cat)
            filters_options.append(filter_ip_dict[cat])
    final_dict = {}
    for data_key, active_cnt in  data_dict.items():
        if my_filters and not validateFilters(data_key, data_key_cat, my_filters, filters_options):
            continue
        #print ("data_key: ", data_key)
        date_str = "%s:00" %data_key[6]
        sub_pkey = data_key[3]
        if not final_dict.get(date_str, {}):
            final_dict[date_str] = {}
        sub_cost_temp  = final_dict.get(date_str, {}).get(sub_pkey, 0)
        sub_cost = sub_cost_temp + active_cnt
        final_dict[date_str][sub_pkey] = sub_cost
        ykeys[sub_pkey] = 1
    #print ("final_dict", final_dict, ykeys) 
    print(final_dict)
    return final_dict, list(ykeys.keys())

def getZeroHostPools(data_dict):
    ykey_cost_dict = {}
    for date_, ykey_dict in data_dict.items():
        for ykey, cost_tup in ykey_dict.items():
            cst_temp = ykey_cost_dict.get(ykey, 0)
            ykey_cost_dict[ykey] = cst_temp+cost_tup
    temp = []
    #print ('ykey_cost_dict: ', ykey_cost_dict)
    for key, val in ykey_cost_dict.items():
        print('fffffffffffffff', key)
        if val==0:
           temp.append(key)  
    return temp

def getFinalDictTable(final_dict, my_ykeys):
    data_dict_arr =[]
    hourkeys = ['0:00', '1:00', '2:00', '3:00', '4:00', '5:00', '6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
    #print ("final_dict: ", final_dict)
    for i, date1 in enumerate(hourkeys):
        ykey_dict = final_dict.get(date1, {})
        temp_dict = {"name":date1, "d_date": date1, "opacity":0.7}
        total = 0
        for ykey in my_ykeys:
            #if ykey in zeroHps: continue
            #print ("ykey: ", ykey)
            cost_tup = ykey_dict.get(ykey, 0)
            temp_dict[ykey] = cost_tup
            total+=cost_tup
        temp_dict["Total"] = round(total, 2)
        data_dict_arr.append(copy.deepcopy(temp_dict))
    return data_dict_arr, hourkeys

def getTableClickData(final_dict, my_ykeys, all_dates, all_ui_dates):
    data_dict_arr =[]
    new_ykeys = []
    for i, date1 in enumerate(all_dates):
        date2 = all_ui_dates[i]
        ykey_dict = final_dict.get(date1, {})
        temp_dict = {"name":"Cost", "d_date": date1}
        total = 0
        currency = "USD"
        cat = 'NA'
        for ykey in my_ykeys:
            cost_tup = ykey_dict.get(ykey, [0, '', 'NA'])
            if round(cost_tup[0], 2)<=0:continue
            temp_dict[ykey] = cost_tup[0]
            temp_dict['%s_Curr'%ykey] = cost_tup[1]
            temp_dict['%s_P'%ykey] = cost_tup[2]
            total+=cost_tup[0]
            currency = cost_tup[1]
            cat = cost_tup[2]
            new_ykeys.append(ykey) 
        temp_dict["Total"] = round(total, 2)
        temp_dict['Total_Curr'] = currency
        temp_dict['Total_P']  = cat
        data_dict_arr.append(copy.deepcopy(temp_dict))
    return data_dict_arr, new_ykeys

def getHPCFilterData(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)
    return {"Subscription": res_dict["sub"], "rproviders":res_dict['resource_provider'] , "Region":res_dict["regions"], "Tags":res_dict["tags"], "Hostpools":res_dict['hostpools']}

def get_date_range():
    today = datetime.today()
    first_range = (str(today - timedelta(days = 8)).split()[0], str(today-timedelta(days = 1)).split()[0])
    second_range = (str(today - timedelta(days = 16)).split()[0],str(today - timedelta(days = 9)).split()[0])
    third_range = (str(today - timedelta(days = 24)).split()[0], str(today - timedelta(days = 17)).split()[0])
    fourth_range = (str(today - timedelta(days = 32)).split()[0],str(today - timedelta(days = 25)).split()[0])
    return [first_range, second_range, third_range, fourth_range]

def getHPCZeroLogins(data_dict):
    dates_ranges = get_date_range()
    tmp_data_dict = data_dict
    tmp_result_list = []
    for datesp in dates_ranges:
        tmp_data_dict["date"] = datesp
        zeroHps = getZeroHPools1(tmp_data_dict)
        #print ("datesp", datesp, zeroHps)
        date_obj = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in datesp]
        date_new = "-".join([d.strftime("%d.%b.%Y") for d in date_obj])
        tmp = {"bodyVal": zeroHps, "header": date_new}
        #print ("tmp: ", tmp) 
        tmp_result_list.append(tmp)
    return {"ZeroLoginData": tmp_result_list}
  
def getZeroHPools1(data_dict):
    subs = data_dict.get("subscriptions", [])
    hostpools = data_dict.get("hostpools", [])
    dates = data_dict.get("date", [])
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    hp_query = {"hostpool_name" :{"$in": hostpools}, "subscription":{"$in":subs}}
    hp_dict = mongo_methods.get_hostpool_names(db_str_mongo_old, "hostpool_mgmt", hp_query)
    sess_hp_query = {"subscription_id":{"$in":subs}}
    sess_hp_dict = mongo_methods.get_hp_from_session_mgmt(db_str_mongo_old, "session_mgmt", sess_hp_query, hp_dict)
    sess_query = {"session_state" :'Active', "date":{"$in":all_dates}}
    sess_data = {}
    for sub in subs:
        sub_new = sub.replace("-", "")
        collection_name = "%s_session_status_timeseries"%(sub_new)
        temp_session_data = mongo_methods.read_session_timeseries(db_str_mongo_old, collection_name, sess_query, sess_hp_dict)
        sess_data.update(temp_session_data)
    print(sess_data)
    date_hour_dict = {}
    d = {}
    for k, v in sess_data.items():
        key = (k[0], k[1], k[2])
        if not date_hour_dict.get(key, 0):
            date_hour_dict[key] = v
        else:
            old_val = date_hour_dict[key]
            if old_val < v:
                date_hour_dict[key] = v
    print(date_hour_dict)
    hour_dict = {}
    for k, v in date_hour_dict.items():
        key = (k[0], k[2])
        if not hour_dict.get(key, 0):
            hour_dict[key] = v
        else:
            old_val = hour_dict[key]
            if old_val < v:
                hour_dict[key] = v
    print(hour_dict)
    data_key_cat = ["hp_name" , "date", "hour", "minute"]
    login_hps = [v[0] for v in date_hour_dict.keys()]
    print(login_hps)
    final_dict, all_ykeys = filter_data1(data_dict, hour_dict, data_key_cat, 6)
    zero_log = list(set(hostpools).difference(set(login_hps)))
    zeroHps = list(set(getZeroHostPools(final_dict)+ zero_log))
    return zeroHps
         

def getZeroHPools(data_dict):
    subs = data_dict.get("subscriptions", [])
    hp_list = data_dict.get("hostpools", [])
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    data_key_cat = ['session_id', "subscriptions", "resource_group", "hostpools", "regions" , "date", "hour", "HP_hpname_hphour"]
    cust_data = {}
    login_hps = []
    for sub in subs:
        sub_new = sub.replace("-", "")
        collection_name = "%s_session_host_status_timeseries"%(sub_new)
        rg_to_hp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sub)
        sesshost_att_dict = mongo_methods.getSessionHostForSubscription(db_str_mongo_old, sub, rg_to_hp_dict)
        print(sesshost_att_dict)
        for k,v in sesshost_att_dict.items():
            login_hps.append(v[2])
        temp_dict = mongo_methods.getTimeSeriesForSessionId(db_str_mongo_old, all_dates, collection_name, sesshost_att_dict)
        cust_data.update(temp_dict)
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 6)
    zero_log = list(set(hp_list).difference(set(login_hps)))
    zeroHps = list(set(getZeroHostPools(final_dict)+ zero_log))
    return zeroHps
 

def getHPCUsageDetails1(data_dict = {}):
    subs = data_dict.get("subscriptions", [])
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    data_key_cat = ['session_id', "subscriptions", "resource_group", "hostpools", "regions" , "date", "hour", "HP_hpname_hphour"]
    cust_data = {}
    for sub in subs:
        sub_new = sub.replace("-", "")
        collection_name = "%s_session_host_status_timeseries"%(sub_new)
        rg_to_hp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sub)
        sesshost_att_dict = mongo_methods.getSessionHostForSubscription(db_str_mongo_old, sub, rg_to_hp_dict)
        print ("sesshost_att_dict: ", sesshost_att_dict)
        temp_dict = mongo_methods.getTimeSeriesForSessionId(db_str_mongo_old, all_dates, collection_name, sesshost_att_dict)
        #print ("temp_dict: ", temp_dict)
        cust_data.update(temp_dict)

    #print ("cust_data: ", cust_data) 
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 6)
    zeroHps = getZeroHostPools(final_dict)
    all_ykeys = list(set(all_ykeys)-set(zeroHps))
    #print ("zeroHps: ", zeroHps)
    #print ("all_ykeys: ", all_ykeys)
    final_tdata_arr, txkeys = getFinalDictTable(final_dict, all_ykeys)
    Tobj =  table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys": txkeys, "tykeys": ["Total"]+all_ykeys, "tdata": final_tdata_arr})
    ntykeys = ndata_dict["tykeys"]
    ntdata = ndata_dict["tdata"]
    return {"txkeys": txkeys,  "tykeys":ntykeys, "tdata":ntdata, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"] }
def filter_data1(filter_ip_dict, data_dict, data_key_cat, p_index):
    active_filters = filter_ip_dict.get('filter', [])
    my_filters = []
    filters_options = []
    ykeys = {}
    for cat in active_filters:
        if cat not in ["subscriptions"]:
            my_filters.append(cat)
            filters_options.append(filter_ip_dict[cat])
    final_dict = {}
    print(data_dict)
    for data_key, active_cnt in  data_dict.items():
        print(data_key, active_cnt)
        if my_filters and not validateFilters(data_key, data_key_cat, my_filters, filters_options):
            continue
        #print ("data_key: ", data_key)
        date_str = "%s:00" %data_key[1]
        hp = data_key[0]
        if not final_dict.get(date_str, {}):
            final_dict[date_str] = {}
        if not final_dict[date_str].get(hp):
            final_dict[date_str][hp] = active_cnt

        ykeys[hp] = 1
    #print ("final_dict", final_dict, ykeys)
    print(final_dict)
    return final_dict, list(ykeys.keys())

def change_timezone(data_dict, tz):
    res_dict = {}
    for k, val in data_dict.items():
        k = list(k)
        date_str = k[1]+ " "+str(k[2])+":"+str(k[3])
        date_d = datetime.strptime(date_str, '%d-%m-%Y %H:%M')
        date_d = date_d.replace(tzinfo=utc)
        converted_date = date_d.astimezone(timezone(tz))
        con_d_str = converted_date.strftime('%Y-%m-%d %-H:%M')
        hour, minute = con_d_str.split()[-1].split(":")

        print("before", k)
        k[2] = int(hour)
        k[3] = int(minute)
        new_key = (k[0], k[1], k[2], k[3])
        res_dict[new_key] = val
    return res_dict

def getHPCUsageDetails(data_dict = {}):
    subs = data_dict.get("subscriptions", [])
    hostpools = data_dict.get("hostpools", [])
    dates = data_dict.get("date", [])
    tz = data_dict.get("tz", "UTC")
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    hp_query = {"hostpool_name" :{"$in": hostpools}, "subscription":{"$in":subs}}
    hp_dict = mongo_methods.get_hostpool_names(db_str_mongo_old, "hostpool_mgmt", hp_query)
    sess_hp_query = {"subscription_id":{"$in":subs}}
    sess_hp_dict = mongo_methods.get_hp_from_session_mgmt(db_str_mongo_old, "session_mgmt", sess_hp_query, hp_dict)
    sess_query = {"session_state" :'Active', "date":{"$in":all_dates}}
    sess_data = {}
    for sub in subs:
        sub_new = sub.replace("-", "")
        collection_name = "%s_session_status_timeseries"%(sub_new)
        temp_session_data = mongo_methods.read_session_timeseries(db_str_mongo_old, collection_name, sess_query, sess_hp_dict)
        sess_data.update(temp_session_data)
    if tz!="UTC":
        change_timezone(sess_data, tz)
    date_hour_dict = {}
    d = {}
    for k, v in sess_data.items():
        key = (k[0], k[1], k[2])
        if not date_hour_dict.get(key, 0):
            date_hour_dict[key] = v
        else:
            old_val = date_hour_dict[key]
            if old_val < v:
                date_hour_dict[key] = v
    print(date_hour_dict)
    hour_dict = {}
    for k, v in date_hour_dict.items():
        key = (k[0], k[2])
        if not hour_dict.get(key, 0):
            hour_dict[key] = v
        else:
            old_val = hour_dict[key]
            if old_val < v:
                hour_dict[key] = v
    print(date_hour_dict)
    data_key_cat = ["hp_name" , "date", "hour", "minute"]
    final_dict, all_ykeys = filter_data1(data_dict, hour_dict, data_key_cat, 6)
    zeroHps = getZeroHostPools(final_dict)
    all_ykeys = list(set(all_ykeys)-set(zeroHps))
    #print ("zeroHps: ", zeroHps)
    #print ("all_ykeys: ", all_ykeys)
    final_tdata_arr, txkeys = getFinalDictTable(final_dict, all_ykeys)
    print(final_tdata_arr)
    Tobj =  table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys": txkeys, "tykeys": ["Total"]+all_ykeys, "tdata": final_tdata_arr})
    ntykeys = ndata_dict["tykeys"]
    ntdata = ndata_dict["tdata"]
    return {"txkeys": txkeys,  "tykeys":ntykeys, "tdata":ntdata, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"] }

if __name__ == '__main__':
    data_dict = {
    "hostpools": [
        "hgs-concor-hp",
        "concor-mm-hp",
        "hgs-agent-hp-uat",
        "windstream-mm_hp",
        "hgs_sony_hp",
        "hgs-ey-hp",
        "hgs-digital",
        "hgs-agent-hp",
        "hgs-sup_hp",
        "windstream-hp",
        "hgs-eit-hp"
    ],
    "subscriptions": [
        "a1c39bf6-6519-4319-9d25-72b011ef01d4"
    ],
    "regions": [
        "global",
        "eastus",
        "centralindia"
    ],
    "tags": [],
    "date": [
        "2023-4-26T00:00:00.0000000Z",
        "2023-5-3T00:00:00.0000000Z"
    ],
    "cust_id": 6,
    "cust_name": "HGS CES",
    "filter": [],
    "tz":"Asia/Kolkata"
}
    print(getHPCUsageDetails(data_dict))
