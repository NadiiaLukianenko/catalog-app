'''

'''
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Numeric, \
    Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy import create_engine

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    items = relationship("Item", backref="item")

class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(800))
    creationDateTime = Column(DateTime)
    picture = Column(String)
    category = relationship(Category)
    category_id = Column(Integer, ForeignKey('category.id'))

    @property
    def serialize(self):
       """Return in serialized format
       """
       return {
           'id' : self.id,
           'name' : self.name,
           'description' : self.description,
           'creationDateTime' : self.creationDateTime,
           'category_id' : self.category_id
       }

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    login = Column(String(80), nullable=False)
    password = Column(String(80), nullable=False)

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)