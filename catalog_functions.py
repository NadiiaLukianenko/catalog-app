from flask import Flask, render_template, request, redirect, url_for, jsonify
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

CLIENT_ID = json.loads(open('client_secret.json',
                            'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    if 'username' not in login_session:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
        login_session['state'] = state
        return render_template('login.html', state=state)
    else:
        return redirect(url_for('catalog'))

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
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
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected'), 200)
        response.headers['Content-Type'] = 'application/json'

    # Strore access token in the session for later use
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' "style = width:300px;height:300px;border-radius:150px;' \
              '-webkit-border-radius:150px;-moz-border-radius:150px;"> '
    return output

@app.route("/gdisconnect")
def gdisconnect():
    # Disconnect if user is connected
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # Token was invalid
        response = make_response(json.dumps('Failed to revoke token '
                                            'for given user'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog/<category_name>.JSON')
def itemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])


# ADD JSON ENDPOINT HERE
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
    return render_template(
        'catalog.html', categories=categories, items=items, dict=dict)

@app.route('/catalog/<category_name>/Items')
def catalogSelected(category_name):
    categories = session.query(Category).all()
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template(
        'catalog_selected.html', categories=categories, category=category,
        items=items, category_name=category_name)

@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category_id=category.id).one()
    return render_template(
        'item.html',category=category, item=item)

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
        return redirect(url_for('catalogSelected', category_name=category_name))
    else:
        categories = session.query(Category).all()
        return render_template('add_item.html', categories=categories)


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
                categories=categories)

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
                               category=category)


if __name__ == '__main__':
    app.secret_key = 'bPpAwqouObw5aCWYAhgSRbVn'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.debug = True
    app.run(host='0.0.0.0', port=8080)