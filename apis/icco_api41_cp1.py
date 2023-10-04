import sys 
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_cp


def get_permission_info():
    tdata = {}
    fdata = []
    permissions = {0:["Azure"],1:["Partner"],2:["Azure","Partner"]}
    data = dbApi_cp.get_users_customers(db_str_mysql)
    #print(data)
    result = dbApi_cp.get_users_permissions(db_str_mysql)
    #print(result)
    for record in result:
        uid,fname,pid = record
        cust_list = data.get(fname,[])
        #print(cust_list)
        perm = permissions.get(pid,["Azure"])
        #print(perm)
        rdata = {}
        rdata["data_rows"] = perm 
        rdata["s1"] = fname
        rdata["s2"] = cust_list 
        rdata["s3"] = uid
        rdata["s4"] = pid 
        fdata.append(rdata)
    #print(tdata)
    print(fdata) 
    return {"tdata":fdata}


def get_all_customers():
    customers = {}
    clients = dbApi_cp.get_clients(db_str_mysql)
    customers["clients"] = clients
    return customers


def get_domains_by_customer(uid,cid,cname):
    tdata = []
    data = {}
    domains = dbApi_cp.get_domains_by_customer(db_str_mysql,cid)
    for row in domains:
        print(row)
        subscription,domain = row
        if domain in data:
            data[domain].append(subscription)
        else:
            data[domain] = [subscription]
    print(data)    
    for i in data:
        tdata.append([i,data[i]])
    return {"tdata":tdata}

def update_permissions(uid,pid):
    dbApi_cp.update_permissions_by_uid(db_str_mysql,uid,pid)
    return {"status":200}


def update_domain_subscription(data):
    uid = data["uid"]
    user = data["user"]
    tdata = data["tdata"]
    for row in tdata:
        customer = row["customer"]
        access_key = row["access_key"]
        ds_data = row["childrens"]
        dbApi_cp.delete_by_user_customer(db_str_mysql,user,customer)
        for r1 in ds_data:
            domain,subscriptions = r1
            dname,d_flag = domain 
            for r2 in subscriptions:
                subscription,s_flag = r2
                vals = (uid,customer,user,dname,subscription,d_flag,s_flag,access_key)
                #print(vals)
                dbApi_cp.insert_into_user_customer_info(db_str_mysql,vals)

    return {"status":200}


def get_customer_details_by_user(uid):
    data = {}
    records = dbApi_cp.get_customer_details_by_user_id(db_str_mysql,uid)
    #print(records)
    df = {}
    for record in records:
        customer,domain,subscription,d_flag,s_flag = record 
        if customer!="Test":continue
        df[customer] = {domain:d_flag}
        if customer in data:
            if domain in data[customer]:
                data[customer][domain].append([subscription,s_flag])
            else:
                data[customer][domain] = [[subscription,s_flag]]
        else:
            data[customer] = {domain:[[subscription,s_flag]]}
    print(data)
    tdata = []
    for key in data:
        cur = {}
        cur["customer"] = key
        cur["childrens"] = []
        for k in data[key]:
            cur["childrens"].append([[k,df[key][k]],data[key][k]])
        tdata.append(cur)
    print(tdata)
    return {"tdata":tdata}


def get_password_hash():
    dbApi_cp.get_passwordHash(db_str_mysql)
   

if __name__ == "__main__":
    d = {
    "user_customers" :[["1","user1","cust1"],["1","user1","cust2"],["2","user2","cust1"]],
    "permissions" : 2
	}

    #print(get_permission_info())
    #print(get_all_customers())
    dm = [("s1","d1"),("s1","d2"),("s1","d3"),("s2","d1"),("s2","d2"),("s3","d1"),("s3","d2")]    
    #print(get_domains_by_customer(dm))
    data = [["Domain1","subscription1"]]
    #print(update_domain_subscription(2,"Harsha A.C","TATA",data))
    #get_customer_details_by_user(3)
    #get_domains_by_customer(14)
    #get_permission_info()
    d = {
    "uid": 6,
    "user": "Durgashree",
    "customer": "Test",
    "data": [[["D1",1],[["S1",1],["S2",0]]]]
    } 
    #print(d["uid"],d["user"],d["customer"],d["data"])   
    #update_domain_subscription(d["uid"],d["user"],d["customer"],d["data"])
    #get_customer_details_by_user(6)
    data = { "uid": 4, "user": "Raunak Kumar", "tdata": [ { "access_key": 0, "childrens": [ [ [ "None", 1 ], [ [ "555d9f6a-7414-4df4-a94d-c7a6d6ded077", 1 ] ] ] ], "customer": "ABSLI - AVD" }, { "access_key": 0, "childrens": [ [ [ "desktopreadymsp24.onmicrosoft.com", 1 ], [ [ "8ad07713-103c-44e7-86d9-ecb7ef6a691c", 1 ] ] ], [ [ "desktopreadymsp35.onmicrosoft.com", 1 ], [ [ "bfc31e8c-532b-4a57-bd13-f0cb50ed19a7", 1 ] ] ], [ [ "devopstest05.onmicrosoft.com", 1 ], [ [ "18264fc3-461b-45c3-8604-21b6775d54e7", 1 ] ] ], [ [ "Techpreview02.onmicrosoft.com", 1 ], [ [ "5c125a70-5341-4052-b182-4f6b426feabc", 1 ] ] ] ], "customer": "PDM/COE/Field_TESTING" }, { "access_key": 0, "childrens": [ [ [ "devopstest09.onmicrosoft.com", 1 ], [ [ "0d355f37-d287-4560-b854-4151c2be3e6a", 1 ] ] ] ], "customer": "ABMF" }, { "access_key": 0, "childrens": [ [ [ "drtrail13.onmicrosoft.com", 1 ], [ [ "a9ec9af6-5e8d-4034-aefd-e9d4faaabe18", 1 ] ] ] ], "customer": "DRDevopsTest2" } ] }
    #update_domain_subscription(data)
    print(get_password_hash())


    
