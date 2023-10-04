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

def filter_data(filter_ip_dict, data_dict, data_key_cat, date_str_list, p_index):
    #data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency", "resource_group", "hostpools", "tags"]
    active_filters = filter_ip_dict.get('filter', [])
    my_filters = []
    filters_options = []
    ykeys = {}
    for cat in active_filters:
        if cat not in ["subscriptions"]:
            my_filters.append(cat)
            filters_options.append(filter_ip_dict[cat])

    results_info = {}  
    for data_key, cost in  data_dict.items():
        if data_key[0] not in date_str_list: continue
        if my_filters and not validateFilters(data_key, data_key_cat, my_filters, filters_options):
            continue
        date_str = data_key[0]
        sub_pkey = data_key[p_index]
        curr = data_key[5]
        tag = data_key[8]
        rp = data_key[3]
        rs = data_key[4] 
        if not results_info.get(tag, []):
           results_info[tag] = {}
        if not results_info[tag].get(rp, {}):
           results_info[tag][rp] = {}
        tmp = {"resource": rs, "account": data_key[2], "region": data_key[1],  "cost": cost, "curr": curr} 
        results_info[tag][rp][rs] = tmp

    return results_info

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

def getFinalDictGraph(results_info):

    data_dict_arr =[]
    gxkeys = []
    gykeys = []
    for tag, vs_dict in results_info.items():
        tag_sum = 0
        tmp_c1 = []
        temp_dict = {"name": tag, "d_date": tag, "opacity":0.7}
        curr = "" 
        for rp, rn_dict in vs_dict.items():
            rp_sum = 0
            tmp_c2 = []
            for rn, cost_dict in rn_dict.items():
                rp_sum += cost_dict["cost"]
                curr = cost_dict["curr"]
            tag_sum += rp_sum

        tag_sum = round(tag_sum, 2)  
        temp_dict[tag] = tag_sum
        temp_dict['%s_Curr' %tag] = curr
        temp_dict['%s_P' %tag] = "NA"
        temp_dict['Total'] = tag_sum
        data_dict_arr.append(copy.deepcopy(temp_dict))
        gxkeys.append(tag)

    return data_dict_arr, gxkeys, gxkeys 

def getFinalDictTable(final_dict, my_ykeys, all_dates, all_ui_dates):
    data_dict_arr =[]
    for i, date1 in enumerate(all_dates):
        date2 = all_ui_dates[i]
        ykey_dict = final_dict.get(date1, {})
        temp_dict = {"name":date2, "d_date": date1, "opacity":0.7}
        total = 0
        currency = "USD"
        cat = 'NA'
        for ykey in my_ykeys:
            cost_tup = ykey_dict.get(ykey, [0, '', 'NA'])
            temp_dict[ykey] = cost_tup[0]
            temp_dict['%s_Curr'%ykey] = cost_tup[1]
            temp_dict['%s_P'%ykey] = cost_tup[2]
            total+=cost_tup[0]
            currency = cost_tup[1]
            cat = cost_tup[2]
        temp_dict["Total"] = round(total, 2)
        temp_dict['Total_Curr'] = currency
        temp_dict['Total_P']  = cat
        data_dict_arr.append(copy.deepcopy(temp_dict))
    return data_dict_arr

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

def TagExplorerCostHistory(data_dict):
    #if data_dict.get("cust_id", ""):
    dates = data_dict["date"]
    #dates = [datetime.strptime(d, '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    #dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    #date_str_list = get_all_dates(dates[0], dates[1])
    xkeys_obj = [datetime.strptime(k, "%Y-%m-%d")for k in date_str_list]
    xkeys = [date_obj.strftime("%d-%b") for date_obj in xkeys_obj]
    hp_list = data_dict["hostpools"]
    location_list = data_dict["regions"]
    rprovider_list = data_dict["rproviders"]
    sub_idxs = data_dict["subscriptions"]

    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency", "resource_group", "hostpools", "tags"]
    cust_data = {}
    tags_info = {}  
    for (sub, month_year) in itertools.product(*[sub_idxs, all_months_years]):
        sub_new = sub.replace("-", "")
        collection_name = "%s_%s"%(sub_new, month_year)
        rg_to_hp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sub)
        tags_info, tag_info2 = mongo_methods.read_tag_mgmt(db_str_mongo, sub)
        temp_dict = mongo_methods.get_hpcost_tag_explorer(db_str_mongo, collection_name, sub, rg_to_hp_dict, tag_info2)
        cust_data.update(temp_dict)

    print ('tags_info: ', tags_info)
    print ('cust_data: ', cust_data)
    results_info = filter_data(data_dict, cust_data, data_key_cat, date_str_list, 7)
    #print ('results_info: ', results_info)
    #LLLL
    result_ar = []
    for tag, vs_dict in results_info.items():
        tag_sum = 0
        tmp_c1 = [] 
        for rp, rn_dict in vs_dict.items():
            rp_sum = 0
            tmp_c2 = [] 
            for rn, cost_dict in rn_dict.items():
                rp_sum += cost_dict["cost"]
                tmp_c2.append(cost_dict)
            rp_temp = {"network": rp, "cost": rp_sum, "children": tmp_c2}  
            tmp_c1.append(rp_temp)
            tag_sum += rp_sum
        tag_tmp = {"tag": tag, "cost": tag_sum, "children": tmp_c1}
        result_ar.append(tag_tmp)

    final_gdata_arr, gxkeys, gykeys = getFinalDictGraph(results_info)
    return {"txkeys": [], "tykeys": [], "tdata": result_ar, "gdata":final_gdata_arr, "gxkeys": gxkeys, "gykeys": gykeys}


def getTagExplorerFilterData(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)
    return {"Subscription": res_dict["sub"], "rproviders":res_dict['resource_provider'] , "Region":res_dict["regions"], "Tags":res_dict["tags"], "Hostpools":res_dict['hostpools'], "hp_type":["pooled", "personal"]}

def customerDesktopUsageDetails(data_dict = {}):
    subs = data_dict.get("subscriptions", [])
    subs = [val.lower() for val in subs]
    all_dates, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    data_key_cat = ['date', "regions", "subscriptions", "rproviders", "resource", "currency" , "resource_group", "hostpools", "desktops"]

    cust_data = {}
    for (sub, month_year) in itertools.product(*[subs, all_months_years]):
        collection_name = "desktop_cost_%s_%s"%(sub, month_year)
        temp_dict = mongo_methods.get_desktop_cost_new(db_str_mongo, collection_name, sub)
        cust_data.update(temp_dict)

    final_dict, all_ykeys = filter_data(data_dict, cust_data, data_key_cat, 4)
    final_gdata_arr, graph_ykeys = get_graph_data(final_dict, all_ykeys, all_dates, all_ui_dates)   
    final_tdata_arr = getFinalDictTable(final_dict, all_ykeys, all_dates, all_ui_dates)

    Tobj =  table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys": all_ui_dates, "tykeys": ["Total"]+all_ykeys, "tdata": final_tdata_arr })
    ## first page data from pagination
    ntykeys = ndata_dict["tykeys"]
    ntdata = ndata_dict["tdata"]
    return {"txkeys":all_ui_dates, "tykeys":ntykeys, "tdata":ntdata, "gdata":final_gdata_arr, "gxkeys":all_ui_dates, "gykeys":graph_ykeys,"key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"] }

if __name__ == '__main__':
    data_dict = {"cust_name":"Anunta Dev","sub_id": "bb953f35-22e7-431c-a6c3-fa44e577c5bc","date": "2022-11-16"}
    data_dict = {"hostpools":["4299-mtw-3","4301-mtw-3","4307-gpu-6","4299-mli-1","4261-shb-5","4261-pct-36","4261-mqy-40","4307-nv8-07","4307-mlt-5","4307-syy-4","4261-mnx-2","4301-mnx-2","4301-mli-1","4298-mtw-3","4261-spo-43","4298-mnx-2","4295-mbs-84","4303-mtw-3","4261-mhe-42","4261-mli-1","4306-mtw-3","4261-sqo-44","4261-syy-4","4299-mhh-86","4295-m24-83","4299-mhe-42","4303-mhe-42","4261-mme-41","4307-mne-91","4292-mnx-2","4307-mxm-93"],"subscriptions":["bb953f35-22e7-431c-a6c3-fa44e577c5bc"],"regions":["eastus","southcentralus"],"tags":["Department_@_Anunta Dev","Project_@_ICCO","ms-resource-usage_@_azure-cloud-shell"],"date":["2022-12-22T00:00:00.0000000Z","2022-12-28T00:00:00.0000000Z"],"cust_id":1,"cust_name":"Anunta Dev","rproviders":["microsoft.network","microsoft.compute","microsoft.storage","microsoft.aad"],"desktops":["Personal","Pooled"],"filter":[]}
    TagExplorerCostHistory(data_dict)
