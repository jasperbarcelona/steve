from flask import url_for, request, session, redirect, jsonify, Response, make_response, current_app
from jinja2 import environment, FileSystemLoader
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import Boolean
from sqlalchemy import or_
from flask.ext import admin
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin import Admin, BaseView, expose
from dateutil.parser import parse as parse_date
from flask import render_template, request
from flask import session, redirect
from datetime import timedelta
from datetime import datetime
from functools import wraps, update_wrapper
import threading
from threading import Timer
from multiprocessing.pool import ThreadPool
import calendar
from calendar import Calendar
from time import sleep
import requests
import datetime
from datetime import date
import time
import json
import uuid
import random
import string
import smtplib
from email.mime.text import MIMEText as text
import os
import schedule
from werkzeug.utils import secure_filename
import db_conn
from db_conn import db, app
from werkzeug.security import generate_password_hash, check_password_hash
from models import *

IPP_URL = 'https://devapi.globelabs.com.ph/smsmessaging/v1/outbound/%s/requests'
UPLOAD_FOLDER = 'static/receipts'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class BubbleAdmin(sqla.ModelView):
    column_display_pk = True

admin = Admin(app, name='Wasg It')
admin.add_view(BubbleAdmin(Client, db.session))
admin.add_view(BubbleAdmin(AdminUser, db.session))
admin.add_view(BubbleAdmin(Transaction, db.session))
admin.add_view(BubbleAdmin(TransactionItem, db.session))
admin.add_view(BubbleAdmin(Service, db.session))
admin.add_view(BubbleAdmin(Bill, db.session))
# admin.add_view(BubbleAdmin(Service, db.session))

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response    
    return update_wrapper(no_cache, view)

def send_email(email_address,customer_name):
    if email_address == '':
        return True
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        myGmail = 'washitlaundryservices@gmail.com'
        myGMPasswd = 'Password123_'
        message = text(('Hi, %s!\r\n \r\nWe\'re happy to let you know that your laundy is now ready for pickup. Thank you.'
                   '\r\n \r\nBest Regards,\r\nWash It') % customer_name)
        message['Subject'] = 'Your Laundry is Ready'
        message['From'] = 'Wash It'
        message['To'] = '%s <%s>' % (email_address, email_address)

        s.starttls()
        s.login(myGmail, myGMPasswd)
        s.sendmail(myGmail,[email_address],message.as_string())
        s.quit()
        return True
    except:
        return False


@app.route('/',methods=['GET','POST'])
@nocache
def index():
    if not session:
        return redirect('/login')

    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()

    if user.active_sort == 'Alphabetical':
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.customer_name).all()
    else:
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.created_at.desc()).all()
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').count()

    services = Service.query.filter_by(client_no=session['client_no']).order_by(Service.name).all()

    return flask.render_template(
        'index.html',
        client_name=session['client_name'],
        transactions=transactions,
        total_entries=total_entries,
        services=services,
        user=user,
        change_pw=session['change_pw']
        )


@app.route('/user/sort/edit',methods=['GET','POST'])
def edit_user_sort():
    sort = flask.request.form.get('sort_val')
    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()
    user.active_sort = sort
    db.session.commit()

    if user.active_sort == 'Alphabetical':
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.customer_name).all()
    else:
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.created_at.desc()).all()
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').count()

    return jsonify(
        template = flask.render_template(
            'transactions_result.html',
            transactions = transactions,
            user=user
            ),
        total_entries = total_entries,
        sort = user.active_sort
        )


@app.route('/active/search',methods=['GET','POST'])
def search_active_transactions():
    keyword = flask.request.form.get('keyword')
    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()
    if keyword != '':
        transactions = Transaction.query.filter(Transaction.customer_name.ilike('%'+keyword+'%'), Transaction.status!='Finished').order_by(Transaction.customer_name).all()
    else:
        if user.active_sort == 'Alphabetical':
            transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.customer_name).all()
        else:
            transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.created_at.desc()).all()
    total_entries = Transaction.query.filter(Transaction.customer_name.ilike('%'+keyword+'%'), Transaction.status!='Finished').order_by(Transaction.customer_name).count()

    return jsonify(
        template = flask.render_template(
            'transactions_result.html',
            transactions = transactions,
            user=user
            ),
        total_entries = total_entries
        )


@app.route('/history/search',methods=['GET','POST'])
def search_history():
    data = flask.request.form.to_dict()
    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()

    if 'from_date' in data and 'to_date' in data:
        if parse_date(data['from_date']) > parse_date(data['to_date']):
            return jsonify(
                status='failed',
                message='"TO DATE should not be earlier than FROM DATE."'
                )

    if 'keyword' in data and data['keyword'] != '':
        if data['to_date'] == None or data['to_date'] == '' or data['to_date'] == data['from_date']:
            transactions = Transaction.query.filter(Transaction.customer_name.ilike('%'+data['keyword']+'%'), Transaction.status=='Finished', Transaction.date==data['from_date']).order_by(Transaction.created_at.desc()).all()
            total_entries = Transaction.query.filter(Transaction.customer_name.ilike('%'+data['keyword']+'%'), Transaction.status=='Finished', Transaction.date==data['from_date']).count()
        else:
            transactions = Transaction.query.filter(Transaction.customer_name.ilike('%'+data['keyword']+'%'), Transaction.status=='Finished').filter(Transaction.date >= data['from_date']).filter(Transaction.date <= data['to_date']).order_by(Transaction.created_at.desc()).all()
            total_entries = Transaction.query.filter(Transaction.customer_name.ilike('%'+data['keyword']+'%'), Transaction.status=='Finished').filter(Transaction.date >= data['from_date']).filter(Transaction.date <= data['to_date']).count()
    else:
        if data['to_date'] == None or data['to_date'] == '' or data['to_date'] == data['from_date']:
            transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status=='Finished', Transaction.date==data['from_date']).order_by(Transaction.created_at.desc()).all()
            total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status=='Finished', Transaction.date==data['from_date']).count()
        else:
            transactions = Transaction.query.filter(Transaction.status=='Finished').filter(Transaction.date >= data['from_date']).filter(Transaction.date <= data['to_date']).order_by(Transaction.created_at.desc())
            total_entries = Transaction.query.filter(Transaction.status=='Finished').filter(Transaction.date >= data['from_date']).filter(Transaction.date <= data['to_date']).count()
    
    total = '{0:.2f}'.format(sum(float(transaction.total) for transaction in transactions))

    return jsonify(
        status='success',
        template = flask.render_template(
            'history_result.html',
            transactions = transactions
            ),
        total_entries = total_entries,
        total = total,
        date=datetime.datetime.now().strftime('%B %d, %Y')
        )


@app.route('/transactions',methods=['GET','POST'])
def transactions():
    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()

    if user.active_sort == 'Alphabetical':
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.customer_name).all()
    else:
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.created_at.desc()).all()            
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').count()

    return jsonify(
        template = flask.render_template(
            'transactions.html',
            transactions = transactions,
            total_entries=total_entries,
            user=user
            )
        )


@app.route('/transaction',methods=['GET','POST'])
def open_transaction():
    transaction_id = flask.request.form.get('transaction_id')
    transaction = Transaction.query.filter_by(client_no=session['client_no'],id=transaction_id).first()
    transaction_items = TransactionItem.query.filter_by(transaction_id=transaction.id).all()

    return jsonify(
        body_template=flask.render_template(
            'transaction_info.html',
            transaction=transaction,
            transaction_items=transaction_items
            ),
        total=transaction.total
        )


@app.route('/transaction/process',methods=['GET','POST'])
def process_transaction():
    transaction_id = flask.request.form.get('transaction_id')
    transaction = Transaction.query.filter_by(client_no=session['client_no'],id=transaction_id).first()
    client = Client.query.filter_by(client_no=session['client_no']).first()

    transaction.status = 'Processing'
    transaction.process_date = datetime.datetime.now().strftime('%B %d, %Y')
    transaction.process_time = time.strftime("%I:%M%p")
    db.session.commit()

    return jsonify(
        status = 'success',
        template = flask.render_template('action_btn.html',entry=transaction)
        )


@app.route('/transaction/done',methods=['GET','POST'])
def done_transaction():
    transaction_id = flask.request.form.get('transaction_id')
    transaction = Transaction.query.filter_by(client_no=session['client_no'],id=transaction_id).first()
    client = Client.query.filter_by(client_no=session['client_no']).first()

    if send_email(transaction.customer_email,transaction.customer_name):
        transaction.status = 'Done'
        transaction.done_date = datetime.datetime.now().strftime('%B %d, %Y')
        transaction.done_time = time.strftime("%I:%M%p")
        db.session.commit()
        return jsonify(
            status = 'success',
            template = flask.render_template('action_btn.html',entry=transaction)
            )
    return jsonify(
        status = 'failed',
        message= 'Something went wrong. Please try again.'
        )
        

@app.route('/transaction/pickup',methods=['GET','POST'])
def pickup_transaction():
    transaction_id = flask.request.form.get('transaction_id')
    transaction = Transaction.query.filter_by(client_no=session['client_no'],id=transaction_id).first()
    client = Client.query.filter_by(client_no=session['client_no']).first()

    transaction.status = 'Finished'
    transaction.pickup_date = datetime.datetime.now().strftime('%B %d, %Y')
    transaction.pickup_time = time.strftime("%I:%M%p")
    db.session.commit()
   
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').count()

    return jsonify(
        status = 'success',
        total_entries = total_entries
        )
    

@app.route('/transaction/save',methods=['GET','POST'])
def save_transaction():
    data = flask.request.form.to_dict()

    transaction = Transaction(
        client_no=session['client_no'],
        date=datetime.datetime.now().strftime('%B %d, %Y'),
        time=time.strftime("%I:%M%p"),
        month_year=datetime.datetime.now().strftime('%B %Y'),
        status='Pending',
        cashier_id=session['user_id'],
        cashier_name=session['user_name'].title(),
        customer_name=data['customer_name'].title(),
        customer_msisdn=data['customer_msisdn'],
        customer_email=data['customer_email'],
        total=data['total'],
        notes=data['notes'],
        additional_charge='{0:.2f}'.format(float(data['additional_charge'])),
        created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
        )

    db.session.add(transaction)
    db.session.commit()

    if data['customer_msisdn'] or data['customer_msisdn'] != '':
        customer = Customer.query.filter_by(msisdn=data['customer_msisdn']).first()
        if not customer or customer == None:
            customer = Customer(
                name=data['customer_name'].title(),
                email=data['customer_email'],
                msisdn=data['customer_msisdn'],
                created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
                )
            db.session.add(customer)
        customer.name=data['customer_name'].title()
        customer.email=data['customer_email']
        customer.msisdn=data['customer_msisdn']
        db.session.commit()

    services = Service.query.filter_by(client_no=session['client_no']).all()
    for service in services:
        quantity = data[str(service.id)]
        if quantity != '0' and quantity != '0.0':
            price = float(quantity) * float(service.price)
            transaction_item = TransactionItem(
                client_no=session['client_no'],
                transaction_id=transaction.id,
                service_id=service.id,
                service_name=service.name,
                quantity=str(quantity),
                price=service.price,
                total='{0:.2f}'.format(price)
                )
            db.session.add(transaction_item)
            db.session.commit()

    client = Client.query.filter_by(client_no=session['client_no']).first()
    bill = Bill.query.filter_by(date=datetime.datetime.now().strftime('%B, %Y'), client_no=session['client_no']).first()

    if not bill or bill == None:
        bill = Bill(
            date=datetime.datetime.now().strftime('%B, %Y'),
            year=datetime.datetime.now().strftime('%Y'),
            client_no=session['client_no'],
            created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f'),
            transactions=0,
            price='0',
            )
        db.session.add(bill)
        db.session.commit()

    bill.price = '{0:.2f}'.format(float(bill.price) + float(client.pricing))
    bill.transactions += 1
    db.session.commit()

    user = AdminUser.query.filter_by(client_no=session['client_no'],id=session['user_id']).first()

    if user.active_sort == 'Alphabetical':
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.customer_name).all()
    else:
        transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').order_by(Transaction.created_at.desc()).all()            
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status!='Finished').count()

    return jsonify(
        template = flask.render_template(
            'transactions.html',
            transactions = transactions,
            total_entries=total_entries,
            user=user
            )
        )


@app.route('/usage',methods=['GET','POST'])
def usage():
    bills = Bill.query.filter_by(client_no=session['client_no'], year=datetime.datetime.now().strftime('%Y')).order_by(Bill.created_at.desc())

    return jsonify(
        template = flask.render_template(
            'usage.html',
            bills = bills,
            year = datetime.datetime.now().strftime('%Y')
            )
        )


@app.route('/bill',methods=['GET','POST'])
def bill_info():
    session['bill_id'] = flask.request.form.get('bill_id')
    bill = Bill.query.filter_by(client_no=session['client_no'], id=session['bill_id']).first()

    return jsonify(
        template = flask.render_template(
            'bill_info.html',
            bill = bill
            )
        )


@app.route('/history',methods=['GET','POST'])
def history():
    transactions = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status=='Finished', Transaction.date == datetime.datetime.now().strftime('%B %d, %Y')).order_by(Transaction.created_at.desc()).all()
    total_entries = Transaction.query.filter(Transaction.client_no==session['client_no'], Transaction.status=='Finished', Transaction.date == datetime.datetime.now().strftime('%B %d, %Y')).count()

    total = '{0:.2f}'.format(sum(float(transaction.total) for transaction in transactions))

    year = datetime.datetime.now().strftime('%Y')

    january_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='January %s' % year).all()
    january = '{0:.2f}'.format(sum(float(transaction.total) for transaction in january_transactions))

    february_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='February %s' % year).all()
    february = '{0:.2f}'.format(sum(float(transaction.total) for transaction in february_transactions))

    march_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='March %s' % year).all()
    march = '{0:.2f}'.format(sum(float(transaction.total) for transaction in march_transactions))

    april_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='April %s' % year).all()
    april = '{0:.2f}'.format(sum(float(transaction.total) for transaction in april_transactions))

    may_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='May %s' % year).all()
    may = '{0:.2f}'.format(sum(float(transaction.total) for transaction in may_transactions))

    june_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='June %s' % year).all()
    june = '{0:.2f}'.format(sum(float(transaction.total) for transaction in june_transactions))

    july_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='July %s' % year).all()
    july = '{0:.2f}'.format(sum(float(transaction.total) for transaction in july_transactions))

    august_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='August %s' % year).all()
    august = '{0:.2f}'.format(sum(float(transaction.total) for transaction in august_transactions))

    september_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='September %s' % year).all()
    september = '{0:.2f}'.format(sum(float(transaction.total) for transaction in september_transactions))

    october_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='October %s' % year).all()
    october = '{0:.2f}'.format(sum(float(transaction.total) for transaction in october_transactions))

    november_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='November %s' % year).all()
    november = '{0:.2f}'.format(sum(float(transaction.total) for transaction in november_transactions))

    december_transactions = Transaction.query.filter_by(client_no=session['client_no'], month_year='December %s' % year).all()
    december = '{0:.2f}'.format(sum(float(transaction.total) for transaction in december_transactions))

    return jsonify(
        template = flask.render_template(
            'history.html',
            transactions = transactions,
            total_entries = total_entries,
            total = total,
            january=january,
            february=february,
            march=march,
            april=april,
            may=may,
            june=june,
            july=july,
            august=august,
            september=september,
            october=october,
            november=november,
            december=december
            ),
        date=datetime.datetime.now().strftime('%B %d, %Y')
        )


@app.route('/users',methods=['GET','POST'])
def users():
    users = AdminUser.query.filter_by(client_no=session['client_no']).order_by(AdminUser.name)
    total_entries = AdminUser.query.filter_by(client_no=session['client_no']).count()

    return jsonify(
        template = flask.render_template(
            'users.html',
            users = users,
            total_entries = total_entries,
            )
        )


@app.route('/services',methods=['GET','POST'])
def services():
    services = Service.query.filter_by(client_no=session['client_no']).order_by(Service.name)
    total_entries = Service.query.filter_by(client_no=session['client_no']).count()

    service_names = []
    service_frequencies = []

    for service in services:
        service_names.append(service.name)
        count = TransactionItem.query.filter_by(client_no=session['client_no'],service_id=service.id).count()
        service_frequencies.append(count)

    return jsonify(
        template = flask.render_template(
            'services.html',
            services = services,
            total_entries = total_entries,
            service_frequencies = service_frequencies,
            service_names = service_names
            ),
        service_frequencies = service_frequencies,
        service_names = service_names
        )


@app.route('/service/save',methods=['GET','POST'])
def save_service():
    data = flask.request.form.to_dict()

    service = Service(
        client_no=session['client_no'],
        name=data['service_name'].title(),
        price='{0:.2f}'.format(float(data['service_price']))
        )

    db.session.add(service)
    db.session.commit()

    services = Service.query.filter_by(client_no=session['client_no']).order_by(Service.name)
    total_entries = Service.query.filter_by(client_no=session['client_no']).count()

    for service in services:
        service_names.append(service.name)
        count = TransactionItem.query.filter_by(client_no=session['client_no'],service_id=service.id).count()
        service_frequencies.append(count)

    return jsonify(
        template = flask.render_template(
            'services_result.html',
            services = services,
            total_entries = total_entries
            ),
        transaction_template = flask.render_template(
            'transaction_service.html',
            services = services
            ),
        total_entries = total_entries,
        service_names = service_names,
        service_frequencies = service_frequencies
        )


@app.route('/service/edit',methods=['GET','POST'])
def edit_service():
    data = flask.request.form.to_dict()

    service = Service.query.filter_by(id=session['service_id']).first()
    service.name = data['service_name']
    service.price = '{0:.2f}'.format(float(data['service_price']))
    db.session.commit()

    services = Service.query.filter_by(client_no=session['client_no']).order_by(Service.name)
    total_entries = Service.query.filter_by(client_no=session['client_no']).count()

    for service in services:
        service_names.append(service.name)
        count = TransactionItem.query.filter_by(client_no=session['client_no'],service_id=service.id).count()
        service_frequencies.append(count)

    return jsonify(
        template = flask.render_template(
            'services_result.html',
            services = services,
            total_entries = total_entries
            ),
        transaction_template = flask.render_template(
            'transaction_service.html',
            services = services
            ),
        message = 'Changes saved.',
        total_entries = total_entries,
        service_names = service_names,
        service_frequencies = service_frequencies
        )


@app.route('/service',methods=['GET','POST'])
def service_info():
    data = flask.request.form.to_dict()
    session['service_id'] = data['service_id']
    service = Service.query.filter_by(id=session['service_id']).first()

    return jsonify(
        template = flask.render_template(
            'service_info.html',
            service = service
            )
        )


@app.route('/user',methods=['GET','POST'])
def user_info():
    data = flask.request.form.to_dict()
    session['open_user_id'] = data['user_id']
    user = AdminUser.query.filter_by(id=session['open_user_id']).first()

    return jsonify(
        template = flask.render_template(
            'user_info.html',
            user = user,
            permissions = user.permissions.split(","),
            current_user_id = session['user_id']
            )
        )


@app.route('/user/edit',methods=['GET','POST'])
def edit_user():
    data = flask.request.form.to_dict()
    permissions = flask.request.form.getlist('edit_permissions[]')
    user = AdminUser.query.filter_by(id=session['open_user_id']).first()

    user.name = data['name'].title()
    user.email = data['email']
    user.permissions = ",".join(permissions)

    db.session.commit()

    users = AdminUser.query.filter_by(client_no=session['client_no']).order_by(AdminUser.name)
    total_entries = AdminUser.query.filter_by(client_no=session['client_no']).count()

    return jsonify(
        template = flask.render_template(
            'users.html',
            users = users,
            total_entries = total_entries,
            ),
        message = 'Changes saved.'
        )


@app.route('/user/edit/logged_in',methods=['GET','POST'])
def edit_logged_user():
    data = flask.request.form.to_dict()
    user = AdminUser.query.filter_by(id=session['user_id']).first()

    user.name = data['name'].title()
    user.email = data['email']

    db.session.commit()

    return jsonify(
        status = 'success',
        message = 'Changes saved.'
        )


@app.route('/user/password/reset',methods=['GET','POST'])
def reset_user_password():
    password = flask.request.form.get('password')
    user = AdminUser.query.filter_by(id=session['open_user_id']).first()
    user.password = generate_password_hash(password)
    user.temp_pw = generate_password_hash(password)
    db.session.commit()
    return jsonify(status='success', message=''),201


@app.route('/user/password/reset/logged_in',methods=['GET','POST'])
def reset_logged_in_user_password():
    password = flask.request.form.get('password')
    user = AdminUser.query.filter_by(id=session['user_id']).first()
    user.password = generate_password_hash(password)
    db.session.commit()
    return jsonify(status='success', message=''),201


@app.route('/user/password/save',methods=['GET','POST'])
def save_password():
    password = flask.request.form.get('password')
    user = AdminUser.query.filter_by(id=session['user_id']).first()
    if check_password_hash(user.password, password) == True:
        return jsonify(status='failed', message='The password you entered is the same as your temporary password, please enter a different one.')
    user.password = generate_password_hash(password)
    db.session.commit()
    session['change_pw'] = 'no'
    return jsonify(status='success', message='Password successfully changed.')


@app.route('/user/add',methods=['GET','POST'])
def add_user():
    data = flask.request.form.to_dict()
    permissions = flask.request.form.getlist('permissions[]')

    new_user = AdminUser(
        client_no=session['client_no'],
        email=data['email'],
        password=generate_password_hash(data['temp_pw']),
        temp_pw=generate_password_hash(data['temp_pw']),
        name=data['name'].title(),
        permissions=",".join(permissions),
        added_by_id=session['user_id'],
        added_by_name=session['user_name'],
        join_date=datetime.datetime.now().strftime('%B %d, %Y'),
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        )

    db.session.add(new_user)
    db.session.commit()

    users = AdminUser.query.filter_by(client_no=session['client_no']).order_by(AdminUser.name)
    total_entries = AdminUser.query.filter_by(client_no=session['client_no']).count()

    return jsonify(
        template = flask.render_template(
            'users.html',
            users = users,
            total_entries = total_entries,
            )
        )


@app.route('/user/delete',methods=['GET','POST'])
def delete_user():
    user = AdminUser.query.filter_by(id=session['open_user_id']).first()
    db.session.delete(user)
    db.session.commit()

    users = AdminUser.query.filter_by(client_no=session['client_no']).order_by(AdminUser.name)
    total_entries = AdminUser.query.filter_by(client_no=session['client_no']).count()

    return jsonify(
        template = flask.render_template(
            'users.html',
            users = users,
            total_entries = total_entries,
            )
        )


@app.route('/service/delete',methods=['GET','POST'])
def delete_service():
    service = Service.query.filter_by(id=session['service_id']).first()
    db.session.delete(service)
    db.session.commit()

    services = Service.query.filter_by(client_no=session['client_no']).order_by(Service.name)
    total_entries = Service.query.filter_by(client_no=session['client_no']).count()

    service_names = []
    service_frequencies = []

    for service in services:
        service_names.append(service.name)
        count = TransactionItem.query.filter_by(client_no=session['client_no'],service_id=service.id).count()
        service_frequencies.append(count)

    return jsonify(
        template = flask.render_template(
            'services.html',
            services = services,
            total_entries = total_entries,
            service_frequencies = service_frequencies,
            service_names = service_names
            ),
        transaction_template = flask.render_template(
            'transaction_service.html',
            services = services
            ),
        service_frequencies = service_frequencies,
        service_names = service_names
        )


@app.route('/account',methods=['GET','POST'])
def account():
    user = AdminUser.query.filter_by(id=session['user_id']).first()
    return jsonify(
        template = flask.render_template(
            'account.html',
            user = user,
            permissions = user.permissions.split(",")
            )
        )


@app.route('/login',methods=['GET','POST'])
@nocache
def user_login():
    if session:
        return redirect('/')
    return flask.render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect('/login')


@app.route('/states',methods=['GET','POST'])
def states():
    customers = Customer.query.all()
    customer_names = []
    for entry in customers:
        customer_names.append(entry.name)
    return jsonify(
        customer_names = customer_names
        )


@app.route('/user/authenticate',methods=['GET','POST'])
def authenticate_user():
    data = flask.request.form.to_dict()
    user = AdminUser.query.filter_by(email=data['user_email']).first()
    if not user or user == None:
        return jsonify(status='failed', error='Invalid username.')
    if check_password_hash(user.password, data['user_password']) == False:
        return jsonify(status='failed', error='Invalid password.')

    if check_password_hash(user.temp_pw, data['user_password']) == True:
        session['change_pw'] = 'yes'
    else:
        session['change_pw'] = 'no'

    client = Client.query.filter_by(client_no=user.client_no).first()
    session['user_name'] = user.name
    session['user_id'] = user.id
    session['client_no'] = client.client_no
    session['client_name'] = client.name
    return jsonify(status='success', error=''),200


@app.route('/bill/receipt/upload', methods=['GET', 'POST'])
def upload_receipt():
    file = flask.request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    bill = Bill.query.filter_by(id=session['bill_id'], client_no=session['client_no']).first()
    bill.receipt_path = 'static/receipts/%s' % filename
    db.session.commit()

    return jsonify(
        template = flask.render_template('bill_info.html', bill=bill)
        ),201


@app.route('/db/rebuild',methods=['GET','POST'])
def rebuild_database():
    db.drop_all()
    db.create_all()

    client = Client(
        client_no='bubble',
        name='E-Laba',
        app_id='EGXMuB5eEgCMLTKxExieqkCGeGeGuBon',
        app_secret='f3e1ab30e23ea7a58105f058318785ae236378d1d9ebac58fe8b42e1e239e1c3',
        passphrase='24BUubukMQ',
        shortcode='21588479',
        pricing='5',
        created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        )

    user = AdminUser(
        client_no='bubble',
        email='stevenbuenafe',
        password=generate_password_hash('password123'),
        temp_pw=generate_password_hash('password123'),
        name='Sample Cashier',
        role='Administrator',
        permissions='Services,Users',
        active_sort='Alphabetical',
        join_date=datetime.datetime.now().strftime('%B %d, %Y'),
        created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
        )

    transaction = Transaction(
        client_no='bubble',
        date=datetime.datetime.now().strftime('%B %d, %Y'),
        time=time.strftime("%I:%M%p"),
        month_year=datetime.datetime.now().strftime('%B %Y'),
        status='Pending',
        cashier_id=1,
        cashier_name='Sample Cashier',
        customer_name='Steven Buenafe',
        customer_msisdn='09176214704',
        customer_email='barcelona.jasperoliver@gmail.com',
        total='4000.00',
        notes='Sample notes.',
        created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
        )

    transaction1 = Transaction(
        client_no='bubble',
        date=datetime.datetime.now().strftime('%B %d, %Y'),
        time=time.strftime("%I:%M%p"),
        month_year=datetime.datetime.now().strftime('%B %Y'),
        status='Processing',
        cashier_id=1,
        cashier_name='Sample Cashier',
        customer_name='Sample Customer',
        customer_msisdn='09176214704',
        customer_email='barcelona.jasperoliver@gmail.com',
        total='4000.00',
        created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
        )

    service = Service(
        client_no='bubble',
        name='Wash & Dry',
        price='100.00'
        )

    service1 = Service(
        client_no='bubble',
        name='Fabric Conditioner',
        price='15.00'
        )

    service2 = Service(
        client_no='bubble',
        name='Fold',
        price='20.00'
        )

    transaction_item = TransactionItem(
        client_no='bubble',
        transaction_id=1,
        service_id=1,
        service_name='Wash & Dry',
        quantity='1',
        price='100',
        total='100'
        )

    report = Report(
        client_no='bubble',
        name='Report Sample',
        report_type='Sales Report',
        generated_by='Sample Cashier',
        generated_by_id=1,
        date=datetime.datetime.now().strftime('%B %d, %Y'),
        time=time.strftime("%I:%M%p"),
        created_at=datetime.datetime.now().strftime('%Y-%m`-%d %H:%M:%S:%f')
        )

    db.session.add(client)
    db.session.add(user)
    # db.session.add(transaction)
    # db.session.add(transaction1)
    # db.session.add(transaction2)
    # db.session.add(transaction3)
    db.session.add(service)
    db.session.add(service1)
    db.session.add(service2)
    db.session.add(transaction_item)
    db.session.add(report)
    db.session.commit()

    return jsonify(
        status='success',
        message='Database rebuilt successfully'
        ),201


if __name__ == '__main__':
    app.run(port=5000,debug=True,host='0.0.0.0')
    # port=int(os.environ['PORT']), host='0.0.0.0'