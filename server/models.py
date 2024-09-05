from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, ForeignKey, Column, Integer, String, Date
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.declarative import declarative_base
from datetime import date

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)



class Episode(db.Model, SerializerMixin):
    __tablename__ = 'episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    date = db.Column(db.String)  # This must be a Date type
    number = db.Column(db.Integer)
    
    # Relationships
    appearances = db.relationship('Appearance', back_populates='episode')
    guests = db.relationship('Guest', secondary='appearances', back_populates='episodes')

    serialize_rules = ('-appearances.guest', '-guests',)

    def __repr__(self):
        return f"<Episode {self.id} {self.title} {self.date}>"

class Guest(db.Model, SerializerMixin):
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    occupation = db.Column(db.String)
    
    # Relationships
    appearances = db.relationship('Appearance', back_populates='guest')
    episodes = db.relationship('Episode', secondary='appearances', back_populates='guests')

    serialize_rules = ('-appearances.episode', '-episodes',)


    def __repr__(self):
        return f"<Guest {self.id}, {self.name}>"

class Appearance(db.Model, SerializerMixin):
    __tablename__ = 'appearances'
    
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    
    # Foreign keys
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'))
    episode_id = db.Column(db.Integer, db.ForeignKey('episodes.id'))
    
    # Relationships
    guest = db.relationship('Guest', back_populates='appearances')
    episode = db.relationship('Episode', back_populates='appearances')

    # Validation for rating
    @validates('rating')
    def validate_rating(self, key, value):
        if value < 1 or value > 5:
            raise ValueError('Rating must be between 1 and 5.')
        return value
    
    serialize_rules = ('-guest', '-episode',)

    def __repr__(self):
        return f"<Appearance {self.id} {self.rating}>"