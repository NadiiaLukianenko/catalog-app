"""
database_setup.py: create database for Catalog App
"""
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    items = relationship("Item", backref="item")

    @property
    def serialize(self):
        """ Return in serialized format
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'Items': self.serialize_one2many
        }

    @property
    def serialize_one2many(self):
        """ Return in serialized format
        """
        return [item.serialize for item in self.items]


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(800))
    creationDateTime = Column(DateTime)
    image = Column(String(250))
    category = relationship(Category)
    category_id = Column(Integer, ForeignKey('category.id'))

    @property
    def serialize(self):
        """Return in serialized format
        """
        return {
           'id': self.id,
           'name': self.name,
           'description': self.description,
           'creationDateTime': str(self.creationDateTime),
           'image': self.image,
           'category_id': self.category_id
        }

engine = create_engine('postgresql://catalog:catalog@localhost/catalogdb')

Base.metadata.create_all(engine)
