def get_user_cust_info(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT user_id,user_name,customer_name FROM user_customer_info"
    cur.execute(sql)
    res = cur.fetchall()
    data = []
    for r in res:
        vals = [r[0],r[1],r[2]]
        if vals not in data:
            data.append(vals)

    cur.close()
    conn.close()
    return data

def get_permission_by_uid(dbstring, uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT permission FROM users WHERE id = '%s'"
    cur.execute(sql%uid)
    res = cur.fetchall()
    data = res[0][0]
    cur.close()
    conn.close()
    return data


def get_clients(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_id,customer_name FROM customer_info"
    cur.execute(sql)
    res = cur.fetchall()
    data = [[r[0],r[1]]for r in res]
    cur.close()
    conn.close()
    return data

def get_domains_by_customer(dbstring, customer_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT subscription,customer_domain FROM customer_subscription WHERE customer_id = '%s'"
    cur.execute(sql%customer_id)
    res = cur.fetchall()
    data = [[r[0],r[1]] for r in res]
    cur.close()
    conn.close()
    return data

def update_permissions_by_uid(dbstring,uid,pid):
    conn, cur = get_connection(dbstring)
    sql = "update users set permission = '%s' where id='%s'"
    cur.execute(sql%(pid,uid))
    conn.commit()
    cur.close()
    conn.close()

def fetch_user_customer_info(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT user_id,customer_name,user_name,customer_domain,subscription from user_customer_info"
    cur.execute(sql)
    res = cur.fetchall()
    print(res)
    cur.close()
    conn.close()
    return res


def insert_into_user_customer_info(dbstring,vals):
    conn, cur = get_connection(dbstring)
    sql = """insert into user_customer_info(user_id,customer_name,user_name,customer_domain,subscription) values(%s,"%s","%s","%s","%s") """
    cur.execute(sql%(vals))
    conn.commit()
    cur.close()
    conn.close()
    print("Inserted")
    return


def delete_by_user_customer(dbstring,user,customer):
    conn, cur = get_connection(dbstring)
    sql = "delete from user_customer_info where user_name='%s' and customer_name='%s'"
    cur.execute(sql%(user,customer))
    conn.commit()
    cur.close()
    conn.close()
    print("deleted")
    return

def get_customer_details_by_user_id(dbstring,uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_name,customer_domain,subscription from user_customer_info where user_id='%s'"
    cur.execute(sql%(uid))
    res = cur.fetchall()
    #print(res)
    cur.close()
    conn.close()
    return res


def get_users_customers(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT user_name,customer_name from user_customer_info"
    cur.execute(sql)
    res = cur.fetchall()
    print(res)
    data = {}
    for record in res:
        user,customer = record
        if user in data:
            if customer not in data[user]:
                data[user].append(customer)
        else:
            data[user] = [customer]
    cur.close()
    conn.close()
    return data


def get_users_permissions(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT id,full_name,permission from users"
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    conn.close()
    return res






