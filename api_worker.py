#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import ujson as json
import unicodedata
import re
import traceback
import string
from my_logger import log
from apis.crunchbase import Crunchbase
from apis.awis import AwisApi

INPUT_CSV = 'input.csv'
OUTPUT_CSV = 'output.csv'
CB_VERSION = 1
NA = ' '
KEY_FILE = 'rootkey.csv'
            

def get_keys(KEY_FILE):
    global CB_KEY
    global AWIS_SECRET_KEY
    global AWIS_KEY_ID    
    try:
        with open(KEY_FILE) as f:
            lines = f.readlines()
            CB_KEY = lines[0].strip().split('=')[1]
            AWIS_KEY_ID = lines[1].strip().split('=')[1]
            AWIS_SECRET_KEY = lines[2].strip().split('=')[1]
            return (CB_KEY, AWIS_KEY_ID, AWIS_SECRET_KEY)
    except:
        return None

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

def get_cb_raw_details(cb, company_name):
    log.info("Looking up '{}' in CB...".format(company_name)) 
    details = cb.company(company_name)
    if not check_details(details):
        cn = company_name.replace(' ','')
        cn = cn.replace('.com','')
        if cn != company_name:
            log.info("\t {}...".format(cn))
            details = cb.company(cn)
    if not check_details(details):
        cn = company_name.lower().replace(' ','-')
        cn = cn.replace('.','-')
        if cn != company_name:
            log.info("\t {}...".format(cn))
            details = cb.company(cn)
    if not check_details(details):
        return None
    return details

def get_awis_tree(awis, website):
        if website:
            log.info("Getting AWIS data for {}...".format(website))
            tree = awis.url_info(website, "Rank")
            status_search = "//{%s}StatusCode" % awis.NS_PREFIXES["alexa"]
            status = tree.find(status_search)
            try:
                if status.text != "Success":
                    log.info('''ERROR:AWIS request unsuccessful for website: 
\t{}'''.format(Website))
                    tree.write(sys.stdout)
                    return None
                return tree
            except Exception as e:
                log.info(traceback.format_exc())
                log.info("Failed to read AWIS return status...")
        else:
            log.info("No website specified. Website is {}.".format(website))

def get_company_details(cb, awis, company_name):
    """
    Use company name to return a list of company details named in needed_details.
    """
    details_list = []

    # get company name and strip spaces and punctuation
    name = company_name.strip()
    company_name = name.strip(string.punctuation)
    log.info('')
    log.info("{}".format(company_name.upper()))
    new_company_name = company_name


    # get company details from CB
    details = get_cb_raw_details(cb, company_name)
    if not details:
        log.info('Searching CB for company {}...'.format(company_name))
        search_details = cb.search(company_name)
        if search_details['total'] == 0:
            return [company_name]
        else:
            for result in search_details['results']:
                try:
                    if company_name in result['name'] \
                            or result['name'] in company_name:
                        new_company_name = result['name']
                        details = get_cb_raw_details(cb, new_company_name)
                        company_name = "{}{}({})".format('?',
                                                         company_name,
                                                         new_company_name)
                        break
                except:
                    pass
    if not details:
        log.info("\t\tNOT FOUND")
        return [company_name]

    website = get_info(details, 'homepage_url')
    # get website details from AWIS
    prev3 = NA
    tree = get_awis_tree(awis, website)
    if tree:
        rank_search = "//{%s}Rank" % awis.NS_PREFIXES["awis"]
        rank = tree.find(rank_search)
        try:
            prev3 = rank.text 
            if not prev3:
                log.info("\tRank not specified.")
        except:
            log.info("\tFailed fetching rank.")

    #Build CSV line list
    # 'Name' - rewrite in case new company found
    lappend(details_list, company_name)
    # 'Website'
    lappend(details_list, website)
    # 'Status'
    acq = get_info(details, 'acquisition')
    ipo = get_info(details, 'ipo')
    status = 'Private'
    if ipo or acq:
        status = 'Public'
    lappend(details_list, status)
    # 'PIC($m)'
    raised_amount = 0
    investors_set = set()
    fund_rounds = get_info(details, 'funding_rounds')
    try:
        for funds in fund_rounds:
            amount = get_info(funds, 'raised_amount')
            if amount: 
                raised_amount += amount
            for investor in funds['investments']:
                if investor['financial_org']:
                    investors_set.add(investor['financial_org']['name'])
    except:
        pass
    if raised_amount == 0: 
        raised_amount = NA
    else:
        raised_amount = '$'+str(raised_amount)
    # OR raised_amount = get_info(details, 'total_money_raised')
    lappend(details_list, raised_amount)
    # 'Existing Investors'
    if not investors_set:
        investors = NA
    else:
        investors = ','.join(investors_set)
    lappend(details_list, investors)
    # '# of Employees'
    lappend(details_list, get_info(details, 'number_of_employees'))
    # 'Alexa Traffic Global Rank'
    lappend(details_list, '')
    # 'Prev 3 mos'
    lappend(details_list, prev3)
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
    return [unicode_to_str(detail) for detail in details_list]


def main():
    cb = Crunchbase(CB_KEY, CB_VERSION)
    awis =  AwisApi(AWIS_KEY_ID, AWIS_SECRET_KEY)
    # # --- TESTING ----------------------
    from pprint import pprint
    api = AwisApi(AWIS_KEY_ID, AWIS_SECRET_KEY)
    tree = api.url_info("http://www.cloudtp.com",
                        'Rank',
                        'RankByCountry',
                        'RankByCity')
    pprint(tree)
    import sys
    tree.write(sys.stdout)
    print "\n"
    # pprint(cb.company('Seven-Medical'))
    text = "//{%s}StatusCode" % api.NS_PREFIXES["alexa"]
    print "Looking for {}".format(text)
    status = tree.find(text)
    if status.text != "Success":
        print "AWIS request unsuccessful."
    text = "//{%s}Rank" % api.NS_PREFIXES["awis"]
    print "Looking for {}".format(text)
    rank = tree.find(text)
    print rank.text 
    text = '//{%s}RankByCountry' % api.NS_PREFIXES['awis']
    rbc = tree.find(text)
    for child in rbc:
        print '{} -> {}'.format(child.tag, child.attrib)
    for n in rbc.findall('Rank'):
        print n.text
    exit()
    # # ------------------------------------
    with open(INPUT_CSV) as read_handler:
        with open (OUTPUT_CSV, 'w') as write_handler:
            reader = csv.reader(read_handler)
            writer = csv.writer(write_handler)
            headers = reader.next()
            writer.writerow(headers)
            for line in reader:
                if not_empty(line):
                    company_name = line[0].strip()
                    new_line = get_company_details(cb, awis, company_name)
                    writer.writerow(new_line)
    
if __name__ == '__main__':
    if not get_keys(KEY_FILE):
        log.info("""ERROR: Failed reading API keys from file {}.
Check the readme and make sure the file exists and 
has the appropriate format.""".format(KEY_FILE))
    try:
        main()
    except IOError as e:
        if 'response code is 403' in e.message:
            log.info(traceback.format_exc())
            log.info("!!! -> Make sure the AWIS keys are correctly read from key file.\n")
        else:
            log.info(e)
    


