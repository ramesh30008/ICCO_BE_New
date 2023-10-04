import mysql.connector 
from binascii import a2b_base64
import copy
import sys, re
sys.path.append("../")
import db_mgmt.dbApi as dbApi
import send_mail
import base64
import os
import traceback
import time
#import generatePassword
import shutil
import subprocess, shlex
import uuid
import time
import random
import shelve
import dateutil
import pandas as pd
import itertools
from datetime import date
from datetime import datetime, timedelta
from random import randint
from utils.config import db_str_mysql
from utils.config import shelveFile_sub
from utils.config import shelveFile_all
sys.path.insert(0, '/home/azureuser/dev_icco_api/')
sys.path.append('/home/azureuser/dev_icco_api/db_mgmt')
from utils.config import db_str_mysql, db_str_mongo
import mongo_methods
import table_paginate


from collections import OrderedDict
#db_str_mysql = "localhost#ai-user#sWS6eKC6h4rA22Dv#inforef_table_extraction"
#OPATH = '/var/www/html/iTe/output/'

def insertCustomer():
    val_list = [("Anunta Dev","active"),("Verbinden","active")]
    dbApi.insertCustomer_Info(db_str_mysql, val_list)


def sign_up(data_dict):
    fullname = data_dict.get('fullname', None)
    email = data_dict.get('email', None)
    p_password = data_dict.get('password', None)
    stype = data_dict.get('type', None)
    def_dict = {'p_code': '', 'p_status': 'Input Error', 'uid': ''}
    if ((not fullname) or (not email) or (not p_password)): 
       return def_dict
    args = [fullname, email, p_password, 'p_status', 'p_code', 'p_id']
    ### Call Procedure
    res = dbApi.call_proc(db_str_mysql, args, 'addUser', 3, 6)
    print(res)
    if not res: 
       return def_dict

    def_dict['p_code'] = res[1]
    def_dict['sign_up'] = 1
    def_dict['uid'] = res[2]
    def_dict['p_status'] = res[0]
    def_dict['email'] = email
    def_dict['fullname'] = fullname

    if "duplicate" in res[0].lower() and stype != 'GSignUp':
        def_dict['p_status'] = "Email already exists, Please sign in with this email."
        def_dict['p_code'] = ""
        return def_dict 

    elif "duplicate" in res[0].lower() and stype == 'GSignUp':
        def_dict['p_status'] = 'Success'
        rs = dbApi.getUId_FullNameByEmail(db_str_mysql, email)
        if not rs: return def_dict
        uid, fullname = rs[0], rs[1] 
        def_dict["uid"] = uid
        def_dict['fullname'] = fullname

    if def_dict['p_status'] == 'Success' and stype == 'GSignUp':
       validate_email(def_dict)     
       dbApi.AdminEnableUser(db_str_mysql, def_dict["uid"], 2)

    elif def_dict['p_status'] == 'Success' and stype != 'GSignUp':
       send_mail.send_mail(email, def_dict['p_code'])

    return def_dict

def sign_in(data_dict):
    #time.sleep(5)
    email = data_dict.get('email', None)
    stype = data_dict.get('type', None)
    p_password = data_dict.get('password', None)
    def_dict = {'uid': '', 'p_status': 'Input Error', 'email': ''}
    if ((not email) or (not p_password)): 
       return def_dict
    args = [email, p_password, 'p_userID', 'p_responseMessage']
    res = dbApi.call_proc(db_str_mysql, args, 'userLogin', 2, 4)
    if not res: 
       return def_dict

    def_dict['p_status'] = res[1]
    if not res[0]: 
       return def_dict

    def_dict['uid'] = res[0]
    
    p_code = dbApi.getPCode(db_str_mysql, def_dict['uid'])
    if res[1] == 'Validate Email':
       send_mail.send_mail(email, p_code)

    def_dict['email'] = email
    #def_dict['TotalPages'] = temp_tot
    #def_dict['PagesLeft'] = temp_tot-consumed
    fullname = dbApi.getFullName(db_str_mysql, def_dict['uid']) 
    def_dict['fullname'] = fullname
    return def_dict

def validate_email(data_dict):
    uid = data_dict.get('uid', None)
    p_code = data_dict.get('p_code', None)
    def_dict = {'p_status': 'Input Error', 'fullname': '', 'uid': '', 'p_code': '', 'email': ''}
    if ((not uid) or (not p_code)): 
       return def_dict
    args = [uid, p_code, 'p_responseMessage']
    print ('args: ', args)
    res = dbApi.call_proc(db_str_mysql, args, 'ValidateUser', 1, 3)
    if not res: 
       return def_dict
    fullname = dbApi.getFullName(db_str_mysql, uid) 
    email = dbApi.getEmail(db_str_mysql, uid)

    if res[1] == 'Email Code Timed Out (Check your mail for new code)':
       send_mail.send_mail(email, def_dict['p_code'])
         
    def_dict['p_status'] = res[1]
    def_dict['p_code'] = res[0]
    def_dict['fullname'] = fullname
    def_dict['uid'] = uid
    def_dict['email'] = email
    return def_dict

def resendOTP(uid):
    args = [uid, 'p_code', 'p_responseMessage']
    res = dbApi.call_proc(db_str_mysql, args, 'ResendOTP', 1, 3)
    p_code = res[0]
    email = dbApi.getEmail(db_str_mysql, uid)
    send_mail.send_mail(email, p_code)
    return {'p_code': p_code, "p_responseMessage": "OTP Resent"}

"""def forgotPassword(data_dict):
    email = data_dict['email']
    uid = dbApi.checkEmail(db_str_mysql, email)
    def_dict = {'p_responseMessage': "Email don't exist"}
    if not uid: return def_dict
    new_password = generatePassword.genPass()
    args = [uid, new_password, 'p_responseMessage']
    res2 = dbApi.call_proc(db_str_mysql, args, 'changePassword', 2, 3)
    if not res2:
       def_dict['p_responseMessage'] = "Password updated failed"
       return def_dict
    send_mail.send_mail_for_password(email, new_password)
    def_dict['p_responseMessage'] = "Success, mail sent"
    return def_dict"""

def forgotPassword(data_dict):
    start_time = time.time()
    email = data_dict['email']
    uid = dbApi.checkEmail(db_str_mysql, email)
    full_name = dbApi.checkName(db_str_mysql, email)
    def_dict = {'p_responseMessage': "Email don't exist"}
    if not uid: return def_dict
    myuuid = uuid.uuid4()
    print('Your UUID is: ' + str(myuuid))
    dbApi.insert_uuid(db_str_mysql, uid, str(myuuid))
    send_mail.send_mail_for_password_change(email, myuuid, full_name)
    #print("--- %s seconds ---" % (time.time() - start_time))
    def_dict['p_responseMessage'] = "Success, mail sent"
    def_dict['token'] = myuuid
    return def_dict

def resetPassword(data_dict):
    print("data", data_dict)
    token = data_dict['token']
    res = dbApi.checkToken(db_str_mysql, token)
    if not res:
        def_dict = {'p_responseMessage': "UID not there"}
        def_dict['status'] = False
        return def_dict
    uid = res[0]
    res_dict = validatePassword(data_dict)
    if not res_dict['status']:
        def_dict ={'p_responseMessage':res_dict['p_responseMessage']}
        def_dict['status'] = False
        return def_dict
    """else:
        def_dict ={'p_responseMessage':"Email link sent already!"}
        def_dict['status'] = False
        return def_dict"""
    new_password = data_dict['password']
    args = [uid, new_password, 'p_responseMessage']
    res2 = dbApi.call_proc(db_str_mysql, args, 'changePassword', 2, 3)
    if not res2:
        def_dict = {'p_responseMessage': "Password update failed"}
        def_dict['status'] = False
        return def_dict
    else:
        dbApi.update_status(db_str_mysql, token)
        def_dict={'p_responseMessage' : "Password updated Successfully"}
        def_dict['status'] = True
        return def_dict

def validatePassword(data_dict):
    print("data", data_dict)
    token = data_dict['token']
    res  = dbApi.checkToken(db_str_mysql, token)
    if not res:
        def_dict = {'p_responseMessage': "UID not there"}
        def_dict['status'] = False
        return def_dict
    status = dbApi.checkStatus(db_str_mysql, token)
    email = dbApi.getEmail(db_str_mysql, res[0])
    print("result", res)
    def_dict = {'p_responseMessage': "Invalid Token"}
    if not status:
        def_dict['p_responseMessage'] = "Password updated already"
        def_dict['status'] = False
        def_dict['email'] =  email
        return def_dict
    if not res:
        def_dict['status'] = False
        def_dict['email'] =  email
        return def_dict
    minutes_diff = (datetime.now() - res[1]).total_seconds() / 60.0
    if minutes_diff>10:
        def_dict['p_responseMessage'] = "Token Expired"
        def_dict['status'] = False
        def_dict['email'] =  email
        return def_dict
    def_dict['p_responseMessage'] = "Valid Token"
    def_dict['status'] = True
    def_dict['email'] =  email
    return def_dict

def addUser(data_dict):
    fullname, email,  password = data_dict["fullname"], data_dict["email"], data_dict["password"]
    args = [fullname, email,  password, 'p_status', 'p_code', 'p_id']
    ### Call Procedure
    res = dbApi.call_proc(db_str_mysql, args, 'addUser', 3, 6)
    return {"p_responseMessage":res[0]}

def get_date_range(thresh):
    today = datetime.today()
    yesterday = today - timedelta(days = 1)
    d1 = yesterday
    d2 = d1 - timedelta(days = thresh-1)
    d3 = d2 - timedelta(days = 1) 
    d4 = d3 - timedelta(days = thresh-1)
    return d1, d2, d3, d4

def check_date(current_d, start_d = '', end_d = ''):
    print(current_d, start_d, end_d)
    if start_d and end_d:
        print(start_d<=current_d<=end_d)
        return start_d<=current_d<=end_d

def get_cust_data_by_date(sub_id):
    c1_d1, c1_d2, c1_d3, c1_d4 = get_date_range(1)
    c7_d1, c7_d2, c7_d3, c7_d4 = get_date_range(7)
    c30_d1, c30_d2, c30_d3, c30_d4 = get_date_range(30)
    c1_st = dbApi.get_cust_data_Timerange(db_str_mysql, c1_d1, c1_d2, sub_id)
    c1_end = dbApi.get_cust_data_Timerange(db_str_mysql, c1_d3, c1_d4, sub_id)
    c7_st = dbApi.get_cust_data_Timerange(db_str_mysql, c7_d1, c7_d2, sub_id)
    c7_end = dbApi.get_cust_data_Timerange(db_str_mysql, c7_d3, c7_d4, sub_id)
    c30_st = dbApi.get_cust_data_Timerange(db_str_mysql, c30_d1, c30_d2, sub_id)
    c30_end = dbApi.get_cust_data_Timerange(db_str_mysql, c30_d3, c30_d4, sub_id)
    print("ddddd",c30_st)
    if c30_st:
        currency = c30_st[0][-1]
    else:
        currency = "USD"

    price1_c, price1_p = add_cost(c1_st, c1_end)
    price7_c, price7_p = add_cost(c7_st, c7_end)
    print("first 7 days data", c7_st, len(c7_st))
    print("1st 7 days price",  price7_c )
    print( "next 7 days data",c7_end, len(c7_end))
    print("next 7 dyas price",  price7_p)
    price30_c, price30_p,  = add_cost(c30_st, c30_end)
    return [price1_c, price1_p, price7_c, price7_p, price30_c, price30_p, currency]

def add_cost(data1, data2):
   c1 = 0
   c1_elm = [val[2]  for val in data1]
   c1  = sum(c1_elm)
   c2 = 0
   c2_elm = [val[2]  for val in data2]
   c2  = sum(c2_elm)
   return c1, c2

def customerPageData(data_dict={}):
    cust_sub_ids = dbApi.get_sub_ids(db_str_mysql)
    final_list = []
    count = 0
    xkeys = ["YESTERDAY", "LAST 7 DAYS", "LAST 30 DAYS"]
    day1 = {"name": "YESTERDAY", "name_2":"FROM DAY BEFORE"}
    day7 = {"name": "LAST 7 DAYS", "name_2":"FROM WEEK BEFORE"}
    day30 = {"name": "LAST 30 DAYS", "name_2":"FROM MONTH BEFORE"}
    for comapny_name, sub_ids in cust_sub_ids.items():
        temp_list = []
        c_id = 0
        for (sub_id, customer_id) in sub_ids:
            #data = dbApi.get_cust_data_60days(db_str_mysql, sub_id)
            res_list = get_cust_data_by_date(sub_id)
            if not temp_list:
                temp_list = res_list
            else:
                temp_list = [temp_list[i]+ x for i,x in enumerate(res_list)]
            c_id = customer_id  
        currency = res_list[-1]
        perc1 = 0
        f1 = "Increment"
        if temp_list[0]>0:
            perc1 = round(((temp_list[0] - temp_list[1])*1.0)/temp_list[0],1)
            if perc1<0:
                f1 = "Decrement"
        perc7 = 0
        f7 = "Increment"
        if temp_list[2]>0:
            perc7 = round(((temp_list[2] - temp_list[3])*1.0)/temp_list[2],1)
            if perc7<0:
                f7 = "Decrement"
        perc30 = 0
        f30 = "Increment"
        if temp_list[4]>0:
            perc30 = round(((temp_list[4] - temp_list[5])*1.0)/temp_list[4], 1)
            if perc30<0:
                f30 = "Decrement"
        day1["%s_P"%comapny_name] = str(perc1)
        day1["%s_A"%comapny_name] =  f1
        day1["%s_CID"%comapny_name] =  c_id
        day1[comapny_name] = int(temp_list[0])
        day1["sortF"] = 0
        day1["%s_cur"%comapny_name] = currency
        day7["%s_P"%comapny_name] = str(perc7)
        day7["%s_A"%comapny_name] =  f7
        day7["%s_CID"%comapny_name] =  c_id
        day7[comapny_name] = int(temp_list[2])
        day7["sortF"] = 0
        day7["%s_cur"%comapny_name] = currency
        day30["%s_P"%comapny_name] = str(perc30)
        day30["%s_A"%comapny_name] =  f30
        day30["%s_CID"%comapny_name] =  c_id
        day30[comapny_name] = int(temp_list[4])
        day30["sortF"] = 0
        day30["%s_cur"%comapny_name] = currency
        #final_list.append({"id":count, "company":comapny_name,"price1":["$%s"%str(temp_list[0]), int(temp_list[0]), str(perc1), f1],"price7":["$%s"%str(temp_list[2]), int(temp_list[2]), str(perc7), f7],"price30":["$%s"%str(res_list[4]), int(res_list[4]), str(perc30), f30]})
        count+=1

    return {"data":[day1, day7, day30], "ykeys":list(cust_sub_ids.keys()), "xkeys":xkeys}

def string_to_datetime(date_str):
    print(date_str)
    print(date_str.split("T"))
    date_obj = dateutil.parser.parse(date_str.split("T")[0])
    return date_obj

def insertCustCost(data_dict):
   file_path = data_dict["file_path"]
   col_name = data_dict["col_name"]
   df  = pd.read_csv(file_path)
   df1 = df.groupby('date').agg({col_name:'sum'})
   print(df1)
   cust_cred_id = data_dict["cust_sub_id"]
   subscription_id = data_dict["subscription_id"]
   dates = dbApi.get_date(db_str_mysql, cust_cred_id, subscription_id)
   for i in df1.index:
       date_ = string_to_datetime(i)
       if date_ not in dates:
           res = dbApi.insert_cust_cost(db_str_mysql, cust_cred_id, subscription_id, int(df1.loc[i,col_name]), date_)
       else:
           print(type(date_),date_,"ddddd", dates[0],type(dates[0]))
           cost = int(dbApi.get_cost(db_str_mysql,date_)[0])
           if cost!=int(df1.loc[i, col_name]):
               dbApi.update_cust_cost(db_str_mysql, int(df1.loc[i,col_name]), date_, cust_cred_id, subscription_id)
   return

def saveDataToShelve(file_name, type_):
    df = pd.read_csv(file_name)
    df["date"] = pd.to_datetime(df["date"])
    df["date"] = df["date"].dt.strftime('%d-%m-%Y')
    if type_ == 1:
        df1 = df.groupby(['date', "resourcelocation", "subscriptionid"]).agg({'cost':'sum'})
    else:
        df1 = df.groupby(['date', "resourcelocation", "subscriptionguid"]).agg({'paygprice':'sum'})
    cost_dict = {}
    for i in df1.index:
        if type_ == 1:
            cost = df1.loc[i, "cost"]
        else:
            cost = df1.loc[i, "paygprice"]
        cost_dict[i] = cost
    try:
        f1 = shelve.open("data",'r')
        f = shelve.open("data",'w')
        temp_d = {**f1["data"], **cost_dict}
        f["data"] = temp_d
        print(len(temp_d))
        f1.close()
    except Exception as e:
        print(e)
        f= shelve.open("data",'n')
        f["data"] = cost_dict

    f.close()

    return cost_dict

def saveRegions(file_name, type_):
    df = pd.read_csv(file_name)
    sub_dict = {}
    regions = df.resourcelocation.unique().tolist()
    if type_ == 1:
        sub_id = df.subscriptionid.unique()
    else:
        sub_id = df.subscriptionguid.unique()
    sub_dict[sub_id[0].lower()] = {"Regions":regions, "Tags":[]}
    shelve_file = "./sub_data.db"
    if not os.path.exists(shelve_file):
        print("if", file_name)
        f = shelve.open(shelve_file, 'n')
    else:
        print("else", file_name)
        shelve_file = "./sub_data"
        f = shelve.open(shelve_file, 'w')
    my_dict = f.get('data', {})
    print(my_dict)
    my_dict.update(sub_dict)
    f["data"] = my_dict
    print(f["data"])
    f.close()
    return sub_dict

def getCustomerFilterData(data_dict):
    cust_name = data_dict["cust_name"]
    res_dict =  mongo_methods.get_subids(db_str_mongo, cust_name)
    return {"Subscription": res_dict["sub"], "Region":res_dict["regions"], "Tags":res_dict["tags"]}

def get_all_dates(start_date, end_date):
    delta = end_date - start_date
    dates = []
    for i in range(delta.days+1):
        dt1 = start_date + timedelta(days=i)
        dt2 = dt1.strftime("%Y-%m-%d")
        dates.append(dt2)
    #dates = [start_date + timedelta(days=i).strptime("%d-%m-%Y") for i in range(delta.days+1)]
    return dates


def customerUsageDetails_1(data_dict):
    out = {}
    for date_, sub_dict in data_dict.items():
        for sub_id, cost in sub_dict.items():
            if not out.get(sub_id, {}):
                out[sub_id] = cost
            else:
                out[sub_id]+=cost

    tup_val = [(v,k)for k,v in out.items()]
    tup_val = sorted(tup_val, reverse=True)
    top_7_sub = [k for (v,k) in tup_val[:7]]
    gdata_dict = {}
    for date_, sub_dict in data_dict.items():
        new_sub_dict = {}
        for sub_id, cost in sub_dict.items():
            if sub_id in top_7_sub:
                new_sub_dict[sub_id] = cost
            else:
                cost_o = new_sub_dict.get('Others', 0)
                new_sub_dict['Others'] = cost_o+cost
        gdata_dict[date_] = copy.deepcopy(new_sub_dict)
    gxkeys = top_7_sub + ["Others"]

    return gdata_dict, gxkeys

def getFinalDictCustomer(final_dict, all_dates):
    out =[]
    subs_distinct = {}
    for date1,date2 in all_dates:
        v = final_dict.get(date1, {})
        temp_dict = {}
        temp_dict["name"] = date1
        temp_dict["d_date"] = date2
        total = 0
        for sub, cost in v.items():
            print(sub)
            currency = dbApi.get_currency(db_str_mysql, sub.lower())
            temp_dict[sub] = cost
            subs_distinct[sub] = 1
            total+=cost
            temp_dict['%s_Curr'%sub]  = currency
        temp_dict["opacity"] = 0.7
        temp_dict["Total"] =  round(total, 2)
        out.append(copy.deepcopy(temp_dict))
    return out, subs_distinct

def get_all_months(date_str_list):
    month_list = []
    for date_ in date_str_list:
        y,m,d = date_.split("-")
        m_y = "%s_%s"%(m,y)
        if m_y not in month_list:
            month_list.append(m_y)
    return month_list

def customerUsageDetails(data_dict = {}):
    subs = [val.lower() for val in data_dict["subscriptions"]]
    dates = [datetime.strptime(d.split("T")[0], '%Y-%m-%d') for d in data_dict["date"]]
    all_dates = get_all_dates(dates[0], dates[1])
    month_list = get_all_months(all_dates)
    dict1 = {}
    for (sub, month_year) in itertools.product(*[subs, month_list]):
        sub_new = sub.replace("-", "")
        collection_name = "n_%s_%s"%(sub_new, month_year)
        temp_dict = mongo_methods.get_cost(db_str_mongo, collection_name, sub)
        dict1.update(temp_dict)
    lists =[all_dates, data_dict["regions"], subs]
    products = itertools.product(*lists)
    final_dict = {}
    all_ui_dates = []
    for (date, region, subscription) in products:
        print(date, dict1.keys())
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_ui = date_obj.strftime("%d-%b")
        d = date_obj.strftime("%Y-%m-%d")
        if [date_ui,d] not in all_ui_dates:
            all_ui_dates.append([date_ui,d])
        if not final_dict.get(date_ui,{}):
            final_dict[date_ui] = {}
        cst = dict1.get(tuple([date, region, subscription]), '')
        if not cst:continue

        if not final_dict[date_ui].get(subscription,{}):
            final_dict[date_ui][subscription] = round(cst,2)
        else:
            sub_cost = final_dict[date_ui][subscription] + cst
            cost = round(sub_cost,2)
            final_dict[date_ui][subscription] = cost
    dats_distinct = final_dict.keys()
    if len(data_dict["subscriptions"])>7:
        gdata, gxkeys = customerUsageDetails_1(final_dict)
        gdata_final, subs_distinct = getFinalDictCustomer(gdata, all_ui_dates)
    else:
        out, subs_distinct = getFinalDictCustomer(final_dict, all_ui_dates)
        gdata_final = out
        gxkeys = list(dats_distinct)

    Tobj =  table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.storeData({"txkeys": list(dats_distinct), "tykeys": ["Total"]+list(subs_distinct.keys()),"tdata": out})
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]   


    return {"txkeys": ntxkeys, "tykeys": ntykeys ,"tdata": ntdata, "gdata": gdata_final, "gxkeys":gxkeys, "gykeys":list(subs_distinct.keys()), "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"]}

def getTalbePaginate_Sort(data_dict):
    #{
    #"key": 1,
    #"currentPage": 2,
    #"rowsCountPerTable": 20
    #}
    key = data_dict["key"]
    sorder = data_dict["sort_order"]
    column_id = data_dict["column_id"]
    Tobj = table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.sortData(key, column_id, sorder)
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]   
    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "key": ndata_dict["key"], "records": ndata_dict["records"]}
 

def getTalbePaginate(data_dict):
    #{
    #"key": 1,
    #"currentPage": 2,
    #"rowsCountPerTable": 20
    #}
    key = data_dict["key"]
    page_no = data_dict["currentPage"]
    no_of_rows = data_dict["rowsCountPerTable"]
    Tobj = table_paginate.table_paginate('142.93.208.71')
    ndata_dict = Tobj.getPageData(key, page_no, no_of_rows)
    ntxkeys = ndata_dict["txkeys"]   
    ntykeys = ndata_dict["tykeys"]   
    ntdata = ndata_dict["tdata"]   
    return {"txkeys": ntxkeys, "tykeys": ntykeys,"tdata": ntdata, "key": ndata_dict["key"], "total_pages": ndata_dict["total_pages"], "records": ndata_dict["records"]}
 

def downloadCSV(data_dict):
    r_data = data_dict["tdata"]   # here I'm assuming key name is "rawdata" in json file.
    x_axis = data_dict["txkeys"]     # here I'm assuming key name is "xaxis" in json file.
    y_axis = data_dict["tykeys"]     # here I'm assuming key name is "Yaxis" in json file.
    comp_name = data_dict["comp_name"]     # here I'm assuming key name is "Yaxis" in json file.
    f_name = str(datetime.now()).split(" ")[0]
    dframe = {}
    i = 0
    for xi in x_axis:
        d = r_data[i]
        for yi in y_axis:
            str_value = d.get(yi, "")
            if yi not in dframe:
                dframe[yi] = [str_value]
            else:
                dframe[yi] += [] + [str_value]
        i += 1

    df = pd.DataFrame(dframe)
    df_trans = df.transpose()
    csv_path = "/home/azureuser/icco_api/apis/data/"
    df_trans.to_csv("%s%s.csv"%(csv_path, f_name), header=x_axis)
    all_rows = [df_trans.columns]
    #print ('df: ', df_trans, df_trans.columns)
    #for index, row in df_trans.iterrows():
    #    tmp = []
    #    for col in df_trans.columns: 
    #        tmp.append(row[col])
    #    all_rows.append(tmp)
    return csv_path, "%s.csv" %f_name, all_rows

if __name__ == '__main__':
    data_dict = {
    "subscriptions": [
        "bb953f35-22e7-431c-a6c3-fa44e577c5bc"
    ],
    "regions": [
        "EASTUS",
        "SOUTHCENTRALUS"
    ],
    "tags": [],
    "date": [
        "2022-12-7T00:00:00.0000000Z",
        "2022-12-14T00:00:00.0000000Z"
    ]
}
    #print(customerPageData())
    data_dict = {"subscriptions":["bb953f35-22e7-431c-a6c3-fa44e577c5bc"],"regions":["EASTUS","SOUTHCENTRALUS"],"tags":[],"date":["2022-12-14T00:00:00.0000000Z","2022-12-21T00:00:00.0000000Z"]}

    customerUsageDetails(data_dict)


    

    pass
