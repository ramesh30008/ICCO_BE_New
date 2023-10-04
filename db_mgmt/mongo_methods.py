import mongo_dbapi
import time
from datetime import datetime
from pymongo import MongoClient
import grainite_methods
def read_subs_cost(dbstring, collection_name, date_str_list, subidx):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date": {"$in": date_str_list}})
    res_dict = {}
    for data_dict in data_dict_list:
        key1 = (data_dict['rprovider'], data_dict['rname'])
        res_dict[key1] = {"cost": data_dict['cost'], "curr": data_dict['curr'], "sub": subidx, "region": data_dict["location"]}
    return res_dict

def read_tag_mgmt(dbstring, subscription):
    data_dict_list = mongo_dbapi.finddata(dbstring, "tags_mgmt", {"sub": subscription})
    res_dict = {}
    res_dict2 = {}
    for data_dict in data_dict_list:
        rp, rn = (data_dict['rprovider'], data_dict['rname'])
        tags = data_dict['tags']
        res_dict2[(rp, rn)] = tags[:]
        for tag in tags:
            if not res_dict.get(tag, []):
               res_dict[tag] = []
            res_dict[tag].append([rp, rn])    
    return res_dict, res_dict2


def read_sub_hostpool(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        key1 = (data_dict['hostpool_name'], data_dict['resource_group'])
        res_dict[key1] = data_dict['_id']
    return res_dict

def insert_hostpool_mgmt(dbstring, res_list, sub_id):
    sub_dict = read_sub_hostpool(dbstring, sub_id)
    final_list = []
    new_data_index_list = []
    for i, data_dict in enumerate(res_list):
        key1 = (data_dict['hostpool_name'], data_dict['resource_group'])
        _id = sub_dict.get(key1, "")
        if not _id: 
            final_list.append(data_dict)
            new_data_index_list.append(i) 
        else:
            data_dict["_id"] = _id
    if final_list:
        ids = mongo_dbapi.insertdata(dbstring, "hostpool_mgmt", final_list)
        for i, each in enumerate(final_list):
            res_list[new_data_index_list[i]]['_id'] = ids[i] 
    return res_list


def getSessionHostForSubscription(dbstring, sub_id, rg_to_hp_dict):
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_host_mgmt",{"subscription_id": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        session_host_id = data_dict["session_host_id"] 
        rg_name = session_host_id.split("/")[4].lower()
        if not rg_to_hp_dict.get(rg_name, ""): continue 
        (hostpool_name, location) = rg_to_hp_dict[rg_name]  
        key = (data_dict["subscription_id"], rg_name, hostpool_name, location) 
        res_dict[data_dict["_id"]] = key
    return res_dict


def read_sub_session_host(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_host_mgmt",{"subscription_id": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        key1 = (data_dict['session_host_name'], data_dict['resource_id'])
        res_dict[key1] = data_dict["_id"]
    return res_dict

def insert_session_host_mgmt(dbstring, res_list, sub_id):
    sub_dict = read_sub_session_host(dbstring, sub_id)
    final_list = []
    new_data_index_list = []
    for i, data_dict in enumerate(res_list):
        key1 = (data_dict['session_host_name'], data_dict['resource_id'])
        _id = sub_dict.get(key1, "")
        if not _id:  
            final_list.append(data_dict)
            new_data_index_list.append(i)   
        else:
            data_dict['_id'] = _id
    if final_list:
        ids = mongo_dbapi.insertdata(dbstring, "session_host_mgmt", final_list)
        for i, each in enumerate(final_list):
            res_list[new_data_index_list[i]]['_id'] = ids[i]
    return res_list

def get_sub_hostpool_data(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        res_dict[data_dict['_id']] = data_dict
    return res_dict

def read_usersession_desktop_name(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_mgmt",{"subscription_id": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        deskname = data_dict.get('desktop_name', "")
        if not deskname: continue
        if not res_dict.get(deskname, []):
           res_dict[deskname] = [] 
        res_dict[deskname].append(data_dict["ad_username"])
    return res_dict



def read_sub_usersession(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_mgmt",{"subscription_id": sub_id })
    res_dict = {}
    for data_dict in data_dict_list:
        key1 = data_dict['session_id']
        res_dict[key1] = data_dict["_id"]
    return res_dict

def insert_session_mgmt(dbstring, res_list, sub_id):
    sub_dict = read_sub_usersession(dbstring, sub_id)
    final_list = []
    new_data_index_list = []
    for i, data_dict in enumerate(res_list):
        key1 = data_dict['session_id']
        _id = sub_dict.get(key1, "")
        if not _id:
            final_list.append(data_dict)
            new_data_index_list.append(i)
        else:
            data_dict['_id'] = _id
    if final_list:
        ids = mongo_dbapi.insertdata(dbstring, "session_mgmt", final_list)
        for i, each in enumerate(final_list):
            res_list[new_data_index_list[i]]['_id'] = ids[i]
    return res_list

def insert_session_status_timeseries(dbstring, res_list, sub_id):
    final_list = []
    for data_dict in res_list:
       session_id = data_dict["_id"]
       session_state = data_dict["session_state"]
       today = datetime.now()
       hour = today.hour
       q,r = divmod(today.minute,5)
       minute = q*5 
       date_ = datetime.now().strftime('%d-%m-%Y')
       res_dict = {"session_id":session_id, "date":date_, "hour":hour, "minute":minute, "session_state":session_state}
       final_list.append(res_dict)
    sub_id = sub_id.replace("-","")
    collection_name = "%s_session_status_timeseries"%sub_id
    if final_list:
        ids = mongo_dbapi.insertdata(dbstring, collection_name, final_list)
    return 

def insert_session_host_status_timeseries(dbstring, res_list, sub_id):
    final_list = []
    for data_dict in res_list:
       session_host_id = data_dict["_id"]
       session_host_state = data_dict["session_host_status"]
       today = datetime.now()
       hour = today.hour
       q,r = divmod(today.minute,5)
       minute = q*5
       date_ = datetime.now().strftime('%d-%m-%Y')
       res_dict = {"session_host_id": session_host_id, "date":date_, "hour":hour, "minute":minute, "session_host_state": session_host_state}
       final_list.append(res_dict)
    sub_id = sub_id.replace("-","")
    collection_name = "%s_session_host_status_timeseries"%sub_id
    if final_list:
        ids = mongo_dbapi.insertdata(dbstring, collection_name, final_list)
    return


def get_all_distinct_hostpool_filters(dbstring, sub_id_list):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": {'$in': sub_id_list}})
    hp_list = []
    rg_list  = []
    tag_list = []
    for data_dict in data_dict_list:
        if data_dict['hostpool_name'] not in hp_list:
            hp_list.append(data_dict['hostpool_name'])
        if data_dict['location'] not in rg_list:
            rg_list.append(data_dict["location"])
        if data_dict['tags']:
            tag_list+=data_dict['tags']
    if tag_list:
        tag_list = list(set(tag_list))
    return hp_list, rg_list, tag_list


def get_all_distinct_hostpool_filters(dbstring, sub_id_list):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": {'$in': sub_id_list}})
    hp_list = []
    rg_list  = []
    tag_list = []
    for data_dict in data_dict_list:
        if data_dict['hostpool_name'] not in hp_list:
            hp_list.append(data_dict['hostpool_name'])
        if data_dict['location'] not in rg_list:
            rg_list.append(data_dict["location"])
        if data_dict['tags']:
            tag_list+=data_dict['tags']
    if tag_list:
        tag_list = list(set(tag_list))
    return hp_list, rg_list, tag_list



def get_all_distinct_hostpool_filters(dbstring, sub_id_list):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": {'$in': sub_id_list}})
    hp_list = []
    rg_list  = []
    tag_list = []
    for data_dict in data_dict_list:
        if data_dict['hostpool_name'] not in hp_list:
            hp_list.append(data_dict['hostpool_name'])
        if data_dict['location'] not in rg_list:
            rg_list.append(data_dict["location"])
        if data_dict['tags']:
            tag_list+=data_dict['tags']
    if tag_list:
        tag_list = list(set(tag_list))
    return hp_list, rg_list, tag_list

def get_all_hostpool_rgrps(dbstring, sub_id):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": sub_id }, {'resource_group': 1, 'hostpool_name': 1, 'location': 1})
    res_dict = {}
    for data_dict in data_dict_list:
        res_dict[data_dict['resource_group']] = [data_dict['hostpool_name'], data_dict['location']]
    return res_dict

def get_rids_from_rgrp(dbstring, rgrp_dict):
    rgrp_list = list(rgrp_dict.keys())
    data_dict_list = mongo_dbapi.finddata(dbstring, "resourcegroup_to_resourceid",{"rgrp": {'$in': rgrp_list}})
    rids = {}
    for data_dict in data_dict_list:
        rg = data_dict['rgrp']
        for rid in data_dict["rid"]:
            rids[rid] = (rg, rgrp_dict[rg][0], rgrp_dict[rg][1])
    return rids

"""def get_cost_by_date_and_rid(dbstring, collection_name, date_str_list, rid_dict):
    hp_curr_dict = {}
    rid_list = list(rid_dict.keys())
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name,{"date": {'$in': date_str_list}, "rid": {'$in': rid_list}})
    data_list = []
    for data_dict in data_dict_list:
        hostpool_name = rid_dict[data_dict["rid"]][1]
        location = rid_dict[data_dict["rid"]][2]
        rg = rid_dict[data_dict["rid"]][0]
        hp_curr_dict[hostpool_name] = data_dict["curr"]
        data_list.append([data_dict["date"], hostpool_name, rg, data_dict["rid"], location, data_dict["curr"], data_dict["cost"]])
    return data_list, hp_curr_dict"""

def get_cost_by_date_and_rid(dbstring, collection_name, date_str_list, rid_dict):
    hp_curr_dict = {}
    rid_list = list(rid_dict.keys())
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name,{"date": {'$in': date_str_list}, "rid": {'$in': rid_list}})
    data_list = []
    duplicte_list = []
    for data_dict in data_dict_list:
        hostpool_name = rid_dict[data_dict["rid"]][1]
        location = rid_dict[data_dict["rid"]][2]
        rg = rid_dict[data_dict["rid"]][0]
        hp_curr_dict[hostpool_name] = data_dict["curr"]
        duplicate_key = (data_dict["date"], data_dict['rname'])
        if duplicate_key in duplicte_list:continue
        duplicte_list.append(duplicate_key)
        #if [data_dict["date"], hostpool_name, rg, data_dict["rid"], location, data_dict["curr"], data_dict["cost"]] not in data_list:
        data_list.append([data_dict["date"], hostpool_name, rg, data_dict["rid"], location, data_dict["curr"], data_dict["cost"]])
    return data_list, hp_curr_dict

def get_all_rgrps_sun_id_by_hostpool(dbstring, hname):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"hostpool_name": hname })
    if data_dict_list:
        rg = data_dict_list[0]['resource_group']
        subscription = data_dict_list[0]['subscription']
        return rg, subscription
    return "", ""

def get_rid_list_from_rgrp(dbstring, rgrp):
    data_dict_list = mongo_dbapi.finddata(dbstring, "resourcegroup_to_resourceid",{"rgrp": rgrp})
    r_dict = {}
    for data_dict in data_dict_list:
        rids = data_dict['rid']
        for rid in rids:
            r_dict[rid] = 1
    return list(r_dict.keys())

def read_collection(dbstring, collection_name, date_str, rname_list):
    myquery = {"date":date_str, "rname":{'$in': rname_list}}
    #print(dbstring, collection_name, myquery)
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, myquery)
    return data_dict_list

def read_collection_rid(dbstring, collection_name, date_str, rname_list):
    myquery = {"date":date_str, "rid":{'$in': rname_list}}
    #print(dbstring, collection_name, myquery)
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, myquery)
    return data_dict_list


def read_sub_rname(dbstring, sid):
    data_dict_list = mongo_dbapi.finddata(dbstring, "subscription_to_resourcename", {'sid':sid})
    rnames = []
    for d1 in data_dict_list:
        rnames +=d1["rname"]
    return rnames

def get_hostpool_mgmt_data(dbstring, hp_list, sub_list, location):
    query = {"$and":[{"hostpool_name":{"$in":hp_list}}, {"subscription":{"$in":sub_list}}, {"location":{"$in":location}}]}
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt", query)
    hp_idxs = {}
    for data_dict in data_dict_list:
        hp_idxs[data_dict["_id"]] = data_dict["hostpool_name"]
    return hp_idxs

def get_all_session_idxs(dbstring, hp_idxs_list, hp_dict):
    query = {"hostpool_id":{"$in":hp_idxs_list}}
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_mgmt", query)
    session_idxs = {}
    for data_dict in data_dict_list:
        hname =  hp_dict.get(data_dict["hostpool_id"], [])
        session_idxs[data_dict["_id"]] = hname
    return session_idxs

def getTimeSeriesForSessionId(dbstring, date_list, collection_name, session_att_dict):
    query = {"date":{"$in":date_list}}
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        if not session_att_dict.get(data_dict["session_host_id"]): continue 
        dkey = session_att_dict[data_dict["session_host_id"]]
        #key = (data_dict["subscription_id"], rg_name, hostpool_name, location) 
        nkey = (data_dict["session_host_id"], dkey[0], dkey[1], dkey[2], dkey[3], data_dict["date"],  data_dict["hour"], "HP_%s_%s" %(dkey[2],  data_dict["hour"]))
        status = 0
        if data_dict["session_host_state"].lower() == "available":
           status = 1  
        if status:
           res_dict[nkey] = status
        elif (not res_dict.get(nkey, "")):
           res_dict[nkey] = status
    return res_dict



def get_usersession_timeseries_data(dbstring, date_list, collection_name, session_dict):
    session_idxs = list(session_dict.keys())
    query = {"date":{"$in":date_list}, "session_id":{"$in":session_idxs}, "session_state":"Active"}
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, query)
    session_idxs = {}
    count_dict = {}
    for data_dict in data_dict_list:
        session_idxs[data_dict["_id"]] = [data_dict["date"], data_dict["hour"], session_dict.get(data_dict["session_id"], "")]
        hour = "%s:00"%data_dict["hour"]
        if not count_dict.get((data_dict["date"], hour,session_dict.get(data_dict["session_id"], ""))):
            count_dict[(data_dict["date"], hour,session_dict.get(data_dict["session_id"], ""))] = {session_dict.get(data_dict["session_id"], ""):1, "name":hour, "d_date":data_dict["date"]}
        else:
            count_dict[(data_dict["date"], hour,session_dict.get(data_dict["session_id"], ""))][session_dict.get(data_dict["session_id"], "")]+=1
    return session_idxs, count_dict


def read_user_time_series(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        ddate = data_dict['date'] 
        sess_id = data_dict['session_id']
        if not res_dict.get(sess_id, []):
           res_dict[sess_id] = []
        val = (data_dict['date'], data_dict['hour'], data_dict["session_state"], data_dict['minute']) 
        if val not in res_dict[sess_id]:
           res_dict[sess_id].append(val)
    return res_dict

def read_user_time_series1(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        ddate = data_dict['date']
        sess_id = data_dict['session_id']
        if not res_dict.get(sess_id, []):
           res_dict[sess_id] = []
        val = (data_dict['date'], data_dict['hour'], data_dict['minute'],  data_dict["session_state"])
        if val not in res_dict[sess_id]:
           res_dict[sess_id].append(val)
    return res_dict

def read_hoststatususer_time_series(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query) 
    res_dict = {}
    for data_dict in data_dict_list:
        h_sess_id = data_dict['session_host_id']
        if not res_dict.get(h_sess_id, []):
           res_dict[h_sess_id] = []
        val = (data_dict['date'], data_dict['hour'], data_dict["session_host_state"], data_dict['minute']) 
        if val not in res_dict[h_sess_id]:
           res_dict[h_sess_id].append(val)
    return res_dict


def get_hostpool_ids(db_str, collection_name, hostpools, regions, subscriptions, filters):
    query = {}
    if filters: 
       if "hostpools" in filters:
          query["hostpool_name"] = {"$in": hostpools}
       if "regions" in filters:
          query["location"] = {"$in": regions}  
       #if "tags" in regions:
       if "subscriptions" in filters:
          query["subscription"] = {"$in": subscriptions}  
    else:
       if hostpools:
          query["hostpool_name"] = {"$in": hostpools}
       if regions:
          query["location"] = {"$in": regions}  
       #if "tags" in regions:
       if subscriptions:
          query["subscription"] = {"$in": subscriptions}  

    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for each in data_dict_list:
        res_dict[each["_id"]] = each["hostpool_name"]
    return res_dict

def get_session_ids(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for each in data_dict_list:
        res_dict[each["_id"]] = each["hostpool_id"]
    return res_dict

def get_session_ids_on_hostpool_name(db_str, collection_name, host_pool_names, colname):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, {})
    res_dict = {}
    for each in data_dict_list:
        session_id = each[colname]
        if session_id.split("/")[8].lower() not in host_pool_names: continue 
        res_dict[each["_id"]] = session_id.split("/")[8].lower()
    return res_dict




def get_cost_by_rprovider(dbstring, collection_name, date_str_list, rid_dict, rprovider_list):
    hp_curr_dict = {}
    rid_list = list(rid_dict.keys())
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name,{"date": {'$in': date_str_list}, "rid": {'$in': rid_list},"rprovider": {'$in': rprovider_list}})
    data_list = []
    for data_dict in data_dict_list:
        hostpool_name = rid_dict[data_dict["rid"]][1]
        location = rid_dict[data_dict["rid"]][2]
        rg = rid_dict[data_dict["rid"]][0]
        hp_curr_dict[hostpool_name] = data_dict["curr"]
        if [data_dict["date"], hostpool_name, rg, data_dict["rid"], location, data_dict["curr"], data_dict["cost"],data_dict["rprovider"], data_dict["rname"]] not in data_list:
            data_list.append([data_dict["date"], hostpool_name, rg, data_dict["rid"], location, data_dict["curr"], data_dict["cost"], data_dict["rprovider"],data_dict["rname"]])
    return data_list, hp_curr_dict

def get_distinct_rproviders(dbstring, sub_list):
    query = {"subscriptionid":{"$in":sub_list}}
    data_dict_list = mongo_dbapi.finddata(dbstring, "subid_rname_provider", query)
    unique_rprovider = []
    for data_dict in data_dict_list:
        if data_dict["resourceprovider"] not in  unique_rprovider:
             unique_rprovider.append(data_dict["resourceprovider"])
    return unique_rprovider

def get_all_session_ids_sub(dbstring, hp_dict):
    hp_idxs_list  = list(hp_dict.keys())
    query = {"hostpool_id":{"$in":hp_idxs_list}}
    data_dict_list = mongo_dbapi.finddata(dbstring, "session_mgmt", query)
    session_idxs = {}
    for data_dict in data_dict_list:
        if not session_idxs.get(data_dict["_id"],[]):
            hp_name = hp_dict[data_dict["hostpool_id"]]
            session_idxs[data_dict["_id"]] = [data_dict["subscription_id"], hp_name]
        else:
            session_idxs[data_dict["_id"]].append([data_dict["subscription_id"], hp_name])
    return session_idxs

def get_all_active_session(dbstring, collection_name, session_dict):
    session_idxs = list(session_dict.keys())
    myquery = {"session_id":{'$in': session_idxs}, "session_state" : "Active"}
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, myquery)
    res_dict = {}
    active_hp_dict = {}
    for data_dict in data_dict_list:
        hp_name = session_dict[data_dict["session_id"]][1]
        if not active_hp_dict.get(hp_name, []):
            active_hp_dict[hp_name] = [data_dict["session_id"]]
        else:
            active_hp_dict[hp_name].append(data_dict["session_id"])
        if not res_dict.get(data_dict["session_id"],[]):
            res_dict[data_dict["session_id"]] = [data_dict["date"]]
        else:
            res_dict[data_dict["session_id"]].append(data_dict["date"])
    return res_dict, active_hp_dict

def get_all_hostpool_idxs(dbstring):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{})
    res_dict = {}
    for data_dict in data_dict_list:
        key1 = data_dict['hostpool_name']
        res_dict[key1] = data_dict['_id']
    return res_dict

def get_all_rgroups(dbstring, sub_list):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt",{"subscription": {'$in': sub_list}})
    res_dict = {}
    for data_dict in data_dict_list:
        res_dict[data_dict["resource_group"]] = data_dict["hostpool_name"]
    return res_dict


def get_cost_per_tag(dbstring, sub_list):
    data_dict_list = mongo_dbapi.finddata(dbstring, "desktop_cost", {"sub": {'$in': sub_list}})
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["hostpool_name"], data_dict["rprovider"],data_dict["location"], data_dict["desktop_name"],data_dict["hostpool_type"])
        if not res_dict.get(key, 0):
            res_dict[key] = data_dict["cost"]
        else:
            res_dict[key]+=data_dict["cost"]
    return res_dict




def get_subscriptions_by_rname(dbstring, rname):
    data_dict_list = mongo_dbapi.finddata(dbstring, "subscription_to_resourcename", {'rname':rname})
    sub_ids = []
    for d1 in data_dict_list:
        sub_ids.append(d1["sid"])
    return sub_ids

def read_collection_rname(dbstring, collection_name, date_str, rname_list):
    myquery = {"date":date_str, "rname":rname_list}
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, myquery)
    return data_dict_list

def mongo_update(dbstring):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt", {})
    for data_dict in data_dict_list:
        query = { 'resource_group': data_dict["resource_group"] }
        new_values = { "$set": { 'resource_group':  data_dict["resource_group"].lower()} }
        mongo_dbapi.updatedata(dbstring, "hostpool_mgmt", query, new_values)
    return

def read_customer_filter_data(dbstring, cust_name, cl_name = 'customer_filter_data'):
    myquery = {"cust":cust_name}
    data_dict_list = mongo_dbapi.finddata(dbstring, cl_name, myquery)
    return data_dict_list[0]

def get_cost(dbstring, collection_name, sub):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    #print(data_dict_list)
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["location"], sub)
        if not res_dict.get(key, 0):
            res_dict[key] = data_dict["cost"]
        else:
            res_dict[key]+=data_dict["cost"]
    return res_dict

def get_cost_new(dbstring, collection_name, sub):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'])
        if not res_dict.get(key, 0):
            res_dict[key] = data_dict["cost"]
        else:
            res_dict[key] += data_dict["cost"]
    return res_dict

def get_rgcost_new(dbstring, collection_name, sub, rg_to_hp_dict):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get('rg', ('', ''))[0]
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_desktop_cost_new2(dbstring, collection_name, sub, desktop_to_users):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    #print ("desktop_to_users: ", desktop_to_users)
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = data_dict['hostpool_name']
        hp_type = data_dict['hostpool_type']
        #print ("desktop_name: ", data_dict['desktop_name'])
        if not desktop_to_users.get(data_dict['desktop_name'], ""): continue   
        username_list = desktop_to_users[data_dict['desktop_name']]
        for username in username_list:
            key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict.get('curr', 'USD'), rg, hp_name, hp_type, data_dict['desktop_name'], username)
            res_dict[key] = data_dict["cost"]
    return res_dict



def get_desktop_cost_new(dbstring, collection_name, sub):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = data_dict['hostpool_name']
        hp_type = data_dict['hostpool_type']
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['desktop_name'], data_dict.get('curr', 'USD'), rg, hp_name, hp_type)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_hpcost_new(dbstring, collection_name, sub, rg_to_hp_dict):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get(rg, ('', ''))[0]
        if not hp_name:continue
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_hpcost_tag_explorer(dbstring, collection_name, sub, rg_to_hp_dict, tag_info2):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get(rg, ('', ''))[0]
        if not hp_name:continue
        key2 = (data_dict['rprovider'], data_dict['rname'])
        tags = tag_info2.get(key2, [])
        if not tags: continue
        for tag in tags: 
            key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name, tag)
            res_dict[key] = data_dict["cost"]
    return res_dict




def get_cost_date(dbstring, collection_name, date_str,sub):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date":date_str})
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'])
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_rgcost_date(dbstring, collection_name, date_str, sub, rg_to_hp_dict, res_grp):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date":date_str, "resource_group":res_grp})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get(rg, ('', ''))[0]
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_resCost_date(dbstring, collection_name, date_str, sub, rg_to_hp_dict, res_grp):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date":date_str, "rname":res_grp})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get(rg, ('', ''))[0]
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_hpcost_date(dbstring, collection_name, date_str, sub, rg_to_hp_dict, hp_clicked):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date":date_str})
    res_dict = {}
    for data_dict in data_dict_list:
        rg = data_dict['resource_group']
        hp_name = rg_to_hp_dict.get(rg, ('', ''))[0]
        if hp_clicked != hp_name:continue 
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'], rg, hp_name)
        res_dict[key] = data_dict["cost"]
    return res_dict

def get_distinct_session_ids(db_str):
    data_dict_list = mongo_dbapi.finddata(db_str, "session_mgmt", {"subscription_id":"555d9f6a-7414-4df4-a94d-c7a6d6ded077"})
    res_dict = {}
    for each in data_dict_list:
        res_dict[each["_id"]] = each["user_principle_name"]
    return res_dict

def read_session_mgmt(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        user_name = data_dict['user_principle_name']
        session_id = data_dict['session_id']
        idx = data_dict['_id']
        if not res_dict.get(idx, []):
            res_dict[idx] = user_name
    return res_dict

def get_hostpool_names(db_str, collection_name, query):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        hp_name = data_dict['hostpool_name']
        location = data_dict['location']
        idx = data_dict['_id']
        if not res_dict.get(idx, []):
            res_dict[idx] = [hp_name,location]
    return res_dict

def get_hp_from_session_mgmt(db_str, collection_name, query, hp_dict):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict = {}
    for data_dict in data_dict_list:
        hp_name, location = hp_dict.get(data_dict['hostpool_id'])
        idx = data_dict['_id']
        if not res_dict.get(idx, []):
            res_dict[idx] = [hp_name, location]
    return res_dict

def read_session_timeseries(db_str, collection_name, query, sess_hp_dict):
    data_dict_list = mongo_dbapi.finddata(db_str, collection_name, query)
    res_dict1 = {}
    for data_dict in data_dict_list:
        hp_name, location = sess_hp_dict.get(data_dict['session_id'])
        key1 = (hp_name, data_dict['date'], data_dict['hour'], data_dict['minute'])
        idx = data_dict['_id']
        if not res_dict1.get(key1, []):
            res_dict1[key1] = 1
        else:
            res_dict1[key1] += 1

    return res_dict1

def get_all_cost(dbstring, collection_name, sub, date_list):
    payload = {"sub_id":sub, "date_list": date_list}
    if sub == "afb3f2d0-f6fc-4391-b9db-bf2cde678ccf":
        data_dict_list = grainite_methods.get_cost_by_sub(payload)
    else:
        data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'])
        c = data_dict.get("cost", 0)
        c_p = data_dict.get("cost_p", 0)
        if not res_dict.get(key, 0):
            res_dict[key] = [[c, c_p]]
        else:
            cost = res_dict[key][0][0]+ c
            cost_p = res_dict[key][0][1]+ c_p
            res_dict[key] = [[cost, cost_p]]
    return res_dict

def get_cost_by_date(dbstring, collection_name, date_str,sub):
    data_dict_list = mongo_dbapi.finddata(dbstring, collection_name, {"date":date_str})
    res_dict = {}
    for data_dict in data_dict_list:
        key = (data_dict["date"], data_dict["location"], sub, data_dict['rprovider'], data_dict['rname'], data_dict['curr'])
        c_p = data_dict.get("cost_p", 0)
        if not res_dict.get(key, []):
            res_dict[key] = [[data_dict["cost"], c_p]]
        else:
            cost = res_dict[key][0][0] + data_dict["cost"]
            cost_p = res_dict[key][0][1] + c_p
            res_dict[key] = [[cost, cost_p]]
    return res_dict
def get_hostpool_regions(dbstring, subs):
    data_dict_list = mongo_dbapi.finddata(dbstring, "hostpool_mgmt", {"subscription" : {"$in": subs}})
    loc_list = []
    for data_dict in data_dict_list:
        loc = data_dict.get("location", "")
        if loc:
            loc_list.append(loc)
    return list(set(loc_list))



def get_regions_by_rgroup(dbstring, collection_name):
    data_dict_list = mongo_dbapi.finddata(dbstring,  collection_name, {})
    res_dict = {}
    for data_dict in data_dict_list:
        if not res_dict.get(data_dict["resource_group"], ""):
            res_dict[data_dict["resource_group"]] = [data_dict["location"]]
        else:
            if data_dict["location"] not in res_dict[data_dict["resource_group"]]:
                res_dict[data_dict["resource_group"]].append(data_dict["location"])
    return res_dict

def get_currency(dbstring, collection_name_list):
    data_dict_list = []
    for collection_name in collection_name_list:
        temp_list = mongo_dbapi.finddata(dbstring, collection_name, {})
        data_dict_list += temp_list
    res_dict = {}
    for data_dict in data_dict_list:
        res_dict[data_dict["curr"]] = 1
    return list(res_dict.keys())[0]

if __name__ == '__main__':
    read_session_mgmt("localhost#27017#testUser#user@123#cq_icco_master", "session_mgmt", {"subscription_id":"555d9f6a-7414-4df4-a94d-c7a6d6ded077"})
    pass
 
