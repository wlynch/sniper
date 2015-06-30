""" Represents the persistent models for the sniper application"""
from google.appengine.ext import ndb

class Snipe(ndb.Model):
    """ A snipe model represents the course info pertaining to a snipe"""
    subject = ndb.StringProperty()
    course_number = ndb.StringProperty()
    section = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

class User(ndb.Model):
    """ Represents a user in the database. """
    user = ndb.UserProperty()
