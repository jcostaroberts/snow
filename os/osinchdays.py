#!/usr/bin/env python

from prettytable import PrettyTable
import argparse
import osutil
import pdb

# Get the percentage of recorded days a resort got more than a given amount of snowfall.
def get_pct_inch_days(dbconn, resort, threshold, data_days):
    return osutil.db_get_inch_days_winter(dbconn, resort, threshold)/float(data_days)

# For all of the threshold amounts, the the percentage of recorded dats a resort got
# more than that much snow.
def get_resort_snowfall_data(dbconn, resort, thresholds, resorts):
    data_days = osutil.db_get_data_days_winter(dbconn, resort)
    return [resorts[resort], data_days] + \
           map(lambda t: get_pct_inch_days(dbconn, resort, t, data_days), thresholds)

# Create output table.
def display_data(sortby, thresholds, resort_data):
    sortby_index = thresholds.index(sortby) + 2
    table_hdr = ["Mountain", "Data Days"] + map(lambda x: "%.1f+\"" % x, thresholds)
    pt = PrettyTable(table_hdr)
    resort_data = sorted(resort_data, key=lambda rd: rd[sortby_index], reverse=True)
    map(lambda rd: pt.add_row(rd[0:2] + map(lambda x: "{0:.2f}%".format(x*100), rd[2:])),
        resort_data)
    print pt

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sort-by", dest="sort", type=int, default=4,
                        help="Inch-days to sort by")
    parser.add_argument("--thresholds", dest="thresholds", type=float, nargs="*",
                        default=[0.1,4.0,9.0,18.0], help="Inch-days to sort by")
    args = parser.parse_args()
    assert args.sort in args.thresholds, "sort-by threshold not in " + str(args.thresholds)

    dbconn = osutil.db_get_connection()
    resorts = osutil.get_resorts()
    display_data(args.sort, args.thresholds,
                 map(lambda x: get_resort_snowfall_data(dbconn, x, args.thresholds, resorts),
                     resorts.keys()))
    osutil.db_close_connection(dbconn)
