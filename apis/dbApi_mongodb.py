from pymongo import MongoClient
#from config import mongo_str, user_name, pwd

def get_connection():
    mongo_str = '20.12.46.172#27017#icco_test'
    user_name = "testUser"
    pwd = "user@123"
    host, port, dbname = mongo_str.split('#')
    client = MongoClient(host, int(port), username = user_name, password = pwd, authSource='admin')
    print("ffffffffffff", client)

    mydatabase = client[dbname]
    print("ddddddddddddddddd", mydatabase)
    return mydatabase

def read_resourceid():
    mydatabase = get_connection()
    mycollection = mydatabase['all_resource_ids_idx']
    resource_ids = mycollection.find()
    dict_res = {}
    for d1 in resource_ids:
        dict_res[d1['rid']] = d1["index"]
    return dict_res

def insert_max_rid_count():
    mydatabase = get_connection()
    rec = { "max_count":0}
    idx = mydatabase["icco_metadata"].insert_one(rec)
    return

def increment_max_rid_count(count):
    mydatabase = get_connection()
    mycol =  mydatabase["icco_metadata"]
    myquery = {"max_count":{'$exists': 1}}
    newvalues = { "$set":{"max_count":count+1}}
    mycol.update_one(myquery, newvalues)
    #mydatabase["icco_metadata"]["max_count"] = count+1
    return

def get_max_rid_count():
    mydatabase = get_connection()
    count = list(mydatabase.icco_metadata.find({"max_count":{'$exists': 1}}))
    if count:
        return count[0]["max_count"]
    else:
        insert_max_rid_count()
        return 0

def insert_resourceid(rid):
    mydatabase = get_connection()
    count = get_max_rid_count()
    print("rrrrrrrrrrrrrrrrrrrr", count)
    rec = { "rid":rid , "index":count+1 }
    idx = mydatabase['all_resource_ids_idx'].insert_one(rec)
    increment_max_rid_count(count)
    return idx

def insert_rids(collection_name, key1, val1, key2, val2):
    mydatabase = get_connection()
    mycol = mydatabase[collection_name]
    data = list(mydatabase.mycol.find({key1:val1, key2:{'$exists': 1}}))
    if not data:
        mycol.insert_one({key1: val1 , key2: val2})
    else:
        myquery = {key1:val1, key2:{'$exists': 1}}
        newvalues = { "$set":{key2: val2}}
        idx = mycol.update_one(myquery, newvalues)
    return

def read_sub_rid():
    mydatabase = get_connection()
    mycollection = mydatabase["subscription_to_resourceid"]
    resource_ids = mycollection.find()
    dict_res = {}
    for d1 in resource_ids:
        dict_res[d1['sid']] = d1["rids"]
    return dict_res

def read_sub_rname(sid):
    mydatabase = get_connection()
    mycollection = mydatabase["subscription_to_resourcename"]
    resource_names = mycollection.find({'sid':sid})
    rnames = []
    for d1 in resource_names:
        rnames +=d1["rname"]
    return rnames


def insert_sub_rname_provider(collection_name, key1, val1, key2, val2, key3, val3):
    mydatabase = get_connection()
    mycol = mydatabase[collection_name]
    data = list(mydatabase.mycol.find({key1:val1, key2:{'$exists': 1}, key3:{'$exists': 1}}))
    if not data:
        mycol.insert_one({key1: val1 , key2: val2, key3: val3})
    else:
        myquery = {key1:val1, key2:{'$exists': 1}, key3: {'$exists': 1}}
        newvalues = { "$set":{key2: val2, key3: val3}}
        idx = mycol.update_one(myquery, newvalues)
    return

def read_keys_3(collection_name, key1, key2, key3):
    mydatabase = get_connection()
    mycollection = mydatabase[collection_name]
    resource_ids = mycollection.find()
    dict_res = {}
    for d1 in resource_ids:
        if not dict_res.get(d1[key1]):
            dict_res[d1[key1]] = [d1[key2], d1[key3]]
        else:
            dict_res[d1[key1]].append([d1[key2], d1[key3]])
    return dict_res

def insert_cost(key, val_list):
    mydatabase = get_connection()
    mycol = mydatabase[key]
    mycol.insert_many(val_list)
    return

def read_collection(collection_name, date_str, rname_list):
    myquery = {"date":date_str, "rname":{'$in': rname_list}}
    mydatabase = get_connection()
    mycollection = mydatabase[collection_name]
    data = mycollection.find(myquery)
    return data
if __name__ == '__main__':
    read_cost()

