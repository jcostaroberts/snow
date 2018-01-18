#!/usr/bin/env python

from lxml import html
import argparse
import osutil
import pdb
import re
import requests

def resort_url(resort):
    return "https://opensnow.com/location/" + resort

def resort_snow_month_url(resort_id, month, year):
    url = "https://opensnow.com/location/snips/snowhistory?location_id=%d&month=%d&year=%d"
    return url % (resort_id, month, year)

def get_resort_location_id(session, resort):
    res_page = session.get(resort_url(resort))
    return int(re.findall("location_id=\d+", res_page.content)[0].split("=")[1])

def get_resort_snow_month_data(dbconn, session, resort, location_id, month, year):
    print "  Updating %d-%d" % (year, month)
    pg = session.get(resort_snow_month_url(location_id, month, year))
    tree = html.fromstring(pg.content)
    snowdays = [x.text_content().strip('"') for x in tree.find_class("report-value")]
    snowdays = [(float(x) if x != "--" else None) for x in snowdays]
    if len(filter(lambda x: x is not None, snowdays)) == 0:
        return
    days = [int(x.text_content()) for x in tree.find_class("day-number")]
    month_data = map(lambda (day, amt): (resort, year, month, day, amt),
                     zip(days, snowdays))
    osutil.db_write(dbconn, month_data)

def get_snowmonths(dbconn, session, resort, location_id):
    dec_page = session.get(resort_snow_month_url(location_id, 12, 2017))
    tree = html.fromstring(dec_page.content)
    months = [y.split("-") for y in tree.find_class("form-control input-sm")[0].value_options]
    months = map(lambda x: (int(x[1]), int(x[0])), months)

    # Find the most recent month for this resort that's in the database. Every month
    # since that month, inclusive, needs updating. (The months list is newest-oldest.)
    for i in range(len(months)):
        if osutil.db_contains_month_data(dbconn, resort, months[i][0], months[i][1]):
            print "  db contains data for %d-%d. Months to update: %s" % \
                  (months[i][1], months[i][0], str(months[:(i+1)][::-1]))
            return months[:(i+1)][::-1]

    # There's no data for this resort yet. Return all months.
    return months[::-1]

def get_resort_snow_data(dbconn, session, resort):
    print "Getting historical data for " + resort + "..."
    lid = get_resort_location_id(session, resort)
    map(lambda (mo, yr): get_resort_snow_month_data(dbconn, session, resort, lid, mo, yr),
        get_snowmonths(dbconn, session, resort, lid))

def get_session(email, password):
    session = requests.session()
    login_url = "https://opensnow.com/user/login"
    result = session.get(login_url)
    tree = html.fromstring(result.text)
    auth_token = list(set(tree.xpath("//input[@name='_token']/@value")))[0]
    result = session.post(login_url,
                          data={"email": email,
                                "password": password,
                                "_token": auth_token},
                          headers = dict(referer=login_url))
    return session

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", dest="email", required=True, help="OpenSnow email")
    parser.add_argument("--password", dest="password", required=True, help="OpenSnow password")
    args = parser.parse_args()

    session = get_session(args.email, args.password)
    dbconn = osutil.db_get_connection()
    map(lambda resort: get_resort_snow_data(dbconn, session, resort),
        osutil.get_resorts().keys())
    osutil.db_close_connection(dbconn)
