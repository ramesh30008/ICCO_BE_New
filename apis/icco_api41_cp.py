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
    print(data)
    result = dbApi_cp.get_users_permissions(db_str_mysql)
    for record in result:
        uid,fname,email,pid = record 
        cust_list = data.get(fname,[])
        perm = permissions.get(pid,["Azure"])
        print(perm)
        rdata = {}
        rdata["data_rows"] = perm 
        rdata["s1"] = fname
        rdata["s2"] = cust_list 
        rdata["s3"] = uid
        rdata["s4"] = pid 
        rdata["s5"] = email
        fdata.append(rdata)
    return {"tdata":fdata}


def get_all_customers():
    customers = {}
    clients = dbApi_cp.get_clients(db_str_mysql)
    clients.sort(key = lambda x: x[1])
    print(clients)
    customers["clients"] = clients
    return customers


def get_domains_by_customer(cid,cname):
    print(cname)
    tdata = []
    data = {}
    domains = dbApi_cp.get_domains_by_customer(db_str_mysql,cid)
    for row in domains:
        print(row)
        subscription,domain = row
        if domain in data:
            data[domain].append([subscription,0])
        else:
            data[domain] = [[subscription,0]]
    print(data)    
    for i in data:
        tdata.append([[i,0],data[i]])
    return {"access_key":0,"customer":cname,"childrens":tdata}


def update_permissions(uid,pid):
    dbApi_cp.update_permissions_by_uid(db_str_mysql,uid,pid)
    return {"status":200}

def update_domain_subscription(uid,user,tdata):
    #uid = data["uid"]
    #user = data["user"]
    #tdata = data["tdata"]
    print(uid,user,tdata)
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
    print(records)
    df = {}
    access = {}
    for record in records:
        customer,domain,subscription,d_flag,s_flag,access_key = record
        access[customer] = access_key
        if customer in df:
            df[customer][domain] = d_flag
        else: 
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
        cur["access_key"] = access[key]
        for k in data[key]:
            cur["childrens"].append([[k,df[key][k]],data[key][k]])
        tdata.append(cur)

    print(tdata)
    return {"tdata":tdata}


def delete_by_user_customer(user,customer):
    dbApi_cp.delete_by_user_customer_in_tb(db_str_mysql,user,customer)
    return {"status":200}


if __name__ == "__main__":
    d = {
    "uid": 8,
    "user": "Raunak.k",
    "data": [
        "drpotomac.onmicrosoft.com",
        [
            "36f0b37a-c0c9-48ad-8582-56646683302b"
        ]
    ]
}
    #update_domain_subscription(d)
    #get_customer_details_by_user(6)
    #delete_by_user_customer("Durgashree","Test") 
    #get_customer_details_by_user(4)
    #get_domains_by_customer(4)
    
    update_domain_subscription()
