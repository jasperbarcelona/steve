import flask
from flask import request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import Boolean
from db_conn import db, app
import json

class Serializer(object):
  __public__ = None

  def to_serializable_dict(self):
    dict = {}
    for public_key in self.__public__:
      value = getattr(self, public_key)
      if value:
        dict[public_key] = value
    return dict

class SWEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Serializer):
      return obj.to_serializable_dict()
    if isinstance(obj, (datetime)):
      return obj.isoformat()
    return json.JSONEncoder.default(self, obj)

def SWJsonify(*args, **kwargs):
  return app.response_class(json.dumps(dict(*args, **kwargs), cls=SWEncoder, 
         indent=None if request.is_xhr else 2), mimetype='application/json')
        # from https://github.com/mitsuhiko/flask/blob/master/flask/helpers.py

class Client(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(50))
    app_id = db.Column(db.Text())
    app_secret = db.Column(db.Text())
    passphrase = db.Column(db.Text())
    pricing = db.Column(db.String(10))
    shortcode = db.Column(db.String(30))
    created_at = db.Column(db.String(50))

class Customer(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(50))
    msisdn = db.Column(db.String(30),default='')
    email = db.Column(db.String(100),default='')
    created_at = db.Column(db.String(50))

class AdminUser(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32))
    email = db.Column(db.String(60))
    password = db.Column(db.Text())
    temp_pw = db.Column(db.Text())
    name = db.Column(db.String(100))
    role = db.Column(db.String(30))
    permissions = db.Column(db.String(100))
    active_sort = db.Column(db.String(30))
    added_by_id = db.Column(db.Integer)
    added_by_name = db.Column(db.String(100))
    join_date = db.Column(db.String(50))
    created_at = db.Column(db.String(50))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_no = db.Column(db.String(32))
    date = db.Column(db.String(30))
    time = db.Column(db.String(10))
    month_year = db.Column(db.String(60))
    status = db.Column(db.String(30))
    cashier_id = db.Column(db.Integer())
    cashier_name = db.Column(db.String(60))
    customer_name = db.Column(db.String(60), nullable=True)
    customer_email = db.Column(db.String(60), nullable=True, default='')
    customer_msisdn = db.Column(db.String(30), nullable=True, default='')
    process_date = db.Column(db.String(30), default='')
    process_time = db.Column(db.String(10), default='')
    done_date = db.Column(db.String(30), default='')
    done_time = db.Column(db.String(10), default='')
    pickup_date = db.Column(db.String(30), default='')
    pickup_time = db.Column(db.String(10), default='')
    total = db.Column(db.String(30))
    additional_charge = db.Column(db.String(30))
    notes = db.Column(db.Text())
    created_at = db.Column(db.String(50))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_no = db.Column(db.String(32))
    name = db.Column(db.String(30))
    price = db.Column(db.String(10))

class Report(db.Model, Serializer):
    id = db.Column(db.Integer,primary_key=True)
    client_no = db.Column(db.String(32))
    name = db.Column(db.String(60))
    report_type = db.Column(db.String(60))
    from_date = db.Column(db.String(30))
    to_date = db.Column(db.String(30))
    generated_by = db.Column(db.String(60))
    generated_by_id = db.Column(db.Integer())
    date = db.Column(db.String(50))
    time = db.Column(db.String(30))
    status = db.Column(db.String(30),default='Pending')
    created_at = db.Column(db.String(50))

class TransactionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_no = db.Column(db.String(32))
    transaction_id = db.Column(db.Integer())
    service_id = db.Column(db.Integer())
    service_name = db.Column(db.String(30))
    quantity = db.Column(db.String(10))
    price = db.Column(db.String(10))
    total = db.Column(db.String(10))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_no = db.Column(db.String(32))
    date = db.Column(db.String(60))
    year = db.Column(db.String(10))
    transactions = db.Column(db.Integer())
    price = db.Column(db.String(30))
    created_at = db.Column(db.String(50))
    receipt_path = db.Column(db.Text(), default='')