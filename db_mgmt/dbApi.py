import mysql.connector
import json
#from config import DB_CONNECTION_OTHER
from datetime import date
from datetime import datetime, timedelta

def get_connection(dbstring):
    h_host, u_user, p_passwd, dbname = dbstring.split('#')
    db_connection = mysql.connector.connect(host=h_host,user=u_user,passwd=p_passwd,database=dbname )
    db_cursor = db_connection.cursor()
    return db_connection, db_cursor

def getPCode(DB_CONNECTION_STR, uid):
    conn, cur = get_connection(DB_CONNECTION_STR)
    sql = "select emailCode from users where id=%s" 
    cur.execute(sql %uid)
    res = cur.fetchone()
    cur.close()
    conn.close()
    if res:
       return res[0]
    return ''

def getFullName(DB_CONNECTION_STR, uid):
    conn, cur = get_connection(DB_CONNECTION_STR)
    sql = "select full_name from users where id=%s" 
    cur.execute(sql %uid)
    res = cur.fetchone()
    cur.close()
    conn.close()
    if res:
       return res[0]
    return ''

def get_currency(dbstring, sid):
    conn, cur = get_connection(dbstring)
    sql = ''' SELECT customer_cost.currency FROM customer_cost INNER JOIN customer_subscription  ON  customer_cost.subscription_id = customer_subscription.id where customer_subscription.subscription_id = '%s' '''
    cur.execute(sql%sid)
    res = cur.fetchall()
    cur.close()
    conn.close()
    if res:
        return res[0][0]
    else:
        return ""
def insert_cust_cost_new(dbstring, sub_id, cost, date_, currency):
    conn, cur = get_connection(dbstring)
    try:
        isql = '''INSERT INTO customer_cost(subscription_id, every_day_cost, date, currency) VALUES (%s, %s, '%s', '%s')'''
        res =cur.execute(isql %(sub_id, cost, date_, currency))
        conn.commit()
    except Exception as e:
        cur.close()
        conn.close()
        return {"status":False, "msg":str(e)}
    cur.close()
    conn.close()
    return {"status":True, "msg":"success"}

def update_cust_cost_new(dbstring, cost, date_, subscription_id):
    conn, cur = get_connection(dbstring)
    try:
        isql = '''UPDATE customer_cost SET every_day_cost = %s WHERE date = '%s' AND subscription_id = %s'''
        res =cur.execute(isql %(cost, date_, subscription_id))
        conn.commit()
    except Exception as e:
        cur.close()
        conn.close()
        return {"status":False, "msg":str(e)}
    cur.close()
    conn.close()
    return {"status":True, "msg":"success"}

def get_date_new(dbstring, sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT date FROM customer_cost WHERE subscription_id = %s"
    cur.execute(sql%sub_id)
    res = cur.fetchall()
    data = [val[0] for val in res]
    cur.close()
    conn.close()
    return data

def get_sub_ids(dbstring):
    conn, cur = get_connection(dbstring)
    sql ="SELECT customer_info.customer_name, customer_subscription.id, customer_info.customer_id FROM customer_info INNER JOIN customer_subscription ON customer_info.customer_id = customer_subscription.customer_id;" 
    cur.execute(sql)
    res = cur.fetchall()
    data = {}
    for val in res:
        if not data.get(val[0]):
            data[val[0]] = [[val[1], val[2]]]
        else:
            data[val[0]].append([val[1], val[2]])
    cur.close()
    conn.close()
    return data

def get_distinct_companies(dbstring):
    conn, cur = get_connection(dbstring)
    sql = """SELECT customer_id, customer_name FROM customer_info"""
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    conn.close()
    return res

def get_cust_data_Timerange(dbstring, start_d, end_d, sub_id):
    conn, cur = get_connection(dbstring)
    start_d = start_d.strftime("%Y-%m-%d")
    end_d = end_d.strftime("%Y-%m-%d")
    sql = "SELECT * FROM customer_cost WHERE (date BETWEEN '%s' AND '%s') AND subscription_id  = %s"
    cur.execute(sql %(end_d, start_d, sub_id))
    res = cur.fetchall()
    data = [val for val in res]
    cur.close()
    conn.close()
    return data

def get_cust_data_TimerangeNew(conn, cur, start_d, end_d, sub_id):
    start_d = start_d.strftime("%Y-%m-%d")
    end_d = end_d.strftime("%Y-%m-%d")
    sql = "SELECT * FROM customer_cost WHERE (date BETWEEN '%s' AND '%s') AND subscription_id  = %s"
    cur.execute(sql %(end_d, start_d, sub_id))
    res = cur.fetchall()
    data = [val for val in res]
    return data

def get_cust_sub_ids(dbstring, customer_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT subscription_id FROM customer_subscription WHERE customer_id = %s"
    cur.execute(sql%customer_id)
    res = cur.fetchall()
    data = [val[0] for val in res]
    cur.close()
    conn.close()
    return data

def get_cust_id(dbstring, sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_id, id FROM customer_subscription WHERE subscription_id = '%s'"
    cur.execute(sql % sub_id)
    res = cur.fetchall()
    data = [[val[0], val[1]] for val in res]
    cur.close()
    conn.close()
    return data[0]

def get_subscription_info(dbstring,sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT * FROM customer_subscription WHERE id = %s"
    cur.execute(sql % sub_id)
    res = cur.fetchall()
    columns = ['id', 'customer_id', 'app_id', 'tenantId', 'secret_key', 'subscription_id', 'subscription_name', 'type', 'date', 'status' ]
    data = [dict(zip(columns, val)) for val in res]
    cur.close()
    conn.close()
    return data[0]

def get_all_subscriptions(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT * FROM customer_subscription;"
    cur.execute(sql)
    res = cur.fetchall()
    data = [val for val in res]
    cur.close()
    conn.close()
    return data

def call_proc(DB_CONNECTION_STR, args, procName, out_ind_st, out_ind_en):
    conn, cur = get_connection(DB_CONNECTION_STR)
    results_ar = cur.callproc(procName, args)
    return results_ar[out_ind_st:out_ind_en] 
    select_outs = []
    for ind in range(out_ind_st, out_ind_en):
        select_outs.append('@_%s_%s' %(procName, str(ind))) 
    results = []
    while cur.nextset():
        results.append(cur.fetchall())
    cur.execute('SELECT %s' %','.join(select_outs))
    res = cur.fetchone()
    cur.close()
    conn.close()
    return res

def insertCustomer_Info(dbstring, val_list):
    conn, cur = get_connection(dbstring)
    for val in val_list:
        try:
            isql = '''INSERT INTO customer_info(customer_name, start_date, status ) VALUES ('%s', now(), '%s')'''
            res =cur.execute(isql %tuple(val))
            conn.commit()
        except Exception as e:
            cur.close()
            conn.close()
            return {"status":False, "msg":str(e)}
    cur.close()
    conn.close()
    return {"status":True, "msg":"success"}

def insertCustomer_Subscription(dbstring, val_list):
    conn, cur = get_connection(dbstring)
    for val in val_list:
        try:
            isql = '''INSERT INTO customer_info(customer_id, ) VALUES ('%s', now(), '%s')'''
            res =cur.execute(isql %tuple(val))
            conn.commit()
        except Exception as e:
            cur.close()
            conn.close()
            return {"status":False, "msg":str(e)}
    cur.close()
    conn.close()
    return {"status":True, "msg":"success"}

def get_subscription_idx(dbstring, sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT id FROM customer_subscription WHERE subscription_id = '%s'"
    cur.execute(sql%sub_id)
    res = cur.fetchone()
    data = res[0]
    cur.close()
    conn.close()
    return data

def get_subscription_ids(dbstring, sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT id FROM customer_subscription WHERE subscription_id = '%s'"
    cur.execute(sql%sub_id)
    res = cur.fetchone()
    data = res[0]
    cur.close()
    conn.close()
    return data

def get_cost(dbstring, date, sub_id):
    conn, cur = get_connection(dbstring)
    sql = "SELECT every_day_cost FROM customer_cost WHERE date = '%s' and subscription_id = %s"
    cur.execute(sql%(date,sub_id))
    res = cur.fetchone()
    data = [res[0]]
    cur.close()
    conn.close()
    return data

def update_email_verified(dbstring):
    conn, cur = get_connection(dbstring)
    isql = '''UPDATE users SET emailVerified = 1'''
    res =cur.execute(isql)
    conn.commit()
    cur.close()
    conn.close()
    return {"status":True, "msg":"success"}


def insert_data_cinfo(DB_CONNECTION_STR,c_name):
    conn, cur =get_connection(DB_CONNECTION_STR)
    check_sql = "select customer_id, customer_name from customer_info"
    cur.execute(check_sql)
    output = cur.fetchall()
    out_dict = {value:key for key, value in output}
    if not c_name in list(out_dict.keys()):
        sql = "insert into customer_info(customer_name,start_date,status) values('%s',now(),'active')"
        sql1 = "SELECT customer_id FROM customer_info where customer_name = '%s'"
        cur.execute(sql %(c_name))
        cur.execute(sql1 %(c_name))
        c_id = cur.fetchall()[0][0]
    else:
        c_id = out_dict[c_name]
    conn.commit()
    cur.close()
    conn.close()
    return c_id


def insert_data_csub(DB_CONNECTION_STR,c_name,appid,tenantid,billing_id,partner_tenantid,passw,subid,sub,sub_type):
    conn, cur = get_connection(DB_CONNECTION_STR)
    c_id = insert_data_cinfo(DB_CONNECTION_STR,c_name)
    check_sql = "select customer_id,subscription_id from customer_subscription"
    cur.execute(check_sql)
    output = cur.fetchall()
    if (c_id,subid) in output:
       sql_1 = "update customer_subscription set appId = '%s', tenantId ='%s', billingId ='%s', partner_tenantId ='%s',  secret_key ='%s' where customer_id =%s and subscription_id ='%s'"
       cur.execute(sql_1 %(appid,tenantid,billing_id,partner_tenantid,passw,c_id,subid))
       msg = "For %s appid,tenantid,billing_id,partner_tenantid,password is updated"%(c_name)
    else:
       sql = """insert into customer_subscription(customer_id,appId,tenantId,partner_tenantId,billingId,secret_key,subscription_id,subscription,subscription_type,subscription_start_date,status) values(%s,"%s","%s","%s","%s","%s","%s","%s","%s",now(),"active") """
       cur.execute(sql %(c_id,appid,tenantid,billing_id,partner_tenantid,passw,subid,sub,sub_type))
       msg = "sucess"
    conn.commit()
    cur.close()
    conn.close()
    return msg


def get_users(dbstring):
    conn, cur = get_connection(dbstring)
    sql = "SELECT email FROM users"
    cur.execute(sql)
    res = cur.fetchall()
    data = [r[0]for r in res]
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
    sql = "SELECT user_id FROM user_cust_info WHERE user_id = '%s'"
    cur.execute(sql%uid)
    res = cur.fetchone()
    data = res[0]
    cur.close()
    conn.close()
    return data

def get_domain_dict(dbstring, domains):
    conn, cur = get_connection(dbstring)
    if not domains:
        cur.close()
        conn.close()
        return []
    if len(domains)==1:
        sql = "select subscription_id  FROM customer_subscription where customer_domain = '%s'"
        cur.execute(sql%domains[0])
    else:
        sql = "select subscription_id  FROM customer_subscription where customer_domain in {}"
        cur.execute(sql.format(tuple(domains)))
    res = cur.fetchall()
    data = [r[0] for r in res]
    cur.close()
    conn.close()
    return data

def get_sub_ids_new(dbstring, company_list):
    conn, cur = get_connection(dbstring)
    if len(company_list) == 1:
        sql ="SELECT customer_info.customer_name, customer_subscription.id, customer_info.customer_id FROM customer_info INNER JOIN customer_subscription ON customer_info.customer_id = customer_subscription.customer_id where customer_info.customer_name = '%s' and customer_info.status = 'active'"
        cur.execute(sql%company_list[0])
    elif not company_list:
        sql ="SELECT customer_info.customer_name, customer_subscription.id, customer_info.customer_id FROM customer_info INNER JOIN customer_subscription ON customer_info.customer_id = customer_subscription.customer_id  where customer_info.status = 'active'"
        cur.execute(sql)
    else:
        sql ="SELECT customer_info.customer_name, customer_subscription.id, customer_info.customer_id FROM customer_info INNER JOIN customer_subscription ON customer_info.customer_id = customer_subscription.customer_id where customer_info.customer_name in {} and customer_info.status = 'active'"
        cur.execute(sql.format(tuple(company_list)))


    res = cur.fetchall()
    data = {}
    for val in res:
        if not data.get(val[0]):
            data[val[0]] = [[val[1], val[2]]]
        else:
            data[val[0]].append([val[1], val[2]])
    cur.close()
    conn.close()
    return data

def get_companies(dbstring, uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_name FROM user_customer_info WHERE user_id = %s "
    cur.execute(sql%uid)
    res = cur.fetchall()
    data  = [r[0] for r in res]
    cur.close()
    conn.close()
    return data

def get_permission(dbstring, uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT permission FROM users WHERE id = %s"
    cur.execute(sql%uid)
    res = cur.fetchall()
    cur.close()
    conn.close()
    if not res:
        return 0
    return res[0]

def get_subs_domain(dbstring, uid, cust_name):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_domain, subscription FROM user_customer_info WHERE user_id = %s and customer_name = '%s' and s_flag = 1"
    cur.execute(sql%(uid,cust_name))
    res = cur.fetchall()
    if not res:
        cur.close()
        conn.close()
        return [], []
    domains = [r[0] for r in res]
    subscription = [r[1] for r in res]
    cur.close()
    conn.close()
    return domains, subscription

def get_user_role(dbstring, uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT user_role FROM users WHERE id = %s"
    cur.execute(sql%uid)
    res = cur.fetchall()
    cur.close()
    conn.close()
    if res:
        return res[0]
    else:
        return 'user'

if __name__=='__main__':
   print(get_users("localhost#ai-user#User@123#cq_icco_master_new") )
   pass
