import sys, time
import copy
from datetime import datetime, timedelta
#sys.path.insert(0, '/home/azureuser/dev_icco_api/')
#sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo, db_str_mongo_old
import itertools
import pandas as pd
from bson import ObjectId
import db_mgmt.dbApi_mongodb as dbApi_mongodb
import db_mgmt.dbApi as dbApi
import db_mgmt.mongo_methods as mongo_methods
import apis.table_paginate as table_paginate

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

def getHostPoolsLoginSummary(data_dict):
    db_str = db_str_mongo
    print ("db_str", db_str)
    dates = data_dict["date"]
    cust_id = data_dict["cust_id"]
    regions = data_dict["regions"]
    subscriptions = data_dict["subscriptions"]
    hostpools = data_dict["hostpools"]
    selected_filters = data_dict["filter"]
    #dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    #date_str_list = get_all_dates2(dates[0], dates[1])
    date_str_list, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    #print ("date_str_list", db_str_mongo_old)
    #sub_idxs = dbApi.get_cust_sub_ids(db_str_mysql, cust_id)
    subscriptions = [val.lower() for val in subscriptions]
    user_session_ids = {}
    host_session_ids = {}
    for sub_id in subscriptions: 
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_session_status_timeseries" %(sub_id_new)
        user_session = mongo_methods.read_user_time_series( db_str_mongo_old, collection_name, {"date": {"$in": date_str_list}} )
        user_session_ids.update(user_session)
        collection_name1 = "%s_session_host_status_timeseries" %(sub_id_new)
        host_session = mongo_methods.read_hoststatususer_time_series( db_str_mongo_old, collection_name1, {"date": {"$in": date_str_list}} )
        host_session_ids.update(host_session)

    hostpool_id_dict = mongo_methods.get_hostpool_ids(db_str_mongo_old, "hostpool_mgmt", hostpools, regions, subscriptions, selected_filters)
    #user_session_id_dict = mongo_methods.get_session_ids(db_str_mongo_old, "session_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    user_session_id_dict = mongo_methods.get_session_ids_on_hostpool_name(db_str_mongo_old, "session_mgmt", list(hostpool_id_dict.values()), "session_id")
    #host_session_id_dict = mongo_methods.get_session_ids(db_str_mongo_old, "session_host_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    host_session_id_dict = mongo_methods.get_session_ids_on_hostpool_name(db_str_mongo_old, "session_host_mgmt", list(hostpool_id_dict.values()), "session_host_id")
    user_int_sess_ids = set(user_session_ids.keys()).intersection(set(user_session_id_dict.keys()))
    host_int_sess_ids = set(host_session_ids.keys()).intersection(set(host_session_id_dict.keys()))

    date_wise_dict = {}
    table_dict = {}

    for uid in user_int_sess_ids:
        dates = user_session_ids[uid]  
        hostpool_name = user_session_id_dict[uid]   
        #hostpool_name = hostpool_id_dict[hostpool_id].lower()
        for date, hh, state in dates:
            #print (" \t\t KKK", date, hh, state)  
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
        hostpool_name = host_session_id_dict[uid]   
        #hostpool_name = hostpool_id_dict[hostpool_id].lower()
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
 
    #print ("table_dict", table_dict)
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
    subscriptions = [val.lower() for val in subscriptions]
    hostpools = data_dict["hostpools"]
    selected_filters = data_dict["filter"]
    #print ("dates: ", dates)
    #dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    #date_str_list = [dates[0].strftime("%d-%m-%Y")]#get_all_dates(dates[0], dates[1])
    #dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    #date_str_list = get_all_dates2(dates[0], dates[1])
    date_str_list, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    #sub_idxs = dbApi.get_cust_sub_ids(db_str_mysql, cust_id)
    user_session_ids = {}
    host_session_ids = {}
    for sub_id in subscriptions: 
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_session_status_timeseries" %(sub_id_new)
        user_session = mongo_methods.read_user_time_series( db_str_mongo_old, collection_name, {"date": {"$in": date_str_list}} )
        print ("user_session: ", user_session) 
        user_session_ids.update(user_session)
        collection_name1 = "%s_session_host_status_timeseries" %(sub_id_new)
        host_session = mongo_methods.read_hoststatususer_time_series( db_str_mongo_old, collection_name1, {"date": {"$in": date_str_list}} )
        host_session_ids.update(host_session)

    #hostpool_id_dict = mongo_methods.get_hostpool_ids(db_str_mongo_old, "hostpool_mgmt", [e.upper() for e in hostpools], regions, subscriptions, selected_filters)
    hostpool_id_dict = mongo_methods.get_hostpool_ids(db_str_mongo_old, "hostpool_mgmt", hostpools, regions, subscriptions, selected_filters)
    #user_session_id_dict = mongo_methods.get_session_ids(db_str_mongo_old, "session_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    #host_session_id_dict = mongo_methods.get_session_ids(db_str_mongo_old, "session_host_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    user_session_id_dict = mongo_methods.get_session_ids_on_hostpool_name(db_str_mongo_old, "session_mgmt", list(hostpool_id_dict.values()), "session_id")
    #host_session_id_dict = mongo_methods.get_session_ids(db_str_mongo_old, "session_host_mgmt", {"hostpool_id": {"$in": list(hostpool_id_dict.keys())}})
    host_session_id_dict = mongo_methods.get_session_ids_on_hostpool_name(db_str_mongo_old, "session_host_mgmt", list(hostpool_id_dict.values()), "session_host_id")
    
    user_int_sess_ids = set(user_session_ids.keys()).intersection(set(user_session_id_dict.keys()))
    host_int_sess_ids = set(host_session_ids.keys()).intersection(set(host_session_id_dict.keys()))

    print ("user_int_sess_ids: ", user_int_sess_ids) 
    print ("host_int_sess_ids: ", host_int_sess_ids) 
    
    date_wise_dict = {}
    table_dict = {}
    table_dict2 = {}
    for uid in user_int_sess_ids:
        dates = user_session_ids[uid]  
        hostpool_name = user_session_id_dict[uid]   
        #hostpool_name = hostpool_id_dict[hostpool_id].lower()
        for date, hh, state in dates:
            if state != "Active": continue
            if not table_dict.get(hh, []):
               table_dict[hh] = {}
            if not table_dict[hh].get(hostpool_name, {}):
               table_dict[hh][hostpool_name] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in table_dict[hh][hostpool_name]["Active Sessions"]:
               table_dict[hh][hostpool_name]["Active Sessions"].append(uid)   

            if not date_wise_dict.get(hh, []):
               date_wise_dict[hh] = {"Active Sessions": [], "ON": [], "OFF": []}
            if uid not in date_wise_dict[hh]["Active Sessions"]:
               date_wise_dict[hh]["Active Sessions"].append(uid)


    date_wise_dict2 = {}
    for uid in host_int_sess_ids:
        dates = host_session_ids[uid]  
        hostpool_name = host_session_id_dict[uid]   
        #hostpool_name = hostpool_id_dict[hostpool_id].lower()
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

def getHourlyPeakConcurrency(data_dict):
    hp_list = data_dict.get("hostpools", [])
    sub_list = data_dict.get("subscriptions", [])
    location = data_dict.get("regions", [])
    sub_list = [val.lower() for val in sub_list]
    selected_filters = data_dict["filter"]
    tags = data_dict.get("tags", [])
    #date_list = [datetime.strptime(d.split("T")[0], '%Y-%m-%d').strftime("%d-%m-%Y") for d in data_dict["date"]]
    date_list, all_ui_dates, all_months_years = get_all_dates(data_dict.get('date', ['', '']))
    hp_idxs = mongo_methods.get_hostpool_mgmt_data(db_str_mongo_old, [e.upper() for e in hp_list], sub_list, location)  
    #print ("hp_idxs: ", hp_idxs)
    session_idxs = mongo_methods.get_all_session_idxs(db_str_mongo_old, list(hp_idxs.keys()), hp_idxs)
    #print ("session_idxs: ", session_idxs)
    session_dict = {}
    for sub_id in sub_list:
        sub_id_new = sub_id.replace("-", "")
        collection_name = "%s_session_status_timeseries"%sub_id_new
        temp_dict, count_dict = mongo_methods.get_usersession_timeseries_data(db_str_mongo_old, date_list, collection_name, session_idxs)
        session_dict.update(temp_dict)

    final_res = {}
    txkeys = ['0:00', '1:00', '2:00', '3:00', '4:00', '5:00', '6:00', '7:00', '8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00']
    unique_keys = []
    active_hp_list = list(set([k[2] for k,v in count_dict.items()]))
    print ("count_dict: ", count_dict) 
    print ("session_dict: ", session_dict) 
    print ("active_hp_list: ", active_hp_list) 
    for date_str in date_list:
        final_res[date_str] = {}
        for hour in txkeys:
            for hp in hp_list:
                hp = hp.upper()
                if hp not in active_hp_list:continue
                key = (date_str, hour, hp)
                print ("\t KEY: ", key, count_dict.get(key))
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

def get_zero_hostpool_logins(dates, session_ids, hp_list):
    #date_str_list = get_all_dates_new(dates[0], dates[1])
    date_str_list, all_ui_dates, all_months_years = get_all_dates(dates[0], dates[1])
    session_vals = list(session_ids.values())
    sub_idxs = list(set([x[0] for x in session_vals]))
    session_idxs = list(session_ids.keys())
    active_dict = {}
    for sub_id  in sub_idxs:
        sub_id_new = sub_id.replace("-","")
        collection_name = "%s_session_status_timeseries"%sub_id_new
        active_session_dict, active_hp_list = mongo_methods.get_all_active_session(db_str_mongo, collection_name, session_ids)
    disconnected_sessions = []
    for sid in session_idxs:
        active_dates = active_session_dict.get(sid, [])
        dates_diff = set(date_str_list).difference(set(active_dates))
        if len(date_str_list) == len(dates_diff):
            disconnected_sessions.append(sid)
    zero_login_hps = []
    for hp in hp_list:
        if hp not in list(active_hp_list.keys()):
            zero_login_hps.append(hp)
            continue
        active_hp = active_hp_list.get(hp,[])
        session_diff = set(active_hp).difference(set(disconnected_sessions))
        if session_diff == 0:
            zero_login_hps.append(hp)
    return zero_login_hps

def get_date_range():
    today = datetime.today()
    first_range = (str(today - timedelta(days = 8)).split()[0], str(today-timedelta(days = 1)).split()[0])
    second_range = (str(today - timedelta(days = 16)).split()[0],str(today - timedelta(days = 9)).split()[0])
    third_range = (str(today - timedelta(days = 24)).split()[0], str(today - timedelta(days = 17)).split()[0])
    fourth_range = (str(today - timedelta(days = 32)).split()[0],str(today - timedelta(days = 25)).split()[0])
    return [first_range, second_range, third_range, fourth_range]

def getZeroLoginHostpools(data_dict):
    hp_list = [e.upper() for e in data_dict["hostpools"]]
    hp_idx_dict = mongo_methods.get_all_hostpool_idxs(db_str_mongo_old)
    print ("hp_idx_dict: ", hp_idx_dict)
    if hp_list:
        if len(hp_list[0]) != 2:
            hp_list = [(x, str(hp_idx_dict[x]))for x in hp_list]
    else:
        hp_list = [(x, str(hp_idx_dict[x]))for x in hp_list]
    hp_dict = {}
    for val in hp_list:
         hp_dict[ObjectId(val[1])] = val[0]
    session_ids = mongo_methods.get_all_session_ids_sub(db_str_mongo, hp_dict)
    date_list = get_date_range()
    res_list = []
    for date_ in date_list:
        date_obj = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in date_]
        date_new = [d.strftime("%d.%b.%Y") for d in date_obj]
        if session_ids:
            zero_login_hp = get_zero_hostpool_logins(date_obj, session_ids, list(hp_dict.values()))
        else:
            zero_login_hp = list(hp_dict.values())

        temp_dict = {"header":["-".join(date_new)], "bodyVal":zero_login_hp}
        res_list.append(temp_dict)
    return {"ZeroLoginData": res_list}





if __name__ == '__main__':
    data_dict = {"cust_name":"Anunta Dev","sub_id": "bb953f35-22e7-431c-a6c3-fa44e577c5bc","date": "2022-11-16"}
    data_dict = {"hostpools":["4299-mtw-3","4301-mtw-3","4307-gpu-6","4299-mli-1","4261-shb-5","4261-pct-36","4261-mqy-40","4307-nv8-07","4307-mlt-5","4307-syy-4","4261-mnx-2","4301-mnx-2","4301-mli-1","4298-mtw-3","4261-spo-43","4298-mnx-2","4295-mbs-84","4303-mtw-3","4261-mhe-42","4261-mli-1","4306-mtw-3","4261-sqo-44","4261-syy-4","4299-mhh-86","4295-m24-83","4299-mhe-42","4303-mhe-42","4261-mme-41","4307-mne-91","4292-mnx-2","4307-mxm-93"],"subscriptions":["bb953f35-22e7-431c-a6c3-fa44e577c5bc"],"regions":["eastus","southcentralus"],"tags":["Department_@_Anunta Dev","Project_@_ICCO","ms-resource-usage_@_azure-cloud-shell"],"date":["2022-12-18T00:00:00.0000000Z","2022-12-25T00:00:00.0000000Z"],"cust_id":1,"cust_name":"Anunta Dev", "filter": []}  
    #getHostPoolsLoginSummary(data_dict)
    #getHostPoolsHourlyReportWVD(data_dict)
    print (getHourlyPeakConcurrency(data_dict))
    #data_dict = {"hostpools":["4299-mtw-3","4301-mtw-3","4307-gpu-6","4299-mli-1","4261-shb-5","4261-pct-36","4261-mqy-40","4307-nv8-07","4307-mlt-5","4307-syy-4","4261-mnx-2","4301-mnx-2","4301-mli-1","4298-mtw-3","4261-spo-43","4298-mnx-2","4295-mbs-84","4303-mtw-3","4261-mhe-42","4261-mli-1","4306-mtw-3","4261-sqo-44","4261-syy-4","4299-mhh-86","4295-m24-83","4299-mhe-42","4303-mhe-42","4261-mme-41","4307-mne-91","4292-mnx-2","4307-mxm-93"]}
    #getZeroLoginHostpools(data_dict)
