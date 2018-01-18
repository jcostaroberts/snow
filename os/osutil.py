#!/usr/bin/env python

import pdb
import sqlite3

db_file = "snowfall.db"
resort_file = "os-resort.txt"

def get_resorts(osname=True):
    f = open(resort_file, "r")
    out = filter(lambda x: x.count("#") == 0 and x != "\n", f.readlines())
    f.close()
    idx = 1 if osname else 0
    rtupl = [x.strip().split(", ") for x in out]
    return dict((b, a) for a, b in rtupl)

def db_get_connection():
    conn = sqlite3.connect(db_file)
    curs = conn.cursor()
    table_fmt = ("(resortname text, year integer, month integer, day integer, snowfall real, "
                 "primary key (resortname, year, month, day))")
    curs.execute("create table if not exists snowfall %s" % table_fmt)
    return conn

def db_close_connection(conn):
    conn.close()

def db_write(conn, rows):
    conn.cursor().executemany("insert or replace into snowfall values (?,?,?,?,?)", rows)
    conn.commit()

def db_contains_month_data(conn, resort, month, year):
    stmt = "select * from snowfall where resortname = ? and year = ? and month = ?"
    rym = (resort, year, month)
    curs = conn.cursor()
    curs.execute(stmt, rym)
    return len(curs.fetchall()) > 0

# Number of days resort reported at least a given amount of fresh snowfall.
def db_get_inch_days_winter(conn, resort, inches):
    stmt = ("select * from snowfall where resortname = ? and (month <= 4 or month = 12) and "
            "snowfall >= ?")
    c = conn.cursor()
    c.execute(stmt, (resort, inches))
    return len(c.fetchall())

# Number of total winter (Dec-April) days with valid (non-NA) data for a given resort.
def db_get_data_days_winter(conn, resort):
    stmt = ("select * from snowfall where resortname = ? and (month <= 4 or month = 12) and "
            "snowfall >= 0")
    c = conn.cursor()
    c.execute(stmt, (resort,))
    return len(c.fetchall())
