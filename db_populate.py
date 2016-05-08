"""
db_populate.py:
    populate database with initial data
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from __init__1 import Base, Category, Item
from datetime import datetime
import json

engine = create_engine('postgresql://catalog:catalog@localhost/catalogdb')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def loadJson(source):
    """
    loadJson loads data from source
    Args:
        source: data source
    """
    with open(source) as data_to_load:
        data = json.load(data_to_load)
        for category in data["Category"]:
            session.add(Category(id=category["id"],
                                 name=category["name"],
                                 description=category["description"]))
            for item in category["Items"]:
                session.add(Item(id=item["id"],
                                 name=item["name"],
                                 description=item["description"],
                                 creationDateTime=datetime.strptime(
                                     item["creationDateTime"],
                                     "%Y-%m-%d %H:%M:%S.%f"),
                                 image=item["image"],
                                 category_id=item["category_id"]))
    session.commit()


if __name__ == '__main__':
    loadJson('static/initialcatalog.json')

