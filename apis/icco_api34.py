import sys, time
import copy
import time
import cProfile
from datetime import datetime, timedelta
from bson import ObjectId
sys.path.insert(0, '/var/www/html/icco_dev/icco_api_dev/')
sys.path.append('/var/www/html/icco_dev/icco_api_dev/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_mongodb
import dbApi
import mongo_methods
import itertools
import pandas as pd
import table_paginate

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


def resourcesCostHistory(data_dict):
    #if data_dict.get("cust_id", ""):
    dates = data_dict["date"]
    #dates = [datetime.strptime(d, '%Y-%m-%d') for d in data_dict["date"]]
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    date_str_list = get_all_dates(dates[0], dates[1])
    hp_list = data_dict["hostpools"]
    location_list = data_dict["regions"]
    rprovider_list = data_dict["rproviders"]
    all_months = get_all_months(date_str_list)
    sub_idxs = data_dict["subscriptions"]
    lists = [sub_idxs, all_months]
    products = itertools.product(*lists)
    cols = ["date", "hostpool", "resource_group", "resource_id", "location", "currency", "cost", "rprovider", "rname"]
    all_data = []
    currency_dict = {}
    for (sub_id, month_str) in products:
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_%s"%(sub_id_new, month_str)
        start_time = time.time()
        rgrp_dict = mongo_methods.get_all_hostpool_rgrps(db_str_mongo, sub_id)
        end_time = time.time()
        rid_dict = mongo_methods.get_rids_from_rgrp(db_str_mongo, rgrp_dict)
        data_list, curr_dict = mongo_methods.get_cost_by_rprovider(db_str_mongo, collection_name, date_str_list, rid_dict, rprovider_list)
        all_data+=data_list
        currency_dict.update(curr_dict)
    start_time = time.time()
    df = pd.DataFrame(all_data, columns = cols)
    df1 = df.groupby(['date', "hostpool", "location", "rname"]).agg({'cost':'sum'})
    cost_dict = {}
    print(df1)
    list1 = [date_str_list, hp_list, location_list, list(set(df.rname))]
    key_list = itertools.product(*list1)
    key_list = [k for k in key_list]
    unique_hp = []
    all_ui_dates = []
    for i in df1.index:
        hp_list.append(i[1])
        date_obj = datetime.strptime(i[0], "%Y-%m-%d")
        date_ui = date_obj.strftime("%d-%b")
        if [date_ui, i[0]] not in all_ui_dates:
            all_ui_dates.append([date_ui, i[0]])
        if not cost_dict.get(date_ui,{}):
             cost_dict[date_ui] = {}
        if i in key_list:
            if i[3] not in unique_hp:
                unique_hp.append(i[3])
            cost = df1.loc[i, "cost"]
            if not cost_dict[date_ui].get(i[3], 0):
                cost_dict[date_ui][i[3]] = round(cost,2)
            else:
                new_cost = cost_dict[date_ui][i[3]] + cost
                cost_dict[date_ui][i[3]] = round(new_cost, 2)
    if len(unique_hp)>7:
        tdata, tykeys = getFinalDictCustomer(cost_dict, all_ui_dates, currency_dict)
        gdata, gykeys = logic_80_20(cost_dict)
        gdata_final, hostpool_distinct = getFinalDictCustomer(gdata, all_ui_dates, currency_dict)
        gxkeys = list(cost_dict.keys())
    else:
        tdata, tykeys = getFinalDictCustomer(cost_dict, all_ui_dates, currency_dict)
        gdata_final = tdata
        gxkeys = list(cost_dict.keys())
        gykeys = list(tykeys.keys())

    Tobj =  table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys": list(cost_dict.keys()), "tykeys": ["Total"]+list(tykeys.keys()),"tdata": tdata})
    ntxkeys = ndata_dict["txkeys"]
    ntykeys = ndata_dict["tykeys"]
    ntdata = ndata_dict["tdata"]

    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "gdata": gdata_final, "gxkeys":gxkeys, "gykeys":gykeys, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"]}




def tableClickResources(data_dict):
    rname = data_dict["rname"]
    sids = list(set(mongo_methods.get_subscriptions_by_rname(db_str_mongo, rname)))
    res = []
    print ("sids: ", sids, 'rname: ', rname)
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
    data_dict = {"date":"2022-11-24", "rname":"4295M2483-0_OsDisk_1_864be754be434a20b4da833b6ac1ebcd"}
    print(tableClickResources(data_dict))
