"""
catalog_functions.py: main functionality for Catalog App:
    - authorization - Login/Logout
    - view categories
    - view/create/update/delete items
"""
from flask import Flask, render_template, request, redirect, url_for, jsonify,\
    flash, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import random
import string
from xml.etree.ElementTree import Element, SubElement, tostring, dump
from flask.ext.responses import xml_response
from werkzeug import secure_filename
import os
import datetime
from flask import send_from_directory
import pdb

#pdb.set_trace()

UPLOAD_FOLDER = 'image/'
ALLOWED_EXTENSIONS = set(['png','jpg','jpeg','gif'])
CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "CatalogApp"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog/image/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




def xmlCategories(categories_xml,i):
        category_xml = SubElement(categories_xml, 'category',
                                  {
                                      'id': str(i.id),
                                      'name': i.name,
                                      'description': i.description,
                                   }
                                  )
        return category_xml


def xmlItems(items_xml,j):
    SubElement(items_xml, 'item',
                            {
                                'id': str(j.id),
                                'name': j.name,
                                'description': j.description,
                                'creationDateTime': str(j.creationDateTime)
                            })


@app.route('/catalog.XML')
def returnXml():
    categories = session.query(Category).all()
    root = Element('catalog')
    categories_xml = SubElement(root, 'categories')
    for i in categories:
        category_xml = xmlCategories(categories_xml,i)
        items = session.query(Item).filter_by(category_id=i.id).all()
        items_xml = SubElement(category_xml, 'items')
        for j in items:
            xmlItems(items_xml,j)

    return xml_response(tostring(root, encoding="us-ascii", method="xml"),
                headers={'Content-Type': 'application/xml; charset=utf-8;'})


@app.route('/catalog/<category_name>.XML')
def returnXmlCategory(category_name):
    category = session.query(Category).filter_by(name=category_name).all()
    root = Element('catalog')
    for i in category:
        category_xml = xmlCategories(root,i)
        items = session.query(Item).filter_by(category_id=i.id).all()
        items_xml = SubElement(category_xml, 'items')
        for j in items:
            xmlItems(items_xml,j)

    return xml_response(tostring(root, encoding="us-ascii", method="xml"),
                headers={'Content-Type': 'application/xml; charset=utf-8;'})


def login_required(func):
    def func_wrapper():
        if 'username' not in login_session:
            return redirect('/login')
    return func_wrapper


@app.route('/login')
def showLogin():
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade '
                                            'the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If error in access token - stop
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-type'] = 'application/json'

    # If access token is used for intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't "
                                            "match given user ID"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # If access token is valid for app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't "
                                            "match app's"), 401)
        print "Token's client ID doesn't match app's"
        response.headers['Content-type'] = 'application/json'
        return response

    # If User is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    if 'access_token' not in login_session:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % \
          login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash(response)
        return redirect('/')
    else:
        response = make_response(json.dumps('Failed to revoke token '
                                            'for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/<category_name>.JSON')
def itemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog.JSON')
def catalogJSON():
    """
    JSON endpoint
    """
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])


@app.route('/')
def catalog():
    """
    catalog returns all categories and lists items ascending by datetime
    """
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.creationDateTime.asc()).\
        limit(10)
    dict = {}
    for i in categories:
        category = session.query(Category).filter_by(id=i.id).one()
        dict[i.id] = category.name
    return render_template('catalog.html', login_session=login_session,
                           categories=categories, items=items, dict=dict)


@app.route('/catalog/<category_name>/Items')
def catalogSelected(category_name):
    """
    catalogSelected fetches and returns items from selected category
    Args:
        category_name: name of category
    """
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template(
        'catalog_selected.html', categories=categories,
        login_session=login_session, category=category,
        items=items, category_name=category_name)


@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    """
    item fetches and returns item data
    Args:
        category_name: name of category
        item_name: name of item in the category
    """
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category_id=category.id).one()
    return render_template('item.html', category=category, item=item,
                           login_session=login_session)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def saveFile(file):
    filename = secure_filename(file.filename)
    filename = ''.join([filename.rsplit('.',1)[0],
                    str(datetime.datetime.now().microsecond),'.',
                    filename.rsplit('.',1)[1]])
    os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename

def deleteFile(file):
    try:
        if len(file) > 4:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],file))
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)

def updateFile(old_file, new_file):
    '''
    :param old_file: path
    :param new_file: object
    :return: new file name
    '''
    deleteFile(old_file)
    return saveFile(new_file)


@login_required
@app.route('/catalog/New', methods=['GET', 'POST'])
def newItem():
    """
    newItem adds new item if user is logged in
    """
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = saveFile(file)
            newItem = Item(name=request.form['item'], description=request.form[
                    'description'], category_id=request.form['category'],
                    image=filename, creationDateTime=datetime.datetime.now())
            session.add(newItem)
            session.commit()
            category_name = session.query(Category).\
            filter_by(id=request.form['category']).one().name

            return redirect(url_for('catalogSelected',
                            category_name=category_name, filename=filename))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', login_session=login_session,
                               categories=categories)


@login_required
@app.route('/catalog/<category_name>/<item_name>/Edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    """
    editItem edits item if user is logged in
    Args:
        category_name: name of category
        item_name: name of item in the category
    """
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    category_id = category.id
    editedItem = session.query(Item).filter_by(name=item_name,
                                               category_id=category_id).one()
    if request.method == 'POST':
        if request.form['item']:
            editedItem.name = request.form['item']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        if request.files['file'] and allowed_file(request.files['file'].filename):
            editedItem.image = updateFile(editedItem.image,
                                          request.files['file'])
        session.add(editedItem)
        session.commit()
        return redirect(url_for('catalogSelected',
                                category_name=category_name))
    else:
        return render_template('edit_item.html', category_name=category.name,
                               item=editedItem, categories=categories,
                               login_session=login_session)


@login_required
@app.route('/catalog/<category_name>/<item_name>/Delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    """
    deleteItem deletes item if user is logged in
    Args:
        category_name: name of category
        item_name: name of item in the category
    """
    category = session.query(Category).filter_by(name=category_name).one()
    itemToDelete = session.query(Item).filter_by(name=item_name,
                                                 category_id=category.id).one()
    if request.method == 'POST':
        deleteFile(itemToDelete.image)
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('catalog', category_name=category_name))
    else:
        return render_template('delete_item.html', item=itemToDelete,
                               login_session=login_session, category=category)


if __name__ == '__main__':
    app.secret_key = 'bPpAwqouObw5aCWYAhgSRbVn'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
