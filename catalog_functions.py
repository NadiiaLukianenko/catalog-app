from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
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
import random, string

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "CatalogApp"
app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

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
        response = make_response(json.dumps("Token's user ID "\
                        "doesn't match given user ID"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # If access token is valid for app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID "\
                         "doesn't match app's"), 401)
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    if 'access_token' not in login_session:
        '''
        print login_session['access_token']
        access_token = login_session['access_token']
        print 'In gdisconnect access token is %s', access_token
        print 'User name is: '
        print login_session['username']
        if login_session['access_token'] is None:
        print 'Access Token is None'
        '''
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
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
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/<category_name>.JSON')
def itemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])

# JSON endpoint
@app.route('/catalog.JSON')
def catalogJSON():
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])

@app.route('/')
def catalog():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.creationDateTime.desc()).limit(10)
    dict = {}
    for i in categories:
        category = session.query(Category).filter_by(id=i.id).one()
        dict[i.id] = category.name
    return render_template('catalog.html', login_session=login_session,
                           categories=categories, items=items, dict=dict)

@app.route('/catalog/<category_name>/Items')
def catalogSelected(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template(
        'catalog_selected.html', categories=categories,
        login_session=login_session, category=category,
        items=items, category_name=category_name)

@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category_id=category.id).one()
    return render_template('item.html',category=category,
                item=item, login_session=login_session)

@app.route('/catalog/New', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['item'], description=request.form[
                    'description'], category_id=request.form['category'])
        session.add(newItem)
        session.commit()
        category_name = session.query(Category).\
            filter_by(id=request.form['category']).one().name
        return redirect(url_for('catalogSelected',
                                category_name=category_name))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', login_session=login_session,
                              categories=categories)


@app.route('/catalog/<category_name>/<item_name>/Edit',
           methods=['GET', 'POST'])
def editItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
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
        session.add(editedItem)
        session.commit()
        return redirect(url_for('catalogSelected', category_name=category_name))
    else:
        return render_template('edit_item.html',
                category_name=category.name,
                item=editedItem,
                categories=categories,
                login_session=login_session)

@app.route('/catalog/<category_name>/<item_name>/Delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    itemToDelete = session.query(Item).filter_by(name=item_name,
                category_id=category.id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('catalog', category_name=category_name))
    else:
        return render_template('delete_item.html', item=itemToDelete,
                    login_session=login_session, category=category)


if __name__ == '__main__':
    app.secret_key = 'bPpAwqouObw5aCWYAhgSRbVn'
    #app.config['SESSION_TYPE'] = 'filesystem'

    app.debug = True
    app.run(host='0.0.0.0', port=8080)