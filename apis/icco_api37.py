import sys, time
import copy
import time
import cProfile
from datetime import datetime, timedelta
from bson import ObjectId
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_mongodb
import dbApi
import mongo_methods
import itertools
import pandas as pd


def getDesktopFilters(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.get_subids(db_str_mongo, cust_name)
    filter_data = mongo_methods.get_desktop_mgmt_data(db_str_mongo, res_dict["sub"]) 
    return {"Hostpools":filter_data[0], "Subscription":filter_data[3], "Region": filter_data[1], "Tags": [], "rproviders":filter_data[2]}

def logic_80_20(data_dict):
    out = {}
    for date_, hostpool_dict in data_dict.items():
        for hostpool, cost in hostpool_dict.items():
            if not out.get(hostpool, {}):
                out[hostpool] = cost
            else:
                out[hostpool]+=cost

    tup_val = [(v,k)for k,v in out.items()]
    tup_val = sorted(tup_val, reverse=True)
    top_7_hostpool = [k for (v,k) in tup_val[:7]]
    gdata_dict = {}
    for date_, hostpool_dict in data_dict.items():
        new_hostpool_dict = {}
        for hostpool, cost in hostpool_dict.items():
            if hostpool in top_7_hostpool:
                new_hostpool_dict[hostpool] = cost
            else:
                cost_o = new_hostpool_dict.get('Others', 0)
                new_hostpool_dict['Others'] = round(cost_o+cost,2)
        gdata_dict[date_] = copy.deepcopy(new_hostpool_dict)
    gykeys = top_7_hostpool + ["Others"]
    return gdata_dict, gykeys

def get_all_dates(start_date, end_date,flag = 0):
    delta = end_date - start_date
    dates = []
    for i in range(delta.days+1):
        dt1 = start_date + timedelta(days=i)
        if flag == 1:
            dt2 = dt1.strftime("%d-%m-%Y")
        else:
            dt2 = dt1.strftime("%Y-%m-%d")
        dates.append(dt2)
    #dates = [start_date + timedelta(days=i).strptime("%d-%m-%Y") for i in range(delta.days+1)]
    return dates

def get_all_months(date_str_list):
    month_list = []
    for date_ in date_str_list:
        y,m,d = date_.split("-")
        m_y = "%s_%s"%(m,y)
        if m_y not in month_list:
            month_list.append(m_y)
    return month_list

def getFinalDictCustomer_tdata(final_dict, all_dates, curr_dict):
    out =[]
    subs_distinct = {}
    dcurr = 'USD'
    for date1,date2 in all_dates:
        v = final_dict.get(date1, {})
        print(v)
        temp_dict = {}
        temp_dict["name"] = date1
        temp_dict["d_date"] = date2
        total = 0
        for hostpool, cost in v.items():
            currency = "USD"
            if currency:dcurr = currency
            else:
               currency = dcurr
            #currency = dbApi.get_currency(db_str_mysql, sub.lower())
            temp_dict[hostpool] = cost
            subs_distinct[hostpool] = 1
            total+=cost
            temp_dict['%s_Curr'%hostpool]  = currency
        temp_dict["opacity"] = 0.7
        temp_dict["Total"] =  round(total, 2)
        out.append(copy.deepcopy(temp_dict))
    return out, subs_distinct

def getFinalDictCustomer(final_dict, all_dates, curr_dict):
    out =[]
    subs_distinct = {}
    dcurr = 'USD'
    for date1,date2 in all_dates:
        v = final_dict.get(date1, {})
        print(v)
        temp_dict = {}
        temp_dict["name"] = date1
        temp_dict["d_date"] = date2
        total = 0
        for hostpool, cost in v.items():
            currency = "USD"
            if currency:dcurr = currency
            else:
               currency = dcurr
            #currency = dbApi.get_currency(db_str_mysql, sub.lower())
            temp_dict[hostpool] = cost
            subs_distinct[hostpool] = 1
            total+=cost
            temp_dict['%s_Curr'%hostpool]  = currency
        temp_dict["opacity"] = 0.7
        temp_dict["Total"] =  round(total, 2)
        out.append(copy.deepcopy(temp_dict))
    return out, subs_distinct



def TagExplorerCostHistory(data_dict):
    #if data_dict.get("cust_id", ""):
    dates = data_dict["date"]
    #dates = [datetime.strptime(d, '%Y-%m-%d') for d in data_dict["date"]]
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list = get_all_dates(dates[0], dates[1])
    xkeys_obj = [datetime.strptime(k, "%Y-%m-%d")for k in date_str_list]
    xkeys = [date_obj.strftime("%d-%b") for date_obj in xkeys_obj]
    hp_list = data_dict["hostpools"]
    location_list = data_dict["regions"]
    rprovider_list = data_dict["rproviders"]
    sub_idxs = data_dict["subscriptions"]
    result_dict = {}   
    tags_info = {}  
    for subidx in sub_idxs:
        nsubidx = "".join(subidx.split("-"))
        tags_info.update(mongo_methods.read_tag_mgmt(db_str_mongo, subidx)[0])
        temp_res = mongo_methods.read_subs_cost(db_str_mongo, nsubidx+"_12_2022", date_str_list, subidx)
        result_dict.update(temp_res) 
    

    print ('result_dict: ', result_dict)
    results_info = {}
    for tag in tags_info.keys():
        if not results_info.get(tag, []):
           results_info[tag] = {}
        rps = tags_info[tag]
        for rp, rs in rps:
            cost = result_dict.get((rp, rs), "")
            if not str(cost): continue
            if not results_info[tag].get(rp, {}):
               results_info[tag][rp] = {}
            results_info[tag][rp][rs] = cost

    print("results_info: ", results_info)  
  
    result_ar = []
    for tag, vs_dict in results_info.items():
        tag_sum = 0
        tmp_c1 = [] 
        for rp, rn_dict in vs_dict.items():
            rp_sum = 0
            tmp_c2 = [] 
            for rn, cost_dict in rn_dict.items():
                rp_sum += cost_dict["cost"]
                rn_temp = {"resource": rn, "account": cost_dict["sub"], "region": cost_dict["region"], "cost": cost_dict["cost"]} 
                tmp_c2.append(rn_temp)
            rp_temp = {"network": rp, "cost": rp_sum, "children": tmp_c2}  
            tmp_c1.append(rp_temp)
            tag_sum += rp_sum
        tag_tmp = {"tag": tag, "cost": tag_sum, "children": tmp_c1}
        result_ar.append(tag_tmp)
    return result_ar   

def tableClickResources(data_dict):
    rname = data_dict["rname"]
    sids = list(set(mongo_methods.get_subscriptions_by_rname(db_str_mongo, rname)))
    res = []
    for sid in sids:
        sid_new = sid.replace("-","")
        date_ = str(datetime.strptime(data_dict["date"].split("T")[0], '%Y-%m-%d')).split()[0]
        y,m,d = date_.split("-")
        key = "%s_%s_%s"%(sid_new, m, y)
        temp_res =  mongo_methods.read_collection_rname(db_str_mongo, key, date_, rname)
        res+=temp_res
    final_res = {}
    final_res[date_] = {}
    final_res[date_]["name"] = 'Cost'
    total = 0
    cur = ""
    rnames = []
    for val in res:
        rname = val.get("rname", "")
        cost = val.get("cost",0)
        provider = val.get("rprovider", "")
        cur = val.get("curr", "")
        if round(cost, 2)<=0:continue
        if rname not in rnames:
            rnames.append(rname)
        else:
            continue
        total += cost
        if not final_res[date_].get(rname, ""):
            final_res[date_][rname] = round(cost,2)
            final_res[date_]["%s_P" %(rname)] = provider
            final_res[date_]["%s_Curr" %(rname)] = cur
        else:
            new_cost = final_res[date_][rname]+cost
            final_res[date_][rname] = round(new_cost,2)
    final_res[date_]["Total"] = round(total,2)
    final_res[date_]["Total_Curr"] = cur
    return {"tdata":[final_res[date_]], "txkeys":['Cost'], "tykeys":rnames}

if __name__ == '__main__':
    #data_dict = {"cust_name":"Anunta Dev"}
    #print(getDesktopFilters(data_dict))
    data_dict ={
    "rproviders": ["Microsoft.DesktopVirtualization"],
    "hostpools": [
        "4261-MHE-42",
        "4261-MLI-1",
        "4261-MME-41",
        "4261-MNX-2",
        "4261-MQY-40",
        "4261-PCT-36",
        "4261-SHB-5",
        "4261-SPO-43",
        "4261-SQO-44",
        "4261-SYY-4",
        "4278-MLI-1",
        "4278-SCT-36",
        "4278-SPO-43",
        "4279-SYY-4",
        "4286-MLI-1",
        "4286-SYY-4",
        "4289-MME-41",
        "4289-SPO-43",
        "4292-MNX-2",
        "4295-M24-83",
        "4295-MBS-84",
        "4296-MNX-2",
        "4297-MSY-85",
        "4298-MNX-2",
        "4298-MTW-3",
        "4299-MHE-42",
        "4299-MHH-86",
        "4299-MLI-1",
        "4299-MTW-3",
        "4301-MLI-1",
        "4301-MNX-2",
        "4302-MLI-1",
        "4302-MMX-89",
        "4302-MNX-2",
        "4303-MHE-42",
        "4303-MTW-3",
        "4304-MTW-3",
        "4306-MTW-3",
        "4307-SYY-4",
        "4307-MLT-5",
        "4301-MTW-3"
    ],
    "subscriptions": [
        "bb953f35-22e7-431c-a6c3-fa44e577c5bc"
    ],
    "regions": [
        "eastus"
    ],
    "tags": [],
    "date": [
        "2022-11-7T00:00:00.0000000Z",
        "2022-12-14T00:00:00.0000000Z"
    ],
    "cust_id": 1
}
    print (data_dict) 
    #print(TagExplorerCostHistory(data_dict))
