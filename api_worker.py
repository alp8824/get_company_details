#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import ujson as json
import unicodedata
import re
from crunchbase import Crunchbase


INPUT_CSV = 'input.csv'
OUTPUT_CSV = 'output.csv'
API_KEY = 'mq96jn265dfzs7bzzcnkdkdq'
API_VERSION = 1
NA = 'NA'

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

def lappend(lst, element):
    if element:
        lst.append(element)
    else:
        lst.append(NA)

def get_info(detail_dict, key):
    try:
        return detail_dict[key]
    except:
        return None

def strip_formatting(data):
    p = re.compile(r'<.*?>')
    if data:
        return p.sub('', data)
    return data

def unicode_to_str(unicode_str):
    if type(unicode_str) is unicode:
        return unicodedata.normalize('NFKD', unicode_str).encode('ascii','ignore')
    else:
        return unicode_str

def get_company_details(cb, company_name):
    """
    Use company name to return a list of company details named in needed_details.
    """
    import time
    now = time.time()
    details = cb.company(company_name.lower().strip().replace(' ','-'))
    details_list = []
    # 'Name'
    lappend(details_list, company_name)
    if not details:
        return details_list
    # 'Website'
    lappend(details_list, get_info(details, 'homepage_url'))
    # 'Status' 
    lappend(details_list, '')
    # 'PIC($m)'
    raised_amount = 0
    investors = set()
    fund_rounds = get_info(details, 'funding_rounds')
    try:
        for funds in fund_rounds:
            amount = get_info(funds, 'raised_amount')
            if amount: raised_amount += amount
            for investor in funds['investments']:
                if investor['financial_org']:
                    investors.add(investor['financial_org']['name'])
    except:
        pass
    if not investors: investors = NA
    lappend(details_list, '$'+str(raised_amount))
    # 'Existing Investors'
    if raised_amount == 0: raised_amount = NA
    lappend(details_list, ','.join(investors))
    # '# of Employees'
    lappend(details_list, get_info(details, 'number_of_employees'))
    # 'Alexa Traffic Global Rank'
    lappend(details_list, '')
    # 'Prev 3 mos'
    lappend(details_list, '')
    # 'Description'
    description = get_info(details,'overview')
    lappend(details_list, strip_formatting(description))
    # 'City'
    offices = get_info(details, 'offices')
    try: 
        offices = offices[0]
        city = get_info(offices, 'city')
        state = get_info(offices,'state_code')
    except:
        city, state = NA, NA
    lappend(details_list, city)
    # 'State'
    lappend(details_list, state)
    # 'CEO Name'
    people = get_info(details, 'relationships')
    ceo = NA
    try:
        for person in people:
            if not person['is_past'] and 'CEO' in person['title']:
                person = get_info(person,'person')
                if person:
                    ceo = "{} {}".format(person['first_name'],
                                         person['last_name'])
    except: 
        pass
    lappend(details_list, ceo)        
#            ceo = person['person']['permalink']
#            ceo_details = cb.person(ceo)
#            external_link = ceo_details['web_presences'][0]['external_url']
    # 'Contact Number'
    lappend(details_list, get_info(details, 'phone_number'))
    # 'Email Address'
    lappend(details_list, get_info(details, 'email_address'))
    print ('Company: {} took: {}'.format(company_name, time.time()-now))
    return [unicode_to_str(detail) for detail in details_list]


@handle_error
def main():
    cb = Crunchbase(API_KEY, API_VERSION)
    from pprint import pprint
    pprint(cb.company('fuelquest'))
    exit()
    with open(INPUT_CSV) as read_handler:
        with open (OUTPUT_CSV, 'w') as write_handler:
            reader = csv.reader(read_handler)
            writer = csv.writer(write_handler)
            headers = reader.next()
            writer.writerow(headers)
            for line in reader:
                company_name = line[0]
                new_line = get_company_details(cb, company_name)
                writer.writerow(new_line)
    
if __name__ == '__main__':
    main()
