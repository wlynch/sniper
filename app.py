""" This file sets up the Flask Application for sniper.
    Sniper is an application that hits the Rutgers SOC API and notifies users when a class opens up. """

from flask import Flask, render_template, request
from wtforms import Form, TextField, validators
from wtforms.validators import StopValidation
from models import Snipe, User, SnipeTime
from soc import Soc, current_semester
import re
import json
import logging
import datetime

from google.appengine.api import users
 
# Set up the Flask application
app = Flask(__name__)

class SnipeForm(Form):
    """ Represents the Snipe form on the homepage. """
    email = TextField('Email', [validators.Email(), validators.Required()])
    subject = TextField('Subject')
    course_number = TextField('Course Number', [validators.Length(min=2, max=4), validators.NumberRange()])
    section = TextField('Section', [validators.Length(min=1, max=4)])

    def validate_subject(form, field):
        if not form.subject.data.isdigit():
            m = re.search('(\d+)', form.subject.data)
            if m:
                form.subject.data = m.group(1)
            else:
                raise StopValidation('Please enter a valid subject')
        return True

    def validate_course_number(form, field):
        # course numbers sometime have leading zeroes
        if form.course_number.data.isdigit():
            form.course_number.data = str(int(form.course_number.data))
        return True

    def validate_section(form, field):
        if form.section.data.isdigit():
            form.section.data = str(int(form.section.data))
        return True

    def save(self):
        """ Saves to Datastore. """
        # Use the email address as the ID to ensure that users are unique.
        # This may change later on if we want to tie Google, Scarletmail, or
        # OAuth accounts to the service.
        user = User(user=users.User(self.email.data), id=self.email.data)
        user.put()
        snipe_id = '%s:%s:%s:%s' % (current_semester,
                                    self.subject.data,
                                    self.course_number.data,
                                    self.section.data)
        snipe = Snipe.get_or_insert(snipe_id, parent = user.key)
        snipe.semester = current_semester
        snipe.subject = self.subject.data
        snipe.course_number = self.course_number.data
        snipe.section = self.section.data
        if not snipe.active:
        # Only add new timestamp if this is currently an inactive snipe
            snipe.time.append(SnipeTime())
        snipe.active = True
        snipe.put()


def _SemesterString(semester):
    # Small helper to go from the semester code to a human-readable string.
    # e.g. 92015 => Fall 2015
    term = {
        '1': 'Spring',
        '9': 'Fall',
    }[semester[0]]
    return "%s %s" % (term, semester[1:])


@app.route('/', methods=['GET', 'POST'])
def home():
    """ Handles the home page rendering."""

    soc = Soc()
    subjects = soc.get_subjects()

    form = SnipeForm(request.form)
    if request.method == 'POST' and form.validate():
        form.save()
        return render_template('success.html', form=form)
    if not request.form:
        # this trick allows us to prepopulate entries using links sent out in emails.
        form = SnipeForm(request.args)

    return render_template('home.html', form=form, subjects=subjects,
            semester=_SemesterString(current_semester))


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
