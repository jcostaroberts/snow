#!/usr/bin/env python

from lxml import html
import csv
import os
import pdb
import requests

resort_file = "resort.txt"
years = range(2009, 2017)

# resort.txt contains a list of mountains with the format:
# <OTS resort name> <state>
# For each resort, get daily snowfall data since 2009 and
# output the data in a csv file
# (data/<OTS resort name>-<yr1>-<yrn>.csv).

def resort_url(resort, state, year):
    return ("http://www.onthesnow.com/%s/%s/historical-snowfall.html?"
            "&y=%d&q=snow&v=list#view") % (state, resort, year)

def create_data_dir():
    try:
        os.makedirs("data")
    except OSError:
        if not os.path.isdir("data"):
            raise

def write_resort_file(resort, data):
    create_data_dir()
    f = open("data/%s-%d-%d.csv" % (resort, min(years), max(years)), "wt")
    writer = csv.writer(f)
    writer.writerow(["month", "day", "year", "new-snow-inches",
		     "season-total-inches", "base-depth-in"])
    map(writer.writerow, data)
    f.close()

def get_resort_year_data(resort, state, year):
    page = requests.get(resort_url(resort, state, year))
    tree = html.fromstring(page.content)
    table = tree.xpath('//td[@class="cell"]/text()')
    # At this point, the table looks like this:
    #     ['Jan  4, 2009', '3 in.', '3 in.', '71 in.',
    #      'Jan  5, 2009', '16 in.', '19 in.', '71 in.']
    # Make each member a month, day, year, or number (in inches)
    table = [x.replace(" in.", "").replace(",", "") for x in table]
    table = sum([x.split() for x in table], [])
    # Group by date
    return [table[i:(i+6)] for i in range(0, len(table), 6)]

def get_resort_data(resort, state):
    return sum(map(lambda y: get_resort_year_data(resort, state, y), years),
               [])

def read_resort_list():
    # File's lines should look like:
    #     whistler-blackcomb british-columbia
    # Return a list of lists:
    #     [ [ "whistler-blackcomb", "british-columbia" ], ... ]
    f = open(resort_file, "r")
    out = filter(lambda x: not x.count("#"), f.readlines())
    f.close()
    return [x.split() for x in out]

if __name__ == "__main__":
    resorts = read_resort_list()
    map(lambda x, y: write_resort_file(x, y), [x[0] for x in resorts],
        map(lambda r: get_resort_data(r[0], r[1]), resorts))
