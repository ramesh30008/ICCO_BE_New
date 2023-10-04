def update_domain_subscription(uid,user,customer,data):
    dbApi.delete_by_user_customer(db_str_mysql,user,customer)
    #tb_vals = dbApi_cp.fetch_user_customer_info(db_str_mysql)
    for row in data:
        domain,subscriptions = row
        dname,d_flag = domain
        for r in subscriptions:
            subscription,s_flag = r
            vals = (uid,customer,user,dname,subscription,d_flag,s_flag)
            print(vals)
            dbApi.insert_into_user_customer_info(db_str_mysql,vals)

    return {"status":200}


def get_customer_details_by_user(uid):
    data = {}
    records = dbApi.get_customer_details_by_user_id(db_str_mysql,uid)
    print(records)
    df = {}
    for record in records:
        customer,domain,subscription,d_flag,s_flag = record
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
        for k in data[key]:
            cur["childrens"].append([[k,df[key][k]],data[key][k]])
        tdata.append(cur)

    print(tdata)
    return {"tdata":tdata}


def delete_by_user_customer(user,customer):
    dbApi.delete_by_user_customer_in_tb(db_str_mysql,user,customer)
    return {"status":200}


