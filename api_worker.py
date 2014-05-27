#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import ujson as json
import unicodedata
import re
import traceback
import string
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from my_logger import log
from apis.crunchbase import Crunchbase
from apis.awis import AwisApi

#INPUT_CSV = 'input.csv'
#OUTPUT_CSV = 'output.csv'
CB_VERSION = 1
NA = ' '
#KEY_FILE = 'rootkey.csv'
            

def parse_cli_opts():
    global args

    arg_parser = ArgumentParser(description='''Get company details via CB & AWIS.
Company list is read from input file.''',
                                formatter_class=ArgumentDefaultsHelpFormatter)

    arg_parser.add_argument('-i', '--input_file',
                            help='Input csv file containing companyes on first column',
                            default='input.csv')
    arg_parser.add_argument('-o', '--output_file',
                            help='Output csv file.',
                            default='outpup.csv')
    arg_parser.add_argument('-k', '--key_file',
                            help='Api keys file.',
                            default='rootkey.csv')
    arg_parser.add_argument('-extra', '--extra-info',
                        help='Get extra info on companies.',
                        action="store_true")
    args = arg_parser.parse_args()


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
            tree = awis.url_info(website, 'Rank', 'RankByCountry', 'RankByCity')
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
                log.debug(traceback.format_exc())
                log.info("Failed to read AWIS return status...")
        else:
            log.info("No website specified. Website is {}.".format(website))

def get_rank(api, tree, rank_type, key_code='', val_code='Rank'):
    rank_search = '//{%s}%s' % (api.NS_PREFIXES['awis'], rank_type)
    rank_root = tree.find(rank_search)
    ret = None
    try:
        if rank_type == 'Rank':
            ret = rank_root.text 
            if not ret:
                log.info("\tRank not specified.")
        else: 
            ret = {}
            for child in rank_root:
                # print '{} -> {}'.format(child.tag, child.attrib)
                key = child.attrib.get(key_code)
                for nep in child:
                    if 'Rank' in nep.tag:
                        value = nep.text
                        if value:
                            ret[key] = value
    except:
        log.info('\t{} info not found...'.format(rank_type))
        log.debug(traceback.format_exc())
    return ret

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

    # get website details from AWIS
    website = get_info(details, 'homepage_url')
    tree = get_awis_tree(awis, website)
    # get prev 3 month rank
    prev3 = get_rank(awis, tree, 'Rank')

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

    #Add extra info if required
    # order here should be the same as in the main function section
    if args.extra_info:
        # get ranks by city and country
        rco = get_rank(awis, tree, 'RankByCountry', 'Code')
        rci = get_rank(awis, tree, 'RankByCity', 'Name')
        # 'Rank By Country'
        lappend(details_list, rco)
        # 'Rank By City'
        lappend(details_list, rci)

    return [unicode_to_str(detail) for detail in details_list]


def main():
    cb = Crunchbase(CB_KEY, CB_VERSION)
    awis =  AwisApi(AWIS_KEY_ID, AWIS_SECRET_KEY)
    # # --- TESTING ----------------------
    # from pprint import pprint
    # api = AwisApi(AWIS_KEY_ID, AWIS_SECRET_KEY)
    # # tree = api.url_info("http://www.cloudtp.com",
    # #                     'Rank',
    # #                     'RankByCountry',
    # #                     'RankByCity')
    # tree = api.url_info("http://www.agilone.com",
    #                     'Rank',
    #                     'RankByCountry',
    #                     'RankByCity')
    # pprint(tree)
    # import sys
    # tree.write(sys.stdout)
    # print "\n"
    # # pprint(cb.company('Seven-Medical'))
    # text = "//{%s}StatusCode" % api.NS_PREFIXES["alexa"]
    # print "Looking for {}".format(text)
    # status = tree.find(text)
    # if status.text != "Success":
    #     print "AWIS request unsuccessful."
    # text = "//{%s}Rank" % api.NS_PREFIXES["awis"]
    # print "Looking for {}".format(text)
    # rank = tree.find(text)
    # print rank.text 
    # rco = get_rank(api, tree, 'RankByCountry', 'Code')
    # print rco
    # rci = get_rank(api, tree, 'RankByCity', 'Name')
    # print rci
    # exit()
    # # ------------------------------------
    with open(args.input_file) as read_handler:
        with open (args.output_file, 'w') as write_handler:
            reader = csv.reader(read_handler)
            writer = csv.writer(write_handler)
            h = reader.next()
            headers = [x for x in h if x]
            headers.remove('Alexa Traffic Global Rank')
            if args.extra_info:
                headers.append('Rank By Country')
                headers.append('Rank By City')
            writer.writerow(headers)
            for line in reader:
                if not_empty(line):
                    company_name = line[0].strip()
                    new_line = get_company_details(cb, awis, company_name)
                    writer.writerow(new_line)
    
if __name__ == '__main__':
    parse_cli_opts()
    if not get_keys(args.key_file):
        log.info("""ERROR: Failed reading API keys from file {}.
Check the readme and make sure the file exists and 
has the appropriate format.""".format(args.key_file))
        exit(1)
    try:
        main()
    except IOError as e:
        if 'response code is 403' in e.message:
            log.debug(traceback.format_exc())
            log.info("!!! -> Make sure the AWIS keys are correctly read from key file.\n")
        else:
            log.info(e)
    


