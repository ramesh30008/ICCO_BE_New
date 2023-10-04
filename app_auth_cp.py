from flask import Flask, make_response, jsonify, request, redirect, url_for, jsonify, send_from_directory
from flask.views import MethodView
from flask_cors import CORS
import sys
import os
import time
import jwt 
from functools import wraps
import datetime
from utils.config import port_num
from utils.config import host_ip
from utils.config import SECRET_KEY
import apis.api_methods_new as api_methods
#import apis.icco_api31 as api31
import apis.icco_api31_new as api31
import apis.icco_api32 as api32
import apis.icco_api32_Cost as api32_Cost
import apis.icco_api32_LSHR as api32_LSHR
import apis.icco_api32_HourlyPeek as api32_HPC
import apis.icco_api_TagExplorer as api32_Tag
import apis.icco_api_Users as api32_users
import apis.icco_api33_New as api33
import apis.icco_api34_New as api34
import apis.icco_api35_New as api35
#import apis.icco_api36 as api36
import apis.icco_api37 as api37
import table_paginate
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = SECRET_KEY

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        #token = request.args.get('token') #http://127.0.0.1:5000/route?token=alshfjfjdklsfj89549834ur
        token = request.headers['Token'].encode('utf-8')

        if not token:
            return jsonify({'message' : 'Token is missing!'}), 403

        try: 
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message' : 'Token is invalid!'}), 403

        return f(*args, **kwargs)

    return decorated


class SignUp(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
           def_dict = api_methods.sign_up(data_dict)
           token = jwt.encode({'user' : def_dict['email'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=500)}, app.config['SECRET_KEY'])
           if def_dict["p_status"] == "Success":
              def_dict['jwt_token'] = token
           return jsonify(def_dict)
        #except: 
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)
         
app.add_url_rule("/cqICCOpApi/SignUp", view_func=SignUp.as_view("SignUp"))

class SignIn(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        print(data_dict,"data")
        if 1:#try:
            def_dict = api_methods.sign_in(data_dict)
            if def_dict.get("p_status", "")=="User successfully logged in":
               token = jwt.encode({'user' : def_dict['email'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'])
               def_dict['jwt_token'] = token
            return jsonify(def_dict)
        #except: 
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/SignIn", view_func=SignIn.as_view("SignIn"))

class ValidateEmail(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.validate_email(data_dict)
            token = jwt.encode({'user' : def_dict['email'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=500)}, app.config['SECRET_KEY'])
            if def_dict["p_status"] == "User Email Validated successfully!":
               def_dict['jwt_token'] = token
               def_dict['jwt_token'] = token
            return jsonify(def_dict)
        #except: 
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqIDPpApi/ValidateEmail", view_func=ValidateEmail.as_view("ValidateEmail"))

class getTablePaginate(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.getTablePaginate(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getTablePaginate", view_func = getTablePaginate.as_view("getTablePaginate"))

class getTablePaginate_Sort(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.getTablePaginate_Sort(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getTablePaginate_Sort", view_func = getTablePaginate_Sort.as_view("getTablePaginate_Sort"))




class resendOTP(MethodView):
    def get(self, uid):
        """ Responds to GET requests """
        if 1:#try:
            def_dict = api_methods.resendOTP(uid)
        return jsonify(def_dict)
        #except: 
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

    def post(self):
        return "Responding to a POST request"

app.add_url_rule("/cqIDPpApi/resendOTP/<uid>", view_func=resendOTP.as_view("resendOTP"))

class forgotPassword(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.forgotPassword(data_dict)
        return jsonify(def_dict)
        #except: 
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqIDPpApi/forgotPassword", view_func=forgotPassword.as_view("forgotPassword"))

class resetPassword(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.resetPassword(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqIDPpApi/resetPassword_U", view_func=resetPassword.as_view("resetPassword"))

class validatePassword(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.validatePassword(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqIDPpApi/resetPassword_V", view_func=validatePassword.as_view("validatePassword"))

class addUser(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.addUser(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/addUser", view_func=addUser.as_view("addUser"))

class customerPageData(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.customerPageData(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/customerPageData", view_func=customerPageData.as_view("customerPageData"))

class insertCustCost(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api_methods.insertCustCost(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/insertCustCost", view_func=insertCustCost.as_view("insertCustCost"))

class getCustomerFilterData(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api31.getCustomerFilterData(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getCustomerFilterData", view_func=getCustomerFilterData.as_view("getCustomerFilterData"))

class customerUsageDetails(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request"

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api31.customerUsageDetails(data_dict)
        return jsonify(def_dict)
        #except:
        #   def_dict = {'p_code': '', 'p_status': 'API Error', 'uid': ''}
        #   return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/customerUsageDetails", view_func=customerUsageDetails.as_view("customerUsageDetails"))

class downloadCSV(MethodView):

    def get(self):

        """ Responds to GET requests """

        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            csv_path, fname, all_rows = api_methods.downloadCSV(data_dict)
        print ("csv_path: ", csv_path, fname, all_rows)
        return send_from_directory(csv_path, fname, as_attachment=True) 
        #return {"res":"hhhhhhhhhhhhhhhh"}
app.add_url_rule("/cqICCOpApi/downloadCSV", view_func = downloadCSV.as_view("downloadCSV"))

class getHostpoolFilters(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_Cost.getCustomerHpFilterData(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/getHostpoolFilters", view_func = getHostpoolFilters.as_view("getHostpoolFilters"))

class getHostpoolCostBydate(MethodView):

    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_Cost.customerHpUsageDetails(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/getHostpoolCostBydate", view_func = getHostpoolCostBydate.as_view("getHostpoolCostBydate"))

class getCostByDateAndSid(MethodView):

    def get(self):

        """ Responds to GET requests """

        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            #def_dict = api32.getCostByDateAndSid(data_dict)
            def_dict = api31.getCostByDateAndSid(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getCostByDateAndSid", view_func = getCostByDateAndSid.as_view("getCostByDateAndSid"))

class getCostByDateAndHostpool(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_Cost.getHpCostByDateAndHp(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/getCostByDateAndHostpool", view_func = getCostByDateAndHostpool.as_view("getCostByDateAndHostpool"))

class getHourlyPeakConcurrency(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_HPC.getHPCUsageDetails(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getHourlyPeakConcurrency", view_func = getHourlyPeakConcurrency.as_view("getHourlyPeakConcurrency"))

class getHostPoolsLoginSummary(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_LSHR.getHostPoolsLoginSummary(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getHostPoolsLoginSummary", view_func = getHostPoolsLoginSummary.as_view("getHostPoolsLoginSummary"))

class getHostPoolsHourlyReportWVD(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict, def_dict2 = api32_LSHR.getHostPoolsHourlyReportWVD(data_dict)
        return jsonify({"data": def_dict, "data2": def_dict2})

app.add_url_rule("/cqICCOpApi/getHostPoolsHourlyReportWVD", view_func = getHostPoolsHourlyReportWVD.as_view("getHostPoolsHourlyReportWVD"))

class getRgroupFilters(MethodView):

    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api33.getCustomerRgFilterData(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/getRgroupFilters", view_func = getRgroupFilters.as_view("getRgroupFilters"))

class rGroupCostHistory(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "
    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api33.customerRgUsageDetails(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/rGroupCostHistory", view_func =  rGroupCostHistory.as_view("rGroupCostHistory"))

class tableClickResourceGroup(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api33.getRgCostByDateAndRg(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/tableClickResourceGroup", view_func =  tableClickResourceGroup.as_view("tableClickResourceGroup"))

class getZeroLoginHostpools(MethodView):

    def get(self):

        """ Responds to GET requests """

        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_HPC.getHPCZeroLogins(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getZeroLoginHostpools", view_func =  getZeroLoginHostpools.as_view("getZeroLoginHostpools"))

class resourcesCostHistory(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api34.customerResUsageDetails(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/resourcesCostHistory", view_func = resourcesCostHistory.as_view("resourcesCostHistory"))

class tableClickResources(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api34.getResCostByDateAndRes(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/tableClickResources", view_func = tableClickResources.as_view("tableClickResources"))

class DesktopCostHistory(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api35.customerDesktopUsageDetails(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/DesktopCostHistory", view_func = DesktopCostHistory.as_view("DesktopCostHistory"))

class getDesktopFilters(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api35.getCustomerDesktopFilterData(data_dict)
        return jsonify(def_dict)
app.add_url_rule("/cqICCOpApi/getDesktopFilters", view_func = getDesktopFilters.as_view("getDesktopFilters"))

class getHostpoolCostBydate_TP(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32.getHostpoolCostBydate_TP(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getHostpoolCostBydate_TP", view_func = getHostpoolCostBydate_TP.as_view("getHostpoolCostBydate_TP"))

class getHostpoolCostBydate_TP_Sort(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32.getHostpoolCostBydate_TP_Sort(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getHostpoolCostBydate_TP_Sort", view_func = getHostpoolCostBydate_TP_Sort.as_view("getHostpoolCostBydate_TP_Sort"))

class getTagsFilters(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api36.getTagsFilters(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/getTagsFilters", view_func = getTagsFilters.as_view("getTagsFilters"))


class TagExplorerCostHistory(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_Tag.TagExplorerCostHistory(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/TagExplorerCostHistory", view_func = TagExplorerCostHistory.as_view("TagExplorerCostHistory"))


class UsersCostHistory(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try:
            def_dict = api32_users.UsersUsageDetails(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/UsersCostHistory", view_func = UsersCostHistory.as_view("UsersCostHistory"))

class GetGraphData(MethodView):
    def get(self):
        """ Responds to GET requests """
        return "Responding to a GET request = "

    def post(self):
        data_dict = request.get_json()
        if 1:#try
            data_dict = request.get_json()
            def_dict=api31.graphclick(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetGraphData", view_func = GetGraphData.as_view("GetGraphData"))


class insert_cdata(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return
    
    
    def post(self):
        if 1:#try
            data_dict = request.get_json()
            def_dict=api_methods.insert_cinfo(data_dict)   
        return jsonify(def_dict) 

app.add_url_rule("/cqICCOpApi/insert_cdata", view_func = insert_cdata.as_view("insert_cdata")) 

class GetClientList(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            def_dict=api_methods.get_client_list(data_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetClientList", view_func = GetClientList.as_view("GetClientList"))

if __name__ == '__main__':
    app.run(debug=True, host = "0.0.0.0", port = 4001)
