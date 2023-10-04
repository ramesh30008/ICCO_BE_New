class DeleteByUserCustomer(MethodView):
    def get(self):
        """ Responds to GET requests """
        #return "Responding to a GET request"
        return


    def post(self):
        if 1:#try
            data_dict = request.get_json()
            user = data_dict["user"]
            customer = data_dict["customer"]
            def_dict=api41.delete_by_user_customer(user,customer)
        return jsonify(def_dict)

app.add_url_rule("/cqICCOpApi/DeleteByUserCustomer", view_func =  DeleteByUserCustomer.as_view("DeleteByUserCustomer"))



