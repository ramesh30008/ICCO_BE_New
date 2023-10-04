def get_permission_info():
    tdata = {}
    fdata = []
    permissions = {0:["Azure"],1:["Partner"],2:["Azure","Partner"]}
    data = dbApi.get_users_customers(db_str_mysql)
    print(data)
    result = dbApi.get_users_permissions(db_str_mysql)
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
