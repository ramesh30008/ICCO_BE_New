import sys, time
import copy
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
        all_dates.append(dt2)
        all_ui_dates.append(date_ui)
    return all_dates, all_ui_dates, all_months_years

def validateFilters(data_key, data_key_cat, filters_cat, filters_val):
    for n, cat in enumerate(filters_cat):
        i = data_key_cat.index(cat)
        print ("======>>", data_key[i], filters_val[n])
        if data_key[i] not in filters_val[n]:  
            return False
    return True 

def filter_data(filter_ip_dict, data_dict, data_key_cat, p_index):
    #data_key_cat = ['date', "regions", "subscriptions", "resource providers", "resource", "currency" ]
    #data_key_cat = ['date', "regions", "subscriptions", "rproviders", "currency" , "resource_group", "hostpools", "desktops", "desk_name", "username"]
    active_filters = filter_ip_dict.get('filter', [])
    my_filters = []
    filters_options = []
    ykeys = {}
    ykeys_user = {}
    for cat in active_filters:
        if cat not in ["subscriptions"]:
            my_filters.append(cat)
            filters_options.append(filter_ip_dict[cat])
    print ("filters_options: ", filters_options)
    print ("filters_options: ", data_dict)
    final_dict = {}
    final_dict_user = {}
    for data_key, cost in  data_dict.items():
        print (data_key, cost)
        if my_filters and not validateFilters(data_key, data_key_cat, my_filters, filters_options):
            continue
        date_str = data_key[0]
        sub_pkey = (data_key[9], data_key[8])
        sp_key = data_key[9] 
        curr = data_key[5]

        if not final_dict.get(date_str, {}):
            final_dict[date_str] = {}
        sub_cost_temp  = final_dict.get(date_str, {}).get(sub_pkey, [0, ''])[0]
        sub_cost = round(sub_cost_temp + cost, 2)
        final_dict[date_str][sub_pkey] = [sub_cost, curr, data_key[3]]

        if not final_dict_user.get(date_str, {}):
            final_dict_user[date_str] = {}
        sub_cost_temp  = final_dict_user.get(date_str, {}).get(sp_key, [0, ''])[0]
        sub_cost = round(sub_cost_temp + cost, 2)
        final_dict_user[date_str][sp_key] = [sub_cost, curr, data_key[3]]
        ykeys_user[sp_key] = 1 
        ykeys[sub_pkey] = 1
    return final_dict, list(ykeys.keys()), final_dict_user, list(ykeys_user.keys())

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

def getFinalDictGraph(final_dict, my_ykeys, all_dates, all_ui_dates):
    data_dict_arr =[]
    for i, date1 in enumerate(all_dates):
        date2 = all_ui_dates[i]
        ykey_dict = final_dict.get(date1, {})
        temp_dict = {"name":date2, "d_date": date1, "opacity":0.7}
        total = 0
        for ykey in my_ykeys:
            cost_tup = ykey_dict.get(ykey, [0, '', 'NA'])
            temp_dict[ykey] = cost_tup[0]
            temp_dict['%s_Curr'%ykey] = cost_tup[1]
            temp_dict['%s_P'%ykey] = cost_tup[2]
            total += cost_tup[0]
        temp_dict['Total'] = total
        data_dict_arr.append(copy.deepcopy(temp_dict))
    return data_dict_arr

def getFinalDictTable(final_dict, my_ykeys, all_dates, all_ui_dates, ui_date):
    result_info = {} 
    xkeys_tmp = {}  
    for date_str, vs_dict in final_dict.items():
      date_str = ui_date.get(date_str, "")
      if not date_str: continue  
      for sp_key, vs_tup in vs_dict.items():
        user = sp_key[0] 
        desktop = sp_key[1]
        if not result_info.get(user, {}):
           result_info[user] = {}
        if not result_info[user].get(desktop, {}):
           result_info[user][desktop] = {}
        result_info[user][desktop][date_str] = vs_tup
        xkeys_tmp[date_str] = 1

    xkeys = list(xkeys_tmp.keys())
    xkeys.sort()
    result_ar = []
    for user, vs_dict in result_info.items():
        tag_sum = 0
        tmp_c1 = [] 
        user_cost_dict = {}
        for desktop, date_cost_dict in vs_dict.items():
           tmp = {}
           rp_sum = 0
           for xkey in xkeys:  
               cost_tup = date_cost_dict.get(xkey, (0, ""))
               rp_sum += cost_tup[0]
               tmp[xkey] = cost_tup[0] 
               t1 = user_cost_dict.get(xkey, 0)
               user_cost_dict[xkey] = t1 + cost_tup[0]
           tmp_c1.append({"desktop": desktop, "cost": [tmp[x] for x in xkeys]})
           tag_sum += rp_sum
        tag_tmp = {"user": user, "cost": [user_cost_dict[x] for x in xkeys], "children": tmp_c1}
        result_ar.append(tag_tmp)

    return result_ar, xkeys 

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

def get_graph_data(final_dict, distinct_ykeys, all_dates, all_ui_dates):    
    gdata_dict, graph_ykeys = customerUsageDetails_1(final_dict, all_dates, all_ui_dates)
    final_gdata_arr = getFinalDictGraph(gdata_dict, graph_ykeys, all_dates, all_ui_dates)
    return final_gdata_arr, graph_ykeys
 
def getRgCostByDateAndRg(data_dict):
    sid = data_dict["subscriptions"][0]
    sid_new = sid.replace("-","")
    date_ = data_dict["date"]
    y,m,d = date_.split("-")
    date_obj = datetime.strptime(date_, "%Y-%m-%d")
    date_ui = date_obj.strftime("%d-%b")
    collection_name = "%s_%s_%s"%(sid_new, m, y)
    resource_grp_clicked = data_dict['rgrp']
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency" , "resource_group", "hostpools", "desktops"]
    rg_to_hp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sid)
    cust_data = mongo_methods.get_rgcost_date(db_str_mongo, collection_name, date_, sid, rg_to_hp_dict, resource_grp_clicked)
    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 4)
    final_tdata_arr, all_ykeys = getTableClickData(final_dict, all_ykeys, [date_], [date_ui])
    return { "tdata": final_tdata_arr, "txkeys":['Cost'], "tykeys":all_ykeys }

def getCustomerDesktopFilterData(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)
    return {"Subscription": res_dict["sub"], "rproviders":res_dict['resource_provider'] , "Region":res_dict["regions"], "Tags":res_dict["tags"], "Hostpools":res_dict['hostpools'], "hp_type":["pooled", "personal"]}

def UsersUsageDetails(data_dict = {}):
    subs = data_dict.get("subscriptions", [])
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    print ("all_dates: ", all_dates)
    print ("all_dates: ", all_ui_dates)
    ui_date = {}
    for i, d in enumerate(all_dates):
        ui_date[d] = all_ui_dates[i]
        
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "currency" , "resource_group", "hostpools", "desktops", "desk_name", "username"]
    cust_data = {}
    for (sub, month_year) in itertools.product(*[subs, all_months_years]):
        collection_name = "desktop_cost_new_%s_%s"%(sub, month_year)
        desktop_to_users = mongo_methods.read_usersession_desktop_name(db_str_mongo_old, sub)
        print ("desktop_to_users: ", desktop_to_users, collection_name, db_str_mongo_old)
        temp_dict = mongo_methods.get_desktop_cost_new2(db_str_mongo, collection_name, sub, desktop_to_users)
        print ("desktop_to_users: ", temp_dict)
        cust_data.update(temp_dict)

    final_dict, all_ykeys, final_dict_user, all_ykeys_user = filter_data(data_dict, cust_data, data_key_cat, 4)
    print ("final_dict: ", final_dict)
    final_gdata_arr, graph_ykeys = get_graph_data(final_dict_user, all_ykeys_user, all_dates, all_ui_dates)   
    final_tdata_arr, txkeys = getFinalDictTable(final_dict, all_ykeys, all_dates, all_ui_dates, ui_date)
    #Tobj =  table_paginate.table_paginate('142.93.208.71')
    #ndata_dict = Tobj.storeData({"txkeys": all_ui_dates, "tykeys": ["Total"]+all_ykeys, "tdata": final_tdata_arr })
    ## first page data from pagination
    #ntykeys = ndata_dict["tykeys"]
    #ntdata = ndata_dict["tdata"]
    #return {"txkeys": txkeys, "tykeys": [], "tdata": final_tdata_arr, "gdata":final_gdata_arr, "gxkeys":all_ui_dates, "gykeys":graph_ykeys,"key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"] }
    return { "txkeys": txkeys, "tykeys": [], "tdata": final_tdata_arr, "gdata":final_gdata_arr, "gxkeys":all_ui_dates, "gykeys":graph_ykeys }

if __name__ == '__main__':
    data_dict = {"hostpools":["4303-mtw-3","4301-mtw-3","4261-syy-4","4307-nv8-07","4306-mtw-3","4301-mnx-2","4299-mli-1","4295-m24-83","4307-syy-4","4303-mhe-42","4261-mli-1","4295-mbs-84","4307-gpu-6","4261-mqy-40","4307-mne-91","4298-mtw-3","4307-mxm-93","4307-mlt-5","4261-mme-41","4261-pct-36","4298-mnx-2","4261-mnx-2","4261-sqo-44","4261-shb-5","4261-spo-43","4292-mnx-2","4299-mhh-86","4261-mhe-42","4301-mli-1","4299-mhe-42","4299-mtw-3"],"subscriptions":["bb953f35-22e7-431c-a6c3-fa44e577c5bc"],"regions":["eastus","southcentralus"],"tags":["Department_@_Anunta Dev","Project_@_ICCO","ms-resource-usage_@_azure-cloud-shell"],"date":["2023-1-11T00:00:00.0000000Z","2023-1-12T00:00:00.0000000Z"],"cust_id":1,"cust_name":"Anunta Dev","filter":[]}
    print (UsersUsageDetails(data_dict))
