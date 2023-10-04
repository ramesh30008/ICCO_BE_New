import sys, time
import copy
import time
import cProfile
from datetime import datetime, timedelta
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_mongodb
import dbApi
import mongo_methods
import itertools
import pandas as pd
import table_paginate


def getHostpoolFilters(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.read_customer_filter_data(db_str_mongo, cust_name)
    return {"Hostpools":res_dict["hostpools"], "Subscription":res_dict["sub"], "Region": res_dict["regions"], "Tags": res_dict["tags"]}

def get_all_dates(start_date, end_date):
    delta = end_date - start_date
    dates = []
    for i in range(delta.days+1):
        dt1 = start_date + timedelta(days=i)
        dt2 = dt1.strftime("%Y-%m-%d")
        dates.append(dt2)
    #dates = [start_date + timedelta(days=i).strptime("%d-%m-%Y") for i in range(delta.days+1)]
    return dates

def get_all_dates2(start_date, end_date):
    delta = end_date - start_date
    dates = []
    for i in range(delta.days+1):
        dt1 = start_date + timedelta(days=i)
        dt2 = dt1.strftime("%d-%m-%Y")
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

def getFinalDictCustomer(final_dict, all_dates, curr_dict):
    out =[]
    subs_distinct = {}
    dcurr = 'USD'
    for date1,date2 in all_dates:
        v = final_dict.get(date1, {})
        temp_dict = {}
        temp_dict["name"] = date1
        temp_dict["d_date"] = date2
        total = 0
        for hostpool, cost in v.items():
            currency = curr_dict.get(hostpool)
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


def getHostpoolCostBydate_TP_Sort(data_dict):
    #{
    #"key": 1,
    #"currentPage": 2,
    #"rowsCountPerTable": 20
    #}
    key = data_dict["key"]
    sorder = data_dict["sort_order"]
    column_id = data_dict["column_id"]
    Tobj = table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.sortData(key, column_id, sorder)
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]   
    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "key": ndata_dict["key"], "records": ndata_dict["records"]}
 

def getHostpoolCostBydate_TP(data_dict):
    #{
    #"key": 1,
    #"currentPage": 2,
    #"rowsCountPerTable": 20
    #}
    key = data_dict["key"]
    page_no = data_dict["currentPage"]
    no_of_rows = data_dict["rowsCountPerTable"]
    Tobj = table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.getPageData(key, page_no, no_of_rows)
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]   
    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"]}
     

def getHostpoolCostBydate(data_dict):
    #if data_dict.get("cust_id", ""):
    cust_id = data_dict["cust_id"]
    dates = data_dict["date"]
    #dates = [datetime.strptime(d, '%Y-%m-%d') for d in data_dict["date"]]
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list = get_all_dates(dates[0], dates[1])
    hp_list = data_dict["hostpools"]
    location_list = data_dict["regions"]
    all_months = get_all_months(date_str_list)
    sub_idxs = dbApi.get_cust_sub_ids(db_str_mysql, cust_id)
    lists = [sub_idxs, all_months]
    products = itertools.product(*lists)
    cols = ["date", "hostpool", "resource_group", "resource_id", "location", "currency", "cost"]
    all_data = []
    currency_dict = {}
    for (sub_id, month_str) in products:
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_%s"%(sub_id_new, month_str)
        #if collection_name== "bb953f3522e7431ca6c3fa44e577c5bc_12_2022":continue
        start_time = time.time()
        rgrp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sub_id)
        print(db_str_mongo, rgrp_dict)
        end_time = time.time()
        rid_dict = mongo_methods.get_rids_from_rgrp(db_str_mongo, rgrp_dict)
        print(rid_dict)
        data_list, curr_dict = mongo_methods.get_cost_by_date_and_rid(db_str_mongo, collection_name, date_str_list, rid_dict)
        print(data_list)
        all_data+=data_list
        currency_dict.update(curr_dict)
    start_time = time.time()
    df = pd.DataFrame(all_data, columns = cols) 
    df1 = df.groupby(['date', "hostpool", "location"]).agg({'cost':'sum'})
    cost_dict = {}
    hp_list = [hp.lower() for hp in hp_list]
    list1 = [date_str_list, hp_list, location_list]
    key_list = itertools.product(*list1)
    key_list = [k for k in key_list]
    all_ui_dates = []
    hplist = []
    for i in df1.index:
        date_obj = datetime.strptime(i[0], "%Y-%m-%d")
        date_ui = date_obj.strftime("%d-%b")
        if [date_ui, i[0]] not in all_ui_dates:
            all_ui_dates.append([date_ui, i[0]])
        if not cost_dict.get(date_ui,{}):
             cost_dict[date_ui] = {}
        if i in key_list:
            if i[1] not in hplist:
                hplist.append(i[1])
            cost = df1.loc[i, "cost"]
            if not cost_dict[date_ui].get(i[1], 0):
                cost_dict[date_ui][i[1]] = round(cost,2)
            else:
                new_cost = cost_dict[date_ui][i[1]] + cost
                cost_dict[date_ui][i[1]] = round(new_cost, 2)
    #if len(data_dict["hostpools"])>7:
    print(cost_dict)
    if len(hplist)>7: 
        tdata, tykeys = getFinalDictCustomer(cost_dict, all_ui_dates, currency_dict)
        gdata, gykeys = logic_80_20(cost_dict)
        gdata_final, hostpool_distinct = getFinalDictCustomer(gdata, all_ui_dates, currency_dict)
        gxkeys = list(cost_dict.keys())
    else:
        tdata, tykeys = getFinalDictCustomer(cost_dict, all_ui_dates, currency_dict)
        gdata_final = tdata
        gxkeys = list(cost_dict.keys())
        gykeys = list(tykeys.keys())

    Tobj = table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys":list(cost_dict.keys()), "tykeys":["Total"]+list(tykeys.keys()),"tdata": tdata})
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]  
    print(gdata_final)
    hhh 
    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "gdata": gdata_final, "gxkeys":gxkeys, "gykeys":gykeys, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"]}
 
def getCostByDateAndSid(data_dict):
    sid = data_dict["sub_id"]
    sid_new = sid.replace("-","")
    date_ = data_dict["date"]
    print("date out", date_)
    y,m,d = date_.split("-")
    key = "%s_%s_%s"%(sid_new, m, y)
    r_list = mongo_methods.read_sub_rname(db_str_mongo, sid)
    r_list = list(set(r_list))
    res = mongo_methods.read_collection(db_str_mongo, key, date_, r_list)
    final_res = {}
    final_res[date_] = {}
    final_res[date_]["name"] = 'Cost'
    total = 0
    cur = ""
    r_new = []
    for val in res:
        rname = val.get("rname", "")
        cost = val.get("cost",0)
        provider = val.get("rprovider", "")
        cur = val.get("curr", "")
        if round(cost, 2)<=0:continue
        if rname not in r_new:
            r_new.append(rname)
        else:continue
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
    return { "tdata":[final_res[date_]], "txkeys":['Cost'], "tykeys":r_new }


def getCostByDateAndHostpool(data_dict):
    hostpool = data_dict["hostpool"]
    rgrp, sid = mongo_methods.get_all_rgrps_sun_id_by_hostpool(db_str_mongo, hostpool)
    r_list = mongo_methods.get_rid_list_from_rgrp(db_str_mongo, rgrp)
    print(rgrp, sid, r_list)
    sid_new = sid.replace("-","")
    date_ = data_dict["date"]
    y,m,d = date_.split("-")
    key = "%s_%s_%s"%(sid_new, m, y)
    res =  mongo_methods.read_collection_rid(db_str_mongo, key, date_, r_list)
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
    return { "tdata":[final_res[date_]], "txkeys":['Cost'], "tykeys":rnames}

def getHourlyPeakConcurrency(data_dict):
    hp_list = data_dict.get("hostpools", [])
    sub_list = data_dict.get("subscriptions", [])
    location = data_dict.get("regions", [])
    tags = data_dict.get("tags", [])
    date_list = [datetime.strptime(d.split("T")[0], '%Y-%m-%d').strftime("%d-%m-%Y") for d in data_dict["date"]]
    hp_idxs = mongo_methods.get_hostpool_mgmt_data(db_str_mongo, hp_list, sub_list, location)  
    session_idxs = mongo_methods.get_all_session_idxs(db_str_mongo,list(hp_idxs.keys()), hp_idxs)
    session_dict = {}
    for sub_id in sub_list:
        sub_id_new = sub_id.replace("-", "")
        collection_name = "%s_session_status_timeseries"%sub_id_new
        temp_dict, count_dict = mongo_methods.get_usersession_timeseries_data(db_str_mongo, date_list, collection_name, session_idxs)
        session_dict.update(temp_dict)
    final_res = {}
    txkeys = ['0:00', '1:00', '2:00', '3:00', '4:00', '5:00', '6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
    unique_keys = []
    active_hp_list = list(set([k[2] for k,v in count_dict.items()]))
    for date_str in date_list:
        final_res[date_str] = {}
        for hour in txkeys:
            for hp in hp_list:
                if hp not in active_hp_list:continue
                key = (date_str, hour, hp)
                if count_dict.get(key):
                    temp_dict = count_dict[key]
                else:
                    temp_dict = {hp:0, "name":hour, "d_date":date_str}

                if not final_res[date_str].get(hour, []):
                    final_res[date_str][hour] = temp_dict
                else:
                    dict1 = {hp:temp_dict[hp]}
                    final_res[date_str][hour].update(dict1)
    dict1 = list(final_res.values())[0]
    res_dict = list(dict1.values())
    return { "tdata":res_dict, "txkeys":txkeys, "tykeys":active_hp_list}


def getHostPoolsLoginSummary(data_dict):
    db_str = db_str_mongo
    print ("db_str", db_str)
    dates = data_dict["date"]
    cust_id = data_dict["cust_id"]
    regions = data_dict["regions"]
    subscriptions = data_dict["subscriptions"]
    hostpools = data_dict["hostpools"]
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list = get_all_dates2(dates[0], dates[1])
    print ("date_str_list", date_str_list)
    sub_idxs = dbApi.get_cust_sub_ids(db_str_mysql, cust_id)
    print ("sub_idxs: ", sub_idxs)
    user_session_ids = {}
    host_session_ids = {}
    for sub_id in sub_idxs: 
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_session_status_timeseries" %(sub_id_new)
        user_session = mongo_methods.read_user_time_series( db_str, collection_name, {"date": {"$in": date_str_list}} )
        user_session_ids.update(user_session)
        collection_name1 = "%s_session_host_status_timeseries" %(sub_id_new)
        host_session = mongo_methods.read_hoststatususer_time_series( db_str, collection_name1, {"date": {"$in": date_str_list}} )
        host_session_ids.update(host_session)

    hostpool_id_dict = mongo_methods.get_hostpool_ids(db_str, "hostpool_mgmt", hostpools, regions, subscriptions)
    user_session_id_dict = mongo_methods.get_session_ids(db_str, "session_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    host_session_id_dict = mongo_methods.get_session_ids(db_str, "session_host_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    
    user_int_sess_ids = set(user_session_ids.keys()).intersection(set(user_session_id_dict.keys()))
    host_int_sess_ids = set(host_session_ids.keys()).intersection(set(host_session_id_dict.keys()))

    print ("user_int_sess_ids: ", user_session_ids) 
    print ("host_int_sess_ids: ", host_session_ids) 
    
    date_wise_dict = {}
    table_dict = {}

    for uid in user_int_sess_ids:
        dates = user_session_ids[uid]  
        hostpool_id = user_session_id_dict[uid]   
        hostpool_name = hostpool_id_dict[hostpool_id]
        for date, hh, state in dates:
            if state != "Active": continue
            if not date_wise_dict.get(date, []):
               date_wise_dict[date] = {"User Sessions": [], "Available VMs": []}
            if uid not in date_wise_dict[date]["User Sessions"]:
               date_wise_dict[date]["User Sessions"].append(uid)
            if not table_dict.get(date, []):
               table_dict[date] = {}
            if not table_dict[date].get(hostpool_name, {}):
               table_dict[date][hostpool_name] = {"User Sessions": [], "Available VMs": []}
            if uid not in table_dict[date][hostpool_name]["User Sessions"]:
               table_dict[date][hostpool_name]["User Sessions"].append(uid)   


    for uid in host_int_sess_ids:
        dates = host_session_ids[uid]  
        hostpool_id = host_session_id_dict[uid]   
        hostpool_name = hostpool_id_dict[hostpool_id]
        for date, hh, state in dates:
            if state != "Available": continue
            if not date_wise_dict.get(date, []):
               date_wise_dict[date] = {"User Sessions": [], "Available VMs": []}
            if uid not in date_wise_dict[date]["Available VMs"]:
               date_wise_dict[date]["Available VMs"].append(uid)

            if not table_dict.get(date, []):
               table_dict[date] = {}
            if not table_dict[date].get(hostpool_name, {}):
               table_dict[date][hostpool_name] = {"User Sessions": [], "Available VMs": []}
            if uid not in table_dict[date][hostpool_name]["Available VMs"]:
               table_dict[date][hostpool_name]["Available VMs"].append(uid)   
 

    print ("table_dict", table_dict)
    #for k, vs in date_wise_dict.items():
    #    print (" ++++++++++++++ ")
    #    print (k)
    #    print ("user: ", vs["User Sessions"])
    #    print ("vms: ", vs["Available VMs"])
    #    print ("user: ", len(vs["User Sessions"]))
    #    print ("vms: ", len(vs["Available VMs"]))

    tmp1 = convertToUIResponse(date_wise_dict, ["User Sessions", "Available VMs"], date_wise_dict.keys(), table_dict, [["User Sessions", "Available VMs"]], ["T1"], 0)
    return tmp1


def getHostPoolsHourlyReportWVD(data_dict):
    db_str = db_str_mongo
    dates = data_dict["date"]
    cust_id = data_dict["cust_id"]
    regions = data_dict["regions"]
    subscriptions = data_dict["subscriptions"]
    hostpools = data_dict["hostpools"]
    #print ("dates: ", dates)
    #dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    #date_str_list = [dates[0].strftime("%d-%m-%Y")]#get_all_dates(dates[0], dates[1])
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list = get_all_dates2(dates[0], dates[1])
    #print ("date_str_list", date_str_list)
    sub_idxs = dbApi.get_cust_sub_ids(db_str_mysql, cust_id)
    user_session_ids = {}
    host_session_ids = {}
    for sub_id in sub_idxs: 
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_session_status_timeseries" %(sub_id_new)
        user_session = mongo_methods.read_user_time_series( db_str, collection_name, {"date": {"$in": date_str_list}} )
        user_session_ids.update(user_session)
        collection_name1 = "%s_session_host_status_timeseries" %(sub_id_new)
        host_session = mongo_methods.read_hoststatususer_time_series( db_str, collection_name1, {"date": {"$in": date_str_list}} )
        host_session_ids.update(host_session)

    hostpool_id_dict = mongo_methods.get_hostpool_ids(db_str, "hostpool_mgmt", hostpools, regions, subscriptions)
    user_session_id_dict = mongo_methods.get_session_ids(db_str, "session_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    host_session_id_dict = mongo_methods.get_session_ids(db_str, "session_host_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    
    user_int_sess_ids = set(user_session_ids.keys()).intersection(set(user_session_id_dict.keys()))
    host_int_sess_ids = set(host_session_ids.keys()).intersection(set(host_session_id_dict.keys()))

    #print ("user_int_sess_ids: ", user_int_sess_ids) 
    #print ("host_int_sess_ids: ", host_int_sess_ids) 
    
    date_wise_dict = {}
    table_dict = {}
    table_dict2 = {}
    for uid in user_int_sess_ids:
        dates = user_session_ids[uid]  
        hostpool_id = user_session_id_dict[uid]   
        hostpool_name = hostpool_id_dict[hostpool_id]
        for date, hh, state in dates:
            if state != "Active": continue
            if not date_wise_dict.get(hh, []):
               date_wise_dict[hh] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in date_wise_dict[hh]["Active Sessions"]:
               date_wise_dict[hh]["Active Sessions"].append(uid)

            if not table_dict.get(hh, []):
               table_dict[hh] = {}
            if not table_dict[hh].get(hostpool_name, {}):
               table_dict[hh][hostpool_name] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in table_dict[hh][hostpool_name]["Active Sessions"]:
               table_dict[hh][hostpool_name]["Active Sessions"].append(uid)   


    date_wise_dict2 = {}
    for uid in host_int_sess_ids:
        dates = host_session_ids[uid]  
        hostpool_id = host_session_id_dict[uid]   
        hostpool_name = hostpool_id_dict[hostpool_id]
        for date, hh, state in dates:
            sstate = "OFF"
            if state == "Available":
               sstate = "ON"
            if not date_wise_dict.get(hh, []):
               date_wise_dict[hh] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in date_wise_dict[hh][sstate]:
               date_wise_dict[hh][sstate].append(uid)

            if not date_wise_dict2.get(hh, []):
               date_wise_dict2[hh] = {"Total Available": [], "ON": [], "OFF": []}
            if uid not in date_wise_dict2[hh][sstate]:
               date_wise_dict2[hh][sstate].append(uid)
            if uid not in date_wise_dict2[hh]["Total Available"]:
               date_wise_dict2[hh]["Total Available"].append(uid)

            if not table_dict.get(hh, []):
               table_dict[hh] = {}
            if not table_dict[hh].get(hostpool_name, {}):
               table_dict[hh][hostpool_name] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in table_dict[hh][hostpool_name][sstate]:
               table_dict[hh][hostpool_name][sstate].append(uid)   

            if not table_dict2.get(hh, []):
               table_dict2[hh] = {}
            if not table_dict2[hh].get(hostpool_name, {}):
               table_dict2[hh][hostpool_name] = {"Total Available": [], "ON": [], "OFF": []}
            if uid not in table_dict2[hh][hostpool_name][sstate]:
               table_dict2[hh][hostpool_name][sstate].append(uid)   
            if uid not in table_dict2[hh][hostpool_name]["Total Available"]:
               table_dict2[hh][hostpool_name]["Total Available"].append(uid)   



    for k, vs in date_wise_dict.items():
        on_ids = date_wise_dict[k]["ON"]
        off_ids = date_wise_dict[k]["OFF"]
        new_offs = list(set(off_ids)-set(on_ids))
        date_wise_dict[k]["OFF"] = new_offs[:]
        date_wise_dict2[k]["OFF"] = new_offs[:]

    for hh, ddict in table_dict.items():
        for hsp, ddict2 in ddict.items():
            on_ids = table_dict[hh][hsp]["ON"]
            off_ids = table_dict[hh][hsp]["OFF"]
            new_offs = list(set(off_ids)-set(on_ids))
            table_dict[hh][hsp]["OFF"] = new_offs[:] 


    for hh, ddict in table_dict2.items():
        for hsp, ddict2 in ddict.items():
            on_ids = table_dict[hh][hsp]["ON"]
            off_ids = table_dict[hh][hsp]["OFF"]
            new_offs = list(set(off_ids)-set(on_ids))
            table_dict2[hh][hsp]["OFF"] = new_offs[:] 



    #for k, vs in date_wise_dict.items():
    #    print (" ++++++++++++++ ")
    #    print (k)
    #    print ("active_sessions: ", len(vs["Active Sessions"]))
    #    print ("on: ", len(vs["ON"]))
    #    print ("off: ", len(vs["OFF"]))

    tmp1 = convertToUIResponse(date_wise_dict, ["ON", "OFF", "Active Sessions"], date_wise_dict.keys(), table_dict, [["Active Sessions"], ["ON", "OFF"]], ["T1", "T2"], 1)
    tmp2 = convertToUIResponse(date_wise_dict2, ["ON", "OFF", "Total Available"], date_wise_dict2.keys(), table_dict2, [["Total Available"], ["ON", "OFF"]], ["T1", "T2"],   1)
    return tmp1, tmp2

def convertToUIResponse(data_dict, gykeys, gxkeys, table_dict, all_right_table_cols, table_keys, dtype=0):

    if dtype==0:
       gxkeys = [(datetime.strptime(tx, '%d-%m-%Y'), tx) for tx in gxkeys]
       gxkeys.sort()
       print ("1: ", gxkeys)
       tgxkeys = [gxelm.strftime("%d-%h") for gxelm, o_elm in gxkeys]
    else:
       gxkeys = [(int(tx), tx) for tx in gxkeys]
       gxkeys.sort()
       tgxkeys = ["%s:00" %o_elm for gxelm, o_elm in gxkeys]

    #gykeys.sort()
    tmp_dict = {"gdata": [], "gxkeys": tgxkeys[:], "gykeys": gykeys[:]}

    for gxelm, o_elm in gxkeys:
        if dtype==0:
           data = {"name": gxelm.strftime("%d-%h")}    
        else:
           data = {"name": "%s:00" %o_elm}    
        for gyelm in gykeys: 
            data[gyelm] = len(data_dict[o_elm][gyelm])
        tdict = table_dict.get(o_elm, {})  
        for key, val in tdict.items():
            for ind, right_table_cols in enumerate(all_right_table_cols):
                tmp = []  
                value_flg = 0
                for yelm in right_table_cols:
                    tvalue = val.get(yelm, [])
                    if tvalue:
                       value_flg = 1
                    tmp.append(len(tvalue))
                print ('data', data)
                if not data.get(table_keys[ind], []):
                   data[table_keys[ind]] = []
                if not value_flg: continue 
                data[table_keys[ind]].append([key]+tmp[:])
        print ("DATA: ", data) 
        tmp_dict["gdata"].append(data) 
    return tmp_dict



if __name__ == '__main__':
    data_dict ={
    "cust_id": 1,
    "cust_name": "Anunta Dev",
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
        "4278-spo-43",
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
        "4301-MTW-3",
        "4307-GPU-6",
        "4307-NV8-07",
        "4307-MNE-91",
        "4307-MXM-93"
    ],
    "subscriptions": [
        "bb953f35-22e7-431c-a6c3-fa44e577c5bc"
    ],
    "regions": [
        "eastus"
    ],
    "date": [
        "2022-12-26T00:00:00.0000000Z",
        "2023-01-02T00:00:00.0000000Z"
    ],
    "tags": [],
    "cust_name":"Anunta Dev"
}
    print (getHostpoolFilters(data_dict))
