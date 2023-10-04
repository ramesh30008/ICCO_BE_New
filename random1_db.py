def insert_into_user_customer_info(dbstring,vals):
    conn, cur = get_connection(dbstring)
    sql = """insert into user_customer_info(user_id,customer_name,user_name,customer_domain,subscription,d_flag,s_flag) values(%s,"%s","%s","%s","%s",%s,%s) """
    cur.execute(sql%(vals))
    conn.commit()
    cur.close()
    conn.close()
    print("Inserted")
    return


def get_customer_details_by_user_id(dbstring,uid):
    conn, cur = get_connection(dbstring)
    sql = "SELECT customer_name,customer_domain,subscription,d_flag,s_flag from user_customer_info where user_id=%s"
    cur.execute(sql%(uid))
    res = cur.fetchall()
    #print(res)
    cur.close()
    conn.close()
    return res


def delete_by_user_customer_in_tb(dbstring,user,customer):
    conn, cur = get_connection(dbstring)
    sql = "delete from user_customer_info where user_name='%s' and customer_name='%s'"
    cur.execute(sql%(user,customer))
    conn.commit()
    cur.close()
    conn.close()
    print("deleted")
    return

