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
NA = ' '

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

def check_details(details):
    if not details:
        return False
    try:
        aux = details['error']
        return False
    except:
        return True

def not_empty(lst):
    for element in lst:
        if element:
            return True
    return False

def get_raw_details(cb, company_name):
    print "Looking up {}...".format(company_name)
    details = cb.company(company_name)
    if not check_details(details):
        cn = company_name.replace(' ','')
        cn = cn.replace('.com','')
        if cn != company_name:
            print ("\t {}...".format(cn))
            details = cb.company(cn)
    if not check_details(details):
        cn = company_name.lower().replace(' ','-')
        cn = cn.replace('.','-')
        if cn != company_name:
            print ("\t {}...".format(cn))
            details = cb.company(cn)
    if not check_details(details):
        return None
    return details

def get_company_details(cb, company_name):
    """
    Use company name to return a list of company details named in needed_details.
    """
    import time
    now = time.time()

    details_list = []
    # 'Name'
    company_name = company_name.strip()
    new_company_name = company_name
    lappend(details_list, company_name)

    # try and get company details
    details = get_raw_details(cb, company_name)
    if not details:
        print 'Searching for company {}...'.format(company_name)
        search_details = cb.search(company_name)
        if search_details['total'] == 0:
            return details_list
        else:
            for result in search_details['results']:
                try:
                    if company_name in result['name'] \
                            or result['name'] in company_name:
                        new_company_name = result['name']
                        break
                except:
                    pass
        if new_company_name != company_name:
            details = get_raw_details(cb, new_company_name)
    if not details:
        print "\t\tNOT FOUND"
        return details_list

    # 'Website'
    lappend(details_list, get_info(details, 'homepage_url'))
    # 'Status' 
    lappend(details_list, '')
    # 'PIC($m)'
    raised_amount = 0
    investors_set = set()
    fund_rounds = get_info(details, 'funding_rounds')
    try:
        for funds in fund_rounds:
            amount = get_info(funds, 'raised_amount')
            if amount: raised_amount += amount
            for investor in funds['investments']:
                if investor['financial_org']:
                    investors_set.add(investor['financial_org']['name'])
    except:
        pass
    if not investors_set:
        investors = NA
    else:
        investors = ','.join(investors_set)
    lappend(details_list, '$'+str(raised_amount))
    # 'Existing Investors'
    if raised_amount == 0: raised_amount = NA
    lappend(details_list, investors)
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
    # from pprint import pprint
    # pprint(cb.company('Seven-Medical'))
    # exit()
    with open(INPUT_CSV) as read_handler:
        with open (OUTPUT_CSV, 'w') as write_handler:
            reader = csv.reader(read_handler)
            writer = csv.writer(write_handler)
            headers = reader.next()
            writer.writerow(headers)
            for line in reader:
                if not_empty(line):
                    company_name = line[0].strip()
                    new_line = get_company_details(cb, company_name)
                    writer.writerow(new_line)
    
if __name__ == '__main__':
    main()
