import sys, time
import copy
from datetime import datetime, timedelta
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_mongodb
import mongo_methods
import itertools
import pandas as pd
import table_paginate
import dbApi
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
        all_dates.append(dt2)
        all_ui_dates.append(date_ui)
    return all_dates, all_ui_dates, all_months_years

def validateFilters(data_key, data_key_cat, filters_cat, filters_val):
    for n, cat in enumerate(filters_cat):
        i = data_key_cat.index(cat)
        if data_key[i] not in filters_val[n]:  
            return False
    return True 

def filter_data(filter_ip_dict, data_dict, data_key_cat, p_index):
    #data_key_cat = ['date', "regions", "subscriptions", "resource providers", "resource", "currency" ]
    active_filters = filter_ip_dict.get('filter', [])
    my_filters = []
    filters_options = []
    ykeys = {}
    for cat in active_filters:
        if cat == "domains":continue
        if cat not in ["subscriptions"]:
            my_filters.append(cat)
            filters_options.append(filter_ip_dict[cat])
    final_dict = {}
    for i, (data_key, cost_list) in enumerate(data_dict.items()):
        cost, cost_p = cost_list[0]
        if my_filters and not validateFilters(data_key, data_key_cat, my_filters, filters_options):
            continue
        date_str = data_key[0]
        sub_pkey = data_key[p_index]
        curr = data_key[5]
        if not final_dict.get(date_str, {}):
            final_dict[date_str] = {}
        sub_cost_temp  = final_dict.get(date_str, {}).get(sub_pkey, [0, 0])[0]
        sub_cost_p_temp  = final_dict.get(date_str, {}).get(sub_pkey, [0, 0])[1]
        #sub_cost = round(sub_cost_temp + cost, 4)
        sub_cost = sub_cost_temp + cost
        sub_cost_p = sub_cost_p_temp + cost_p
        if p_index == 2:
            final_dict[date_str][sub_pkey] = [sub_cost, sub_cost_p, curr, 'Subscription']
        elif p_index == 4:
            final_dict[date_str][sub_pkey] = [sub_cost, sub_cost_p, curr, data_key[3]]
        ykeys[sub_pkey] = 1
    return final_dict, list(ykeys.keys())

def customerUsageDetails_1(data_dict, all_dates, all_ui_dates):
    ykey_cost_dict = {}
    for date_, ykey_dict in data_dict.items():
        for ykey, cost_tup in ykey_dict.items():
            cst_temp = ykey_cost_dict.get(ykey, 0)
            ykey_cost_dict[ykey] = cst_temp+cost_tup[0]
    tup_val = [(v,k)for k,v in ykey_cost_dict.items()]
    tup_val = sorted(tup_val, reverse=True)
    top_7_sub = [k for (v,k) in tup_val[:7]]
    gdata_dict = {}
    for date_, sub_dict in data_dict.items():
        new_sub_dict = {}
        for sub_id, cost_tup in sub_dict.items():
            if sub_id in top_7_sub:
                new_sub_dict[sub_id] = cost_tup
            else:
                cost_o = new_sub_dict.get('Others', (0, '', ''))[0]
                new_sub_dict['Others'] = [cost_o+cost_tup[0], cost_tup[1], cost_tup[2]]
        gdata_dict[date_] = copy.deepcopy(new_sub_dict)
    gykeys = top_7_sub[:]
    if len(tup_val)>7:
        gykeys.append("Others")
    return gdata_dict, gykeys

def getFinalDictGraph(final_dict, my_ykeys, all_dates, all_ui_dates, flag):
    data_dict_arr_a =[]
    data_dict_arr_p =[]
    temp_dict_p = {}
    temp_dict_a = {}
    for i, date1 in enumerate(all_dates):
        date2 = all_ui_dates[i]
        ykey_dict = final_dict.get(date1, {})
        if 1 in flag:
            temp_dict_p = {"name":date2, "d_date": date1, "opacity":0.7}
        if 0 in flag:
            temp_dict_a = {"name":date2, "d_date": date1, "opacity":0.7}
        total = 0
        total_p = 0
        for ykey in my_ykeys:
            cost_tup = ykey_dict.get(ykey, [0,0,'', 'NA'])
            if 1 in flag:
                temp_dict_p[ykey] = cost_tup[1]
                temp_dict_p['%s_Curr'%ykey] = cost_tup[2]
                temp_dict_p['%s_P'%ykey] = cost_tup[3]
                total_p += cost_tup[1]
            if 0 in flag:
                temp_dict_a[ykey] = cost_tup[0]
                temp_dict_a['%s_Curr'%ykey] = cost_tup[2]
                temp_dict_a['%s_P'%ykey] = cost_tup[3]
                total += cost_tup[0]
        if 0 in flag:
            temp_dict_a['Total'] = total     
        if 1 in flag:
            temp_dict_p['Total'] = total_p
        if temp_dict_a:
            data_dict_arr_a.append(copy.deepcopy(temp_dict_a))
        if temp_dict_p:
            data_dict_arr_p.append(copy.deepcopy(temp_dict_p))
    return data_dict_arr_a, data_dict_arr_p

def getFinalDictTable(final_dict, my_ykeys, all_dates, all_ui_dates, flag, subs):
    res_dict = {}
    total_list = []
    total_p_list = []
    curr = "NA"
    for i, date1 in enumerate(all_dates):
        ykey_dict = final_dict.get(date1, {})
        val_data = list(final_dict.values())[0].values()
        _,_,curr, ui_k = list(val_data)[0]
        if not ykey_dict:
            for sid in subs:
                ykey_dict[sid] =[0, 0, curr, ui_k]
        cost_subs = list(ykey_dict.keys())
        if  ykey_dict and len(subs)!= len(cost_subs):
            missed_sub = list(set(subs).difference(set(cost_subs)))
            ykey_dict[missed_sub[0]] = [0, 0, curr, ui_k]
        total = []
        total_p = []
        for sub, [cost, cost_p, curr, col] in ykey_dict.items():
            if 0 in flag and 1 in flag:
                total += [cost]
                total_p += [cost_p]
                if not res_dict.get(sub, ""):
                    res_dict[sub] = {"s1": sub, "data_rows":[[cost],[cost_p]], "data_rows_desc":['A', 'P'], "c":curr}
                else:
                    res_dict[sub]["data_rows"][0] +=[cost]
                    res_dict[sub]["data_rows"][1] +=[cost_p]
            elif 1 in flag:
                total_p += [cost_p]
                if not res_dict.get(sub, ""):
                    res_dict[sub] = {"s1": sub, "data_rows":[[cost_p]], "data_rows_desc":['P'], "c":curr}
                else:
                    res_dict[sub]["data_rows"][0] +=[cost]
            elif 0 in flag:
                total += [cost]
                if not res_dict.get(sub, ""):
                    res_dict[sub] = {"s1": sub, "data_rows":[[cost]], "data_rows_desc":['A'], "c":curr}
                else:
                    res_dict[sub]["data_rows"][0] +=[cost]
        total_list.append(sum(total))
        total_p_list.append(sum(total_p))
        
            
    #add NA if all values are zero
    for sub in list(res_dict.keys()):
        if 0 in flag and 1 in flag:
            all_zero_p = all(v == 0 for v in res_dict[sub]["data_rows"][1])
            if all_zero_p:
                res_dict[sub]["data_rows"][1] = [0 for i in range(len(all_dates))]
            all_zero_a = all(v == 0 for v in res_dict[sub]["data_rows"][0])
            if all_zero_a:
                res_dict[sub]["data_rows"][0] = [0 for i in range(len(all_dates))]
        else:
            all_zero = all(int(v )== 0 for v in res_dict[sub]["data_rows"][0])
            if all_zero:
                res_dict[sub]["data_rows"][0] = [0 for i in range(len(all_dates))]

    all_subs = ['total'] + list(res_dict.keys())
    if 0 in flag and 1 in flag:
        if not total_list:
            total_list = [0 for i in range(len(all_dates))]
        if not total_p_list:
            total_p_list = [0 for i in range(len(all_dates))]
        res_dict["total"] = {"s1": "Total", "data_rows":[total_list, total_p_list], "data_rows_desc":['A', 'P'], "c":curr}
    elif 1 in flag:
        if not total_p_list:
            total_p_list = [0 for i in range(len(all_dates))]
        res_dict["total"] = {"s1": "Total", "data_rows":[total_p_list], "data_rows_desc":['P'], "c":curr}
    elif 0 in flag:
        if not total_list:
            total_list = [0 for i in range(len(all_dates))]
        res_dict["total"] = {"s1": "Total", "data_rows":[total_list], "data_rows_desc":['A'], "c":curr}
    data_dict_arr = [res_dict[k1] for k1 in all_subs]
    return data_dict_arr

def getTableClickData(final_dict, my_ykeys, all_dates, all_ui_dates, flag):
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
            cost_tup = ykey_dict.get(ykey, [0, 0,'', 'NA'])
            
            if flag:
                if round(cost_tup[0], 2)<=0:continue
                temp_dict[ykey] = cost_tup[0]
                total+=cost_tup[0]
            else:
                if round(cost_tup[1], 2)<=0:continue
                temp_dict[ykey] = cost_tup[1]
                total+=cost_tup[1]
            temp_dict['%s_Curr'%ykey] = cost_tup[2]
            temp_dict['%s_P'%ykey] = cost_tup[3]
            currency = cost_tup[2]
            cat = cost_tup[3]
            new_ykeys.append(ykey) 
        temp_dict["Total"] = round(total, 2)
        temp_dict['Total_Curr'] = currency
        temp_dict['Total_P']  = cat
        data_dict_arr.append(copy.deepcopy(temp_dict))
    return data_dict_arr, new_ykeys

def get_graph_data(final_dict, distinct_ykeys, all_dates, all_ui_dates, flag):    
    gdata_dict, graph_ykeys = customerUsageDetails_1(final_dict, all_dates, all_ui_dates)
    final_gdata_arr_a, final_gdata_arr_p = getFinalDictGraph(gdata_dict, distinct_ykeys, all_dates, all_ui_dates, flag)
    return final_gdata_arr_a,final_gdata_arr_p,distinct_ykeys
 
def getCostByDateAndSid(data_dict):
    sid = data_dict["sub_id"]
    sid_new = sid.replace("-","")
    date_ = data_dict["date"]
    ## flag 1 -- Azure Cost, flag 0 -- Partner Cost
    flag = data_dict.get("flag", 1)
    y,m,d = date_.split("-")
    date_obj = datetime.strptime(date_, "%Y-%m-%d")
    date_ui = date_obj.strftime("%d-%b")
    collection_name = "%s_%s_%s"%(sid_new, m, y)
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency" ]
    cust_data = mongo_methods.get_cost_by_date(db_str_mongo, collection_name, date_, sid)
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 4)
    final_tdata_arr, all_ykeys = getTableClickData(final_dict, all_ykeys, [date_], [date_ui], flag)
    return { "tdata": final_tdata_arr, "txkeys":['Cost'], "tykeys":all_ykeys }

def getCustomerFilterData(data_dict):
    cust_name = data_dict["cust_name"]
    uid = data_dict.get("userid", 0)
    domains, subs = dbApi.get_subs_domain(db_str_mysql, uid, cust_name)
    if cust_name == 'Multi Subscription Test':
        collection_name = 'customer_filter_data_new'
        res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name, collection_name)
    else:
        res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)

    if not domains:
        domains = res_dict.get("domains",[])
    if not subs:
        subs = res_dict.get("sub", [])
    domains = list(set(domains))
    subs = list(set(subs))
    return {"Subscription": subs, "rproviders":res_dict.get('resource_provider',[]) , "Region":res_dict.get("regions",[]), "Tags":res_dict.get("tags",[]), "domains":domains}

    
def customerUsageDetails(data_dict = {}):
    filter_subs = data_dict.get("subscriptions", [])
    flag = data_dict.get("flag", [])
    userid = data_dict.get("userid", '')
    domains = data_dict.get("domains", [])
    new_subs = dbApi.get_domain_dict(db_str_mysql, domains)
    if "domains" in data_dict.get("filter", []):
        subs =list(set(filter_subs+new_subs))
    else:
        subs = filter_subs
    if not flag:
        flag = [dbApi.get_permission(db_str_mysql, userid)][0]
        if flag[0] == 2:
            flag = [0,1]
    #write a query to get which type of cost the customer has
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency"]
    cust_data = {}
    for (sub, month_year) in itertools.product(*[subs, all_months_years]):
        sub_new = sub.replace("-", "")
        collection_name = "%s_%s"%(sub_new, month_year)
        temp_dict = mongo_methods.get_all_cost(db_str_mongo, collection_name, sub, all_dates)
        cust_data.update(temp_dict)
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 2)
    all_ykeys = subs
    final_gdata_arr_a,final_gdata_arr_p, graph_ykeys = get_graph_data(final_dict, all_ykeys, all_dates, all_ui_dates, flag)  
     
    final_tdata_arr = getFinalDictTable(final_dict, all_ykeys, all_dates, all_ui_dates, flag, subs)
    #final_tdata_arr = []
    #Tobj =  table_paginate.table_paginate('142.93.208.71')
    #ndata_dict = Tobj.storeData({"txkeys": all_ui_dates, "tykeys": ["Total"]+all_ykeys, "tdata": final_tdata_arr })
    ## first page data from pagination
    ntykeys = ["Total"]+all_ykeys
    print(ntykeys)
    ntdata = final_tdata_arr
    # flag 0 -- Partner Cost, flag 1 -- Azure Cost
    if 0 in flag and 1 in flag:
        txkeys = [ "s1", ["A", "P"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Azure", "Partner"]] + all_ui_dates
    elif 1 in flag:
        txkeys = [ "s1", ["P"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Partner"]] + all_ui_dates
    elif 0 in flag:
        txkeys = [ "s1", ["A"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Azure"]] + all_ui_dates
    return {"txkeys":txkeys,"tx_display_keys":tx_display_keys, "tykeys":ntykeys, "tdata":ntdata, "gdata_a":final_gdata_arr_a, "gdata_p":final_gdata_arr_p, "gxkeys":all_ui_dates, "gykeys":graph_ykeys}
    #return {"txkeys":txkeys,"tx_display_keys":tx_display_keys, "tykeys":ntykeys, "tdata":ntdata, "gdata":final_gdata_arr, "gxkeys":all_ui_dates, "gykeys":graph_ykeys,"key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"] }

def graphclick(data_dict = {}):
    subs = data_dict.get("subscriptions", [])
    flag = data_dict.get("flag", [])
    userid = data_dict.get("userid", '')
    if not userid:
        flag = [0,1]
     
    elif not flag:
        flag = [dbApi.get_permission(db_str_mysql, userid)][0]
        if flag[0] == 2:
            flag = [0,1]
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency"]
    cust_data = {}
    for (sub, month_year) in itertools.product(*[subs, all_months_years]):
        sub_new = sub.replace("-", "")
        collection_name = "%s_%s"%(sub_new, month_year)
        temp_dict = mongo_methods.get_all_cost(db_str_mongo, collection_name, sub, all_dates)
        cust_data.update(temp_dict)
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 2)
    all_ykeys = subs
    final_tdata_arr = getFinalDictTable(final_dict, all_ykeys, all_dates, all_ui_dates, flag, subs)
    tykeys = ["Total"]+all_ykeys
    ntdata = final_tdata_arr
    # flag 0 -- Partner Cost, flag 1 -- Azure Cost
    if 0 in flag and 1 in flag:
        txkeys = [ "s1", ["A", "P"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Azure", "Partner"]] + all_ui_dates
    elif 1 in flag:
        txkeys = [ "s1", ["P"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Partner"]] + all_ui_dates
    elif 0 in flag:
        txkeys = [ "s1", "c", ["A"]]+all_dates
        tx_display_keys =  [ "subscription","currency",  ["Azure"]] + all_ui_dates
    return {"txkeys":txkeys,"tx_display_keys":tx_display_keys, "tykeys":tykeys, "tdata":final_tdata_arr}
if __name__ == '__main__':
    data_dict = {
    "subscriptions": [
        "5b835511-add7-4979-aa42-deb3b0711f30",
        "dr_zenworx_ri_cost",
        "a24d81d4-940f-4503-95d7-46748219b4d8"
    ],
    "regions": [
        " in central",
        "eastus",
        "centralindia"
    ],
    "tags": [],
    "rproviders": [
        "microsoft.aad",
        "microsoft.recoveryservices",
        "microsoft.compute",
        "microsoft.storage",
        "microsoft.capacity",
        "microsoft.network"
    ],
    "date": [
        "2023-3-20T00:00:00.0000000Z",
        "2023-3-25T00:00:00.0000000Z"
    ],
    "filter": [],
    "flag": [],
    "userid": 14,
    "cust_id": 11,
    "domains": [
        "Zenworx.in"
    ]
}
    res = customerUsageDetails(data_dict)
    print(res)
