import requests
import adal
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import time
sys.path.append('/home/durga/icco_api_dev/db_mgmt')
import dbApi
import mongo_methods
sys.path.insert(0, '/home/durga/icco_api_dev')
from utils.config import db_str_mysql, db_str_mongo

def getAccessToken(application_id, secret, tenant_id):
    AUTH_ENDPOINT = 'https://login.microsoftonline.com/'
    RESOURCE  = 'https://management.core.windows.net/'
    # get an Azure access token using the adal library
    context = adal.AuthenticationContext(AUTH_ENDPOINT + tenant_id)
    token_response = context.acquire_token_with_client_credentials(RESOURCE, application_id, secret)
    access_token = token_response.get('accessToken')
    return access_token

def execute_endpoint(endpoint, access_token):
    headers = {"Authorization": 'Bearer ' + access_token}
    print(endpoint)
    json_output = requests.get(endpoint, headers=headers).json()
    return json_output

def getSubscriptions(access_token):
    subscriptions = []
    endpoint = 'https://management.azure.com/subscriptions/?api-version=2015-01-01'
    json_output = execute_endpoint(endpoint, access_token)
    for sub in json_output["value"]:
        subscriptions.append([sub["displayName"], sub["subscriptionId"]])
    return subscriptions

def getUsageData(subscriptionId, access_token, api_version):
    #sub_url = "https://management.azure.com/subscriptions/%s/providers/Microsoft.Consumption/usageDetails?api-version=%s"
    today = datetime.today()
    start_d = today - timedelta(days = 30)
    today = str(today).split()[0]
    start_d = str(start_d).split()[0]
    sub_url = "https://management.azure.com/subscriptions/%s/providers/Microsoft.Consumption/usageDetails?$filter=properties/usageStart ge '%s' and properties/usageEnd le '%s'&api-version=%s"
    json_output = execute_endpoint(sub_url %(subscriptionId, start_d, today, api_version), access_token)
    return json_output

def getTagList(subscriptionId, access_token, api_version):
    apData = {}
    sub_url = "https://management.azure.com/subscriptions/%s/tagNames?api-version=%s"
    #sub_url = "https://management.azure.com/subscriptions/%s/providers/Microsoft.Resources/tags/default?api-version=%s"
    #sub_url = "https://management.azure.com/subscriptions/%s/providers/Microsoft.Consumption/tags?api-version=%s"
    sub_url1 = "https://management.azure.com/subscriptions/%s/resources?$filter=tagName eq '%s' and tagValue eq '%s'&api-version=%s"
    json_output = execute_endpoint(sub_url%(subscriptionId,"2021-04-01"), access_token)
    for tg in json_output["value"]:
        print(tg.get("tagName"))
        print("!!!!!!!")
        for vtg in tg["values"]:
            print(vtg.get("tagValue"))
            print("##########################################################")
            json_output1 = execute_endpoint(sub_url1%(subscriptionId,tg.get("tagName"),vtg.get("tagValue"),"2022-09-01"), access_token)
            print(json_output1)
            print("##########################################################")  
            for k,v in json_output1.items():
                if not apData.get(k):
                    apData[k] = [v]
                else:
                    apData[k].append(v)
    return apData   


def getUserSessions(access_token, session_host_list, subId ):
    res_list = []
    hostpool_id_dict = mongo_methods.get_sub_hostpool_data(db_str_mongo, subId)
    processed_hnames = []
    #sub_url = "https://management.azure.com/subscriptions/%s/resourceGroups/%s/providers/Microsoft.DesktopVirtualization/hostPools/%s/sessionHosts/%s/userSessions?api-version=%s"
    sub_url = "https://management.azure.com/subscriptions/%s/resourceGroups/%s/providers/Microsoft.DesktopVirtualization/hostPools/%s/userSessions?api-version=%s"
    for data_dict in session_host_list:
        hostpool_id = data_dict["hostpool_id"]
        hostpool_name = hostpool_id_dict[hostpool_id]["hostpool_name"]
        if hostpool_name in processed_hnames:continue
        processed_hnames.append(hostpool_name)
        resource_grp = hostpool_id_dict[hostpool_id]["resource_group"]  
        #userSession = execute_endpoint(sub_url%(subId, resource_grp, hostpool_name, data_dict["session_host_name"],"2022-02-10-preview"), access_token)
        userSession = execute_endpoint(sub_url%(subId, resource_grp, hostpool_name,"2022-02-10-preview"), access_token)
        for temp_dict in userSession["value"]:
            session_name = temp_dict["name"]
            session_id = temp_dict["id"]
            user_principle_name = temp_dict["properties"]["userPrincipalName"]
            application_type = temp_dict["properties"]["applicationType"]
            session_state = temp_dict["properties"]["sessionState"]
            ad_username = temp_dict["properties"]["activeDirectoryUserName"]
            res_dict = {"subscription_id": subId, "hostpool_id": hostpool_id, "session_name": session_name, "session_id": session_id, "user_principle_name":user_principle_name, "application_type": application_type, "session_state":session_state, "ad_username":ad_username}
            res_list.append(res_dict)
    return res_list

def getSessionsHost(access_token, hostPools_list):
    res_list = []
    sub_url = "https://management.azure.com/subscriptions/%s/resourceGroups/%s/providers/Microsoft.DesktopVirtualization/hostPools/%s/sessionHosts?api-version=%s"
    for data_dict in hostPools_list:
        userSession = execute_endpoint(sub_url%(data_dict["subscription"], data_dict["resource_group"], data_dict["hostpool_name"],"2022-02-10-preview"), access_token)
        for temp_dict in userSession["value"]:
            session_host_name = temp_dict["name"]
            session_host_id = temp_dict["id"]
            session_host_type = temp_dict["type"]
            resource_id = temp_dict["properties"]["resourceId"]
            session_host_status = temp_dict["properties"]['status']
            vm_id = temp_dict["properties"]["virtualMachineId"]
            sessions_count = temp_dict["properties"]["sessions"]
            res_dict = {"subscription_id": data_dict["subscription"], "hostpool_id": data_dict["_id"], "session_host_name": session_host_name, "session_host_id": session_host_id, "session_host_type": session_host_type, "resource_id": resource_id, "session_host_status": session_host_status, "vm_id":vm_id, "sessions_count":sessions_count}
            res_list.append(res_dict)  
    return res_list

def read_hostpool_json(json_output, sub_id):
    res_list = []
    for temp_dict in json_output["value"]:
        hostpool_name = temp_dict["name"]
        location = temp_dict["location"]
        tag_dict = temp_dict["tags"]
        if tag_dict:
            print(tag_dict)
            hh
        tag_list = [k+"_"+v for k,v in tag_dict.items()]
        resource_id = temp_dict["id"]
        resource_group = resource_id.split("/")[4]
        app_group_name = "NA"
        app_group_type = "NA"
        host_pool_type = temp_dict["properties"]["hostPoolType"]
        res_dict = {"hostpool_name":hostpool_name, "location":location, "subscription":sub_id, "resource_group":resource_group, "app_group_name":app_group_name, "app_group_type":app_group_type, "hostpool_type":host_pool_type, "tags":tag_list}
        res_list.append(res_dict)
    return res_list

    
def main():
    sub_idxs = dbApi.get_all_subscriptions(db_str_mysql)
    for rows in sub_idxs:
        print("Sub id ================", rows[5])
        application_id = rows[2]
        secret = rows[4]
        tenant_id = rows[3]
        subId = rows[5]
        access_token = getAccessToken(application_id, secret, tenant_id)
        host_pools_list = getHostPools(subId, access_token)    
        host_pools_list = mongo_methods.insert_hostpool_mgmt(db_str_mongo, host_pools_list, subId)
        session_host_list = getSessionsHost(access_token, host_pools_list)
        session_host_list = mongo_methods.insert_session_host_mgmt(db_str_mongo, session_host_list, subId)
        mongo_methods.insert_session_host_status_timeseries(db_str_mongo, session_host_list, subId)
        user_session_list = getUserSessions(access_token, session_host_list, subId)
        user_session_list = mongo_methods.insert_session_mgmt(db_str_mongo, user_session_list, subId)
        mongo_methods.insert_session_status_timeseries(db_str_mongo, user_session_list, subId)


 
def getHostPools(subId, access_token):
    sub_url = "https://management.azure.com/subscriptions/%s/providers/Microsoft.DesktopVirtualization/hostPools?api-version=%s"
    hostPools = execute_endpoint(sub_url%(subId,"2022-02-10-preview"), access_token)
    res_list = read_hostpool_json(hostPools, subId )
    return res_list
    


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
    #hostpools,at = getHostPools(1)
    #sesiionHost = getSessionsHost(at, hostpools)
