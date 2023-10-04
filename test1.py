from flask import Flask, make_response, jsonify, request, redirect, url_for, jsonify, send_from_directory
from flask.views import MethodView
from flask_cors import CORS
import sys
import os
import time
import jwt
from functools import wraps
import datetime
import apis.api_methods as api
app = Flask(__name__)
CORS(app)
SECRET_KEY = ""
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

if __name__ == '__main__':
    app.run(debug=True)

