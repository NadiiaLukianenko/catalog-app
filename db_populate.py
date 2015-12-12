from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog_functions import Base, Category, Item
#from flask.ext.sqlalchemy import SQLAlchemy
import datetime


engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

#Add Categories
category1 = Category(id = 1,
                     name = "Work",
                     description = "Work goals")
session.add(category1)

category2 = Category(id = 2,
                     name = "Sport",
                     description = "Sports")
session.add(category2)

category5 = Category(id = 3,
                     name = "Hobbies",
                     description = "All hobbies")
session.add(category5)

category3 = Category(id = 4,
                     name = "Languages",
                     description = "All languages to learn")
session.add(category3)

category4 = Category(id = 5,
                     name = "Education",
                     description = "All courses")
session.add(category4)

category5 = Category(id = 6,
                     name = "Finance",
                     description = "Finance goals")
session.add(category5)
session.commit()

#Add items
item1 = Item(id = 1,
             name = "Automation testing",
             description = "ToDo: JUnit, Selenium",
             creationDateTime = datetime.datetime.now(),
             category_id = 1)
session.add(item1)

item2 = Item(id = 2,
             name = "Finance",
             description = "ToDo: read Security Operations",
             creationDateTime = datetime.datetime.now(),
             category_id = 1)
session.add(item2)

item3 = Item(id = 3,
             name = "Yoga",
             description = "ToDo: prepare sequences for training",
             creationDateTime = datetime.datetime.now(),
             category_id = 2)
session.add(item3)

item4 = Item(id = 4,
             name = "RockClimbing",
             description = "ToDo: Trainings 2 times per week",
             creationDateTime = datetime.datetime.now(),
             category_id = 2)
session.add(item4)

item5 = Item(id = 5,
             name = "Photography",
             description = "ToDo: Prepare album",
             creationDateTime = datetime.datetime.now(),
             category_id = 3)
session.add(item5)

item6 = Item(id = 6,
             name = "English",
             description = "ToDo: prepare and pass IELTS",
             creationDateTime = datetime.datetime.now(),
             category_id = 4)
session.add(item6)

item7 = Item(id = 7,
             name = "German",
             description = "ToDo: roll the course",
             creationDateTime = datetime.datetime.now(),
             category_id = 4)
session.add(item7)

item8 = Item(id = 8,
             name = "Udacity",
             description = "ToDo: complete course",
             creationDateTime = datetime.datetime.now(),
             category_id = 5)
session.add(item8)

session.commit()
