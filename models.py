""" Represents the persistent models for the sniper application"""
from google.appengine.ext import ndb

class SnipeTime(ndb.Model):
    created = ndb.DateTimeProperty(auto_now_add=True)
    completed = ndb.DateTimeProperty()

class Snipe(ndb.Model):
    """ A snipe model represents the course info pertaining to a snipe"""
    semester = ndb.StringProperty()
    subject = ndb.StringProperty()
    course_number = ndb.StringProperty()
    section = ndb.StringProperty()
    # Keep track of each time a user requests a snipe. If a snipe is fired off,
    # the user may re-request it.
    time = ndb.StructuredProperty(SnipeTime, repeated=True)
    # Start inactive so we can tell the difference between a new
    # and active snipe.
    active = ndb.BooleanProperty(default=False)

class User(ndb.Model):
    """ Represents a user in the database. """
    user = ndb.UserProperty()
