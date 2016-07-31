import sys
from sqlalchemy import Column, ForeignKey, Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()

class User(Base):
    __tablename__='user'
    name=Column(
        String(80), nullable=False
    )
    id=Column(
        Integer, primary_key = True
    )
    email=Column(
        String(80), nullable=False
    )
    picture = Column(String(250))
    
class Restaurant(Base):
    __tablename__='restaurant'
    name=Column(
        String(80), nullable=False
    )
    id=Column(
        Integer, primary_key = True
    )
    user=relationship(User)
    user_id=Column(
        Integer, ForeignKey('user.id')
    )
    
    @property
    def serialRes(self):
        return {
            'name':self.name,
            'id':self.id,
        }

class MenuItem(Base):
    __tablename__='menu_item'
    user=relationship(User)
    restaurant= relationship(Restaurant)
    name=Column(
        String(80),nullable= False
    )
    id=Column(
        Integer,primary_key= True
    )
    course= Column(
        String(250)
    )
    description= Column(
        String(250)
    )
    price = Column(
        String(8)
    )
    restaurant_id= Column(
        Integer, ForeignKey('restaurant.id')
    )
    user_id=Column(
        Integer, ForeignKey('user.id')
    )
    
    @property
    def serialize(self):
        return {
            'name': self.name,
            'description': self.description, 
            'id': self.id,
            'price': self.price,
            'course': self.course,
        }
    
#insert at the end of file
engine= create_engine(
    'sqlite:///restaurantmenu.db')
Base.metadata.create_all(engine)
print 'done'