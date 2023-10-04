import apis.icco_api41_cp as api41

class GetPermissionInfo(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            def_dict=api41.get_permission_info()
            print(def_dict)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetPermissionInfo", view_func = GetPermissionInfo.as_view("GetPermissionInfo"))

class GetAllCustomers(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            def_dict=api41.get_all_customers()
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetAllCustomers", view_func = GetAllCustomers.as_view("GetAllCustomers"))

class GetDomainsByCustomer(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            customer_id = data_dict.get("customer_id")
            def_dict=api41.get_domains_by_customer(customer_id)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetDomainsByCustomer", view_func = GetDomainsByCustomer.as_view("GetDomainsByCustomer"))


class UpdatePermissionsByUid(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            user_id = data_dict.get("user_id")
            permission_id = data_dict.get("permission_id")
            def_dict=api41.update_permissions(user_id,permission_id)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/UpdatePermissionsByUid", view_func = UpdatePermissionsByUid.as_view("UpdatePermissionsByUid"))


class UpdateDomainSubscription(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            uid = data_dict.get("uid")
            user = data_dict.get("user")
            customer = data_dict.get("customer")
            data = data_dict.get("data")
            def_dict=api41.update_domain_subscription(uid,user,customer,data)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/UpdateDomainSubscription", view_func = UpdateDomainSubscription.as_view("UpdateDomainSubscription"))

class GetCustomersByUserId(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            uid = data_dict.get("uid")
            def_dict=api41.get_customer_details_by_user(uid)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/GetCustomersByUserId", view_func =  GetCustomersByUserId.as_view("GetCustomersByUserId"))



