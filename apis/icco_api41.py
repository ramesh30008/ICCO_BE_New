import sys 
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import dbApi_cp


def get_permission_info():
    tdata = {}
    data = []
    users_customers = dbApi_cp.get_user_cust_info(db_str_mysql) #d["user_customers"]
    #print(users_customers)
    for r in users_customers:
        row = {}
        #print(r)
        uid,user_name,customer_name = r
        permissions = []
        pid = dbApi_cp.get_permission_by_uid(db_str_mysql,uid) #d["permissions"]
        #print(pid)
        if pid == None:
            permissions.append(["None"])
        elif pid == 0:
            permissions.append(["Azure"])
        elif pid == 1:
            permissions.append(["Partner"])
        elif pid == 2:
            permissions.append(["Azure","Partner"])

        row["data_rows"] = permissions
        row["s1"] = user_name 
        row["s2"] = customer_name

        data.append(row)
        #print(row)
    tdata["tdata"] = data
    return tdata   


def get_all_customers():
    customers = {}
    clients = dbApi_cp.get_clients(db_str_mysql)
    customers["clients"] = clients
    return customers


def get_domains_by_customer(cid):
    tdata = {}
    data = {}
    domains = dbApi_cp.get_domains_by_customer(db_str_mysql,cid)
    for row in domains:
        print(row)
        subscription,domain = row
        if domain in data:
            data[domain].append(subscription)
        else:
            data[domain] = [subscription]
    
    tdata["tdata"] = data 
    return tdata    


def update_permissions(uid,pid):
    dbApi_cp.update_permissions_by_uid(uid,pid)
    return 


def update_domain_subsription():
    pass
    

if __name__ == "__main__":
    d = {
    "user_customers" :[["1","user1","cust1"],["1","user1","cust2"],["2","user2","cust1"]],
    "permissions" : 2
	}

    print(get_permission_info())
    #print(get_all_customers())
    dm = [("s1","d1"),("s1","d2"),("s1","d3"),("s2","d1"),("s2","d2"),("s3","d1"),("s3","d2")]    
    print(get_domains_by_customer(dm))

