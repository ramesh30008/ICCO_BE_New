from pymongo import MongoClient
import time

def createDbConn(db_str="20.12.46.172#27017#testUser#user@123#icco_test"):
    host, port, uname, pwd, dbname = db_str.split('#')
    hosts = ["192.168.1.6:27017","192.168.1.7:27017","192.168.1.4:27017"]
    client = MongoClient(hosts, username = uname, password = pwd, authSource='admin')
    return client, dbname

def insertdata(db_str, coll, data_dict_list):
    client, db = createDbConn(db_str) 
    x = client[db][coll].insert_many(data_dict_list) 
    client.close()
    return x.inserted_ids

def finddata(db_str, col, query, params={}):
    client, db = createDbConn(db_str) 
    print(db, col, query)
    find_obj = client[db][col].find(query, params)
    data_list = list(find_obj)
    #data_list = [x for x in list(find_obj)]
    client.close()
    return data_list
 
def updatedata(db_str, col, query, new_values):
    client, db = createDbConn(db_str) 
    data_list = [x for x in client[db][col].update_one(query, new_values)]
    client.close()
    return data_list

if __name__ == '__main__':
    db_str="localhost#27017#testUser#user@123#icco_test"
    updatedata(db_str, "customer_filter_data", { "$set": {"domains": 1}})
    pass
