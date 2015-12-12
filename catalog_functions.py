from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login/')
def login():
    pass


@app.route('/catalog/<category_name>/JSON')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(
        category_id=category.id).all()
    return jsonify(Items=[i.serialize for i in items])


# ADD JSON ENDPOINT HERE
@app.route('/catalog/<category_name>/JSON')
def itemJSON(category_name, item_name):
    category = session.query(Category).\
        filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
        category_id=category.id).one()
    return jsonify(Item=item.serialize)


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
    category = session.query(Category).filter_by(name=category_name).one()
    editedItem = session.query(Item).filter_by(name=item_name,
                category_id=category.id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category']:
            editedItem.category = request.form['category']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('catalogSelected', category_name=category_name))
    else:
        return render_template('edit_item.html', category_name=category_name,
                               item_name=item_name, item=editedItem,
                               category=category)


@app.route('/catalog/<category_name>/<item_name>/Delete',
           methods=['GET', 'POST'])
def deleteItem(category_name, item_name):
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
    app.debug = True
    app.run(host='0.0.0.0', port=8080)