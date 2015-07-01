#!/usr/bin/env python
""" This represents the cronjob that runs to check for course openings"""
from google.appengine.api import mail

from models import Snipe
from app import app
from soc import Soc, current_semester

from collections import namedtuple
import datetime
import logging
import urllib

EMAIL_SENDER = "Course Sniper <sniper@rutgers.io>"

Section = namedtuple('Section', ['number', 'index'])

def poll(subject, result=False):
    """ Poll a subject for open courses. """
    app.logger.warning("Polling for %s" % (subject))

    soc = Soc()
    # get all the course data from SOC
    courses = soc.get_courses(subject)

    # build information about which courses/sections are currently open.
    open_data = {}
    for course in courses:
        course_number = course['courseNumber']

        # remove leading zeroes
        if course_number.isdigit():
            course_number = str(int(course_number))

        open_data[course_number] = []
        for section in course['sections']:
            section_number = section['number']
            if section_number.isdigit():
                section_number = str(int(section_number))
            # section is open
            if section['openStatus']:
                open_data[course_number].append(Section(section_number, section['index']))

    # all of these course numbers are open
    open_courses = [course for course, open_sections in open_data.iteritems() if open_sections]

    logging.debug(open_courses)

    if result:
        return open_data

    if open_courses:
        # Notify people that were looking for these courses
        snipes = Snipe.query(Snipe.course_number.IN(open_courses), 
                             Snipe.subject==str(subject),
                             Snipe.active == True).fetch()
        logging.debug(snipes)
        for snipe in snipes:
            for section in open_data[snipe.course_number]:
                if section.number == str(snipe.section):
                    notify(snipe, section.index)
    else:
        logging.warning('Subject "%s" has no open courses' % (subject))


def notify(snipe, index):
    """ Notify this snipe that their course is open"""
    course = '%s:%s:%s' % (snipe.subject, snipe.course_number, snipe.section)
    user = snipe.key.parent().get().user
    logging.info(user)

    if user.email():

        attributes = {
            'email': user.email(),
            'subject': snipe.subject,
            'course_number': snipe.course_number,
            'section': snipe.section,
        }

        # build the url for prepopulated form
        url = 'http://sniper.rutgers.io/?%s' % (urllib.urlencode(attributes))

        register_url = 'https://sims.rutgers.edu/webreg/editSchedule.htm?login=cas&semesterSelection=%s&indexList=%s' % (current_semester, index)

        email_text = 'A course (%s) that you were watching looks open. Its index number is %s. Click the link below to register for it!\n\n %s \n\n If you don\'t get in, visit this URL: \n\n %s \n\n to continue watching it.\n\n Send any feedback to sniper@rutgers.io' % (course, index, register_url, url)

        # send out the email
        message = mail.EmailMessage(sender = EMAIL_SENDER, subject = '[Course Sniper](%s) is open' % (course),)
        message.body = email_text
        message.to = user.email()

        logging.debug(message)
        message.send()
    
    # Record time of snipe.
    snipe.time[-1].completed = datetime.datetime.now()
    # Mark snipe as inactive.
    snipe.active=False
    snipe.put()

    logging.info('Notified user: %s about snipe %s' % (user, snipe))


@app.route('/cron/soc', methods=['GET', 'POST'])
def main():
    logging.getLogger().setLevel(logging.DEBUG)
    subjects = Snipe.query(projection=[Snipe.subject], distinct=True).fetch()
    logging.info(subjects)
    for subject in subjects:
        poll(subject.subject)
    return '', 200


if __name__ == '__main__':
    main() 
