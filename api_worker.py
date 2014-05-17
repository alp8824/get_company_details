#!/usr/bin/env python

import csv
import ujson as json
from crunchbase import Crunchbase


INPUT_CSV = 'input.csv'
OUTPUT_CSV = 'output.csv'
API_KEY = 'mq96jn265dfzs7bzzcnkdkdq'
API_VERSION = 1

def handle_error(function):
    """
    Exception handling decorator
    """
    def workout_problems(*args, **kwargs):
        import traceback
        try:
            return function(*args, **kwargs)
        except Exception as e:
            print "\nEXCEPTION encountered: {}\n".format(e)
            print traceback.format_exc()
            return None
    return workout_problems

def get_company_details(cb, company_name, needed_details):
    """
    Use company name to return a list of company details named in needed_details.
    """
    json_details = cb.company(company_name) 

@handle_error
def main():
    cb = Crunchbase(API_KEY, API_VERSION)
    with open(INPUT_CSV) as read_handler:
        with open (OUTPUT_CSV, 'w') as write_handler:
            reader = csv.reader(read_handler)
            writer = csv.writer(write_handler)
            headers = reader.next()
            writer.writerow(headers)
            for line in reader:
                company_name = line[0]
                new_line = get_company_details(cb, company_name)

cb = Crunchbase(API_KEY, API_VERSION)
details = cb.company('Agilone')
from pprint import pprint
#pprint(details)
print "Website: {}".format(details['homepage_url'])
print "Description: {}".format(details['overview'])
print "# of Employees: {}".format(details['number_of_employees'])
offices = details['offices'][0]
print 'City: {}'.format(offices['city'])
print 'State: {}'.format(offices['state_code'])

people = details['relationships']
for person in people:
    if not person['is_past'] and person['title'] == 'CEO':
        print "CEO Name: {} {}".format(person['person']['first_name'],
                                       person['person']['last_name'])
        ceo = person['person']['permalink']
        print "CEO link: {}".format(person['person']['permalink'])
pprint(cb.person(ceo))


# 'Name' = 
# 'Website' = json_details['homepage_url']
# 'Status' = 
# 'PIC($m)'
# 'Existing Investors'
# '# of Employees'
# 'Alexa Traffic Global Rank'
# 'Prev 3 mos'
# 'Description'
# 'City'
# 'State'
# 'CEO Name'
# 'Contact Number'
# 'Email Address'
# ''
# ''

