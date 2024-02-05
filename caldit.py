#!/usr/bin/python3
# -*- coding: utf-8 -*-

dbasepath = ''
import os # needed 4 dbasepath and parse_custom_url() cut windows path
if os.name == 'nt':
    dbasepath = 'C:\\Users\\ds\\cnet\\py\\cal\\'
else:
    dbasepath = '/home/debian/synct/cnet/py/cal/'

verbose = 0 #3 all
local_time_zone = "Europe/Paris"

cat_farbcodes = {
    "day_top": "#E8E8E8", # number on top
    "events": "#FF484F",
    "home": "#00FF00",
    "logs": "#0D2053",
    "birthday": "#FFD700",
    "urgent": "#200202"
}

"""
req : pip install python-dateutil  for RRULE.
to connect html with python script, over mime support

Debian 12:
sudo nano /usr/share/mime/packages/caldit-mime.xml
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-caldit">
        <comment>Caldit</comment>
        <glob pattern="caldit://*"/>
    </mime-type>
</mime-info>
sudo nano /usr/share/applications/caldit.desktop
[Desktop Entry]
Type=Application
Name=Caldit
Exec=/usr/bin/python3 /home/debian/synct/cnet/py/cal/caldit.py %U
Icon=weather-clear
Categories=WebBrowser;
MimeType=x-scheme-handler/caldit;
sudo update-desktop-database
sudo update-mime-database /usr/share/mime
xdg-mime default caldit.desktop application/x-caldit
xdg-mime query default application/x-caldit
xdg-open "caldit://create?single=yes"
open 'months.html' in browser, push export button(longest wait), accept popup. same page2.html

Windows:
where python
pip install tzdata
caldit.reg content
Windows Registry Editor Version 5.00
[HKEY_CLASSES_ROOT\caldit]
@="URL:caldit Protocol"
"URL Protocol"=""
[HKEY_CLASSES_ROOT\caldit\shell]
[HKEY_CLASSES_ROOT\caldit\shell\open]
[HKEY_CLASSES_ROOT\caldit\shell\open\command]
@="\"C:\\Users\\ds\\AppData\\Local\\Programs\\Python\\Python311\\python.exe\" \"C:\\Users\\ds\\cnet\\py\\cal\\caldit.py\" \"%1\""
create caldit.reg, edit paths(python and script), doubleclick, accept.
python caldit.py
open 'months.html' in browser, push export button(longest wait), accept popup. same page2.html
"""

import sys
import time
import sqlite3
from datetime import datetime, timedelta, timezone
import calendar
import ast
from urllib.parse import unquote
import logging
from dateutil.rrule import rrulestr
from zoneinfo import ZoneInfo, available_timezones
import re

scan_time = time.strftime("%d%m%Y%H%M%S")
con = sqlite3.connect('{}ical.db'.format(dbasepath))
all_termins = {}
multi_day_dic = {}

logging.basicConfig(level=logging.INFO, filename=f"{dbasepath}cal.log", filemode='a')
if verbose > 1: logging.info(f"{dbasepath}cal.log started {scan_time}")

def erstelle_table_termine():
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS termine (" 
                    "UID TEXT, DTSTAMP TEXT, CREATED TEXT, LASTMODIFIED TEXT, DTSTARTZID TEXT,"
                    "DTSTART TEXT, DTEND TEXT, SUMMARY TEXT, DESCRIPTION TEXT, "
                    "LOCATION TEXT, GEO TEXT, ORGANIZER TEXT, ATTENDEE TEXT, "
                    "URL TEXT, STATUS TEXT, VALARM TEXT, RRULE TEXT, RRULEND TEXT, RRULEXTRA TEXT, CLASS TEXT, "
                    "TRANSP TEXT, PRIORITY INTEGER, CATEGORIES TEXT, ATTACH BLOB, "
                    "ATTACH2 BLOB, TMP TEXT, UNIQUE (UID));")
erstelle_table_termine()

def parse_datetime(time_str, DTSTARTZID):
    try:
        pattern = r'(\d{4})(?:[-/]?)(\d{2})(?:[-/]?)(\d{2})(?:(?:[ T])?(\d{2})(?::?(\d{2}))?(?::?(\d{2}))?)?(?:Z)?'
        match = re.search(pattern, time_str)
        if match:
                year, month, day, hour, minute, second = match.groups()
                year, month, day = map(int, [year, month, day])
                hour = int(hour) if hour is not None else 0
                minute = int(minute) if minute is not None else 0
                second = int(second) if second is not None else 0
                if time_str.endswith('Z'):
                    dt = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo("UTC"))
                    local_time = dt.astimezone(ZoneInfo(local_time_zone))
                    return local_time
                elif DTSTARTZID in available_timezones():
                    dt = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(DTSTARTZID))
                    local_time = dt.astimezone(ZoneInfo(local_time_zone))
                    return local_time
                else:
                    local_time = datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(local_time_zone))
                    return local_time
        else:
            return None
    except Exception as e:
        if verbose > 1: logging.info(f" parse_datetime  except Exception as e: {e} " )
        return None

# needed 4 check_termin_at_date
def insert_rr_freq_termins(y, m, d):
    with con:
        string_to_insert = ''
        cur = con.cursor()
        cur.execute(f'SELECT UID, DIC_TERMIN, DTSTART FROM RRULET WHERE YEAR="{y}";')
        result1 = cur.fetchall()
        if result1:
            for entry in result1:
                string_to_dic = entry[1]
                DTSTARTRR = entry[2]
                if f'datetime.datetime({y}, {m}, {d}, ' in string_to_dic:
                    cur = con.cursor()
                    cur.execute(f'SELECT UID, DTSTART, DTEND, CATEGORIES, SUMMARY, DESCRIPTION, DTSTARTZID FROM termine WHERE UID="{entry[0]}";')
                    result = cur.fetchone()
                    if result:

                        UID = result[0]
                        CATEGORIES = result[3]
                        SUMMARY = result[4]
                        DESCRIPTION = result[5]
                        status_day = 'RR'
                        DTSTARTZID = result[6]

                        if f"{y:4d}{m:02d}{d:02d}" not in DTSTARTRR:
                            if CATEGORIES in cat_farbcodes:
                                farbecode = cat_farbcodes[CATEGORIES]
                            else:
                                farbecode = cat_farbcodes['day_top']

                            date = "{:04d}{:02d}{:02d}".format(y, m, d)
                            if date not in all_termins:
                                all_termins[date] = []
                            DTSTARTs = parse_datetime(result[1], DTSTARTZID)
                            dt_rr_start = DTSTARTs.replace(year=y, month=m, day=d)
                            DTENDs = parse_datetime(result[2], DTSTARTZID)
                            dt_rr_end = DTENDs.replace(year=y, month=m, day=d)
                            all_termins[date].append([UID, dt_rr_start, dt_rr_end, SUMMARY, DESCRIPTION, CATEGORIES, status_day, date])

def between(date, y, m, d):
    string_to_insert = ''
    if len(multi_day_dic) > 0:
        with con:
            # get copy
            uids_to_process = list(multi_day_dic.keys())
            keys_to_delete = []
            for uidd in uids_to_process:
                multi_day_dic[uidd] -= 1
                cur = con.cursor()
                cur.execute(f'SELECT SUMMARY, DESCRIPTION, CATEGORIES, DTSTART, DTEND, DTSTARTZID FROM termine WHERE UID="{uidd}";')
                termin2 = cur.fetchall()
                if termin2:
                    SUMMARY = termin2[0][0]
                    DESCRIPTION = termin2[0][1]
                    cat = termin2[0][2]
                    status_day = 'between'
                    DTSTART = termin2[0][3]
                    DTEND = termin2[0][4]
                    DTSTARTZID = termin2[0][5]

                    if date not in all_termins:
                        all_termins[date] = []

                    DTSTARTs = parse_datetime(DTSTART, DTSTARTZID)
                    dt_rr_start = DTSTARTs.replace(year=y, month=m, day=d, hour=0, minute=0, second=0)
                    DTENDs = parse_datetime(DTEND, DTSTARTZID)
                    dt_rr_end = DTENDs.replace(year=y, month=m, day=d, hour=0, minute=0, second=0)

                    all_termins[date].append([uidd, dt_rr_start, dt_rr_end, SUMMARY, DESCRIPTION, cat, status_day, date])

                    if multi_day_dic[uidd] <= 0:
                        keys_to_delete.append(uidd)
            # del after iter
            for uidd in keys_to_delete:
                del multi_day_dic[uidd]

def check_termin_at_date(date):
    string_to_insert = ''
    farbecode = '#E8E8E8'
    DTSTART = ''
    DTEND = ''
    SUMMARY = ''
    DESCRIPTION = ''
    UID = ''

    y = int(date[:4])
    m = int(date[4:6])
    d = int(date[6:])

    between(date, y, m, d)
    insert_rr_freq_termins(y, m, d)

    with con:
        cur = con.cursor()
        cur.execute(f"""
        SELECT * FROM (
            SELECT
                DTSTART,
                DTEND,
                SUMMARY,
                DESCRIPTION,
                UID,
                CATEGORIES,
                DTSTARTZID,
                CASE
                    WHEN DTSTART LIKE "%{date}%" AND DTEND LIKE "%{date}%" THEN 'sameday'
                    WHEN DTSTART LIKE "%{date}%" AND DTEND NOT LIKE "%{date}%" THEN 'startonday'
                    WHEN DTEND LIKE "%{date}%" AND DTSTART NOT LIKE "%{date}%" THEN 'endonday'
                END AS DateStatus
            FROM
                termine
        ) AS subquery
        WHERE DateStatus IS NOT NULL ORDER BY DTSTART ASC;
        """)

        result=cur.fetchall()
        if result:
            for termin in result:
                
                DTSTART = termin[0]
                DTEND = termin[1]
                SUMMARY = termin[2][:25]
                DESCRIPTION = termin[3][:30]
                UID = termin[4]
                cat = termin[5]
                DTSTARTZID = termin[6]
                status_day = termin[7]
                if date not in all_termins:
                    all_termins[date] = []
                DTSTARTs = parse_datetime(DTSTART, DTSTARTZID)
                DTENDs = parse_datetime(DTEND, DTSTARTZID)
                all_termins[date].append([UID, DTSTARTs, DTENDs, SUMMARY, DESCRIPTION, cat, status_day, date])
#check_termin_at_date('20240110')

def insert_termin(UID, DTSTAMP=None, CREATED=None, LASTMODIFIED=None, DTSTARTZID=None, DTSTART=None,
         DTEND=None, SUMMARY=None, DESCRIPTION=None, LOCATION=None, GEO=None,
         ORGANIZER=None, ATTENDEE=None, URL=None, STATUS=None, VALARM=None,
         RRULE=None, RRULEND=None, RRULEXTRA=None, CLASS=None, TRANSP=None, PRIORITY=None, CATEGORIES=None,
         ATTACH=None, ATTACH2=None, TMP=None):
    with con:
        cur = con.cursor()
        insert_into_table = (
            '"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", '
            '"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", '
            '"{}", "{}", "{}", "{}", "{}", "{}"'.format(
                UID, DTSTAMP, CREATED, LASTMODIFIED, DTSTARTZID, DTSTART, DTEND, SUMMARY,
                DESCRIPTION, LOCATION, GEO, ORGANIZER, ATTENDEE, URL, STATUS,
                VALARM, RRULE, RRULEND, RRULEXTRA, CLASS, TRANSP, PRIORITY, CATEGORIES, ATTACH,
                ATTACH2, TMP
            )
        )
        sql_prompt = (
            "INSERT OR REPLACE INTO termine ("
            "UID, DTSTAMP, CREATED, LASTMODIFIED, DTSTARTZID, DTSTART, DTEND, SUMMARY, DESCRIPTION, "
            "LOCATION, GEO, ORGANIZER, ATTENDEE, URL, STATUS, VALARM, RRULE, RRULEND, RRULEXTRA, CLASS, "
            "TRANSP, PRIORITY, CATEGORIES, ATTACH, ATTACH2, TMP"
            ") VALUES ({});".format(insert_into_table)
        )
        cur.execute(sql_prompt)

def sql_dump():
    cur = con.cursor()
    cur.execute("SELECT * FROM termine ORDER BY DTSTART ASC")
    rows = cur.fetchall()
    html = """
    <table>
    """

    columns = [description[0] for description in cur.description]
    html += "<tr>" + "".join(f"<th>{column}</th>" for column in columns) + "</tr>"
    for row in rows:
        uid = row[0]
        html += "<tr>"
#        html += f"<td><input type='button' value='Insert' onclick='senden(); setTimeout(function() {{ window.location.href=\"month.html\"; }}, 1000);'></td>"
        html += f"""<td> <a href="caldit://goto_termin?UID={uid}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;">{uid}</a></td>"""
        html += "".join(f"<td>{cell}</td>" for cell in row[1:])  # Rest der Zellen
        html += "</tr>"
    html += "</table>"
    con.close()
    return html

def create_single_site(UID, DTSTAMP=None, CREATED=None, LASTMODIFIED=None, DTSTARTZID=None, DTSTART=None,
         DTEND=None, SUMMARY=None, DESCRIPTION=None, LOCATION=None, GEO=None,
         ORGANIZER=None, ATTENDEE=None, URL=None, STATUS=None, VALARM=None,
         RRULE=None, RRULEND=None, RRULEXTRA=None, CLASS=None, TRANSP=None, PRIORITY=None, CATEGORIES=None,
         ATTACH=None, ATTACH2=None, TMP=None):
    head = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Caldit</title>
<style>
body {
    font-family: Arial, sans-serif;
    background-color: #696969;
}
input[type="text"], select {
    width: 97%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
}
input[type="button"] {
    background-color: #3D3D3D;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
    width: 97%;
}
textarea {
    height: 110px;
}
.grid-container {
    display: grid;
    gap: 4px;
    margin: 4px;
}
.grid-container.first-two-rows {
    grid-template-columns: repeat(3, 1fr);
}
.grid-container.next-two-a {
    grid-template-columns: repeat(1, 2fr);
}
.grid-container.next-two-disc {
    grid-template-columns: repeat(3, 1fr);
}
.grid-container.buttons {
    grid-template-columns: repeat(4, 1fr);
}
.description {
    text-align: center;
    font-size: 12px;
    color: #C45137;
    font-family: "Courier New", Courier, monospace;
    margin-bottom: 0px;
}
*{
background: #494949;
color: #E8E8E8;
border-color: #696969;
}
::placeholder {
    color: #FACADE;
}
table {
    border-collapse: collapse;
    font-family: monospace;
    width: 100%;
}
th, td {
    border: 1px solid #ddd;
    padding: 2px;
    border-color: #696969;
}
th {
    padding-top: 2px;
    padding-bottom: 2px;
    text-align: left;
    background-color: #696969;
}
</style>
</head>
"""
    body = f"""
<body>
<form id="meinFormular">
  <div class="grid-container first-two-rows">
    <div class="description">LASTMODIFIED</div>
    <div class="description">CATEGORIES</div>
    <div class="description">CREATED</div>
    <input type="text" id="LASTMODIFIED" name="LASTMODIFIED" placeholder="LASTMODIFIED" value="{ LASTMODIFIED if LASTMODIFIED else '' }">
    <input type="text" id="CATEGORIES" name="CATEGORIES" placeholder="CATEGORIES" value="{ CATEGORIES if CATEGORIES else '' }">
    <input type="text" id="CREATED" name="CREATED" placeholder="CREATED" value="{ CREATED if CREATED else '' }">
    <div class="description">ORGANIZER</div>
    <div class="description">ATTENDEE</div>
    <div class="description">ATTACH</div>
    <input type="text" id="ORGANIZER" name="ORGANIZER" placeholder="ORGANIZER" value="{ ORGANIZER if ORGANIZER else '' }">
    <input type="text" id="ATTENDEE" name="ATTENDEE" placeholder="ATTENDEE" value="{ ATTENDEE if ATTENDEE else '' }">
    <input type="text" id="ATTACH" name="ATTACH" placeholder="https://example.com/dokument.pdf" value="{ ATTACH if ATTACH else '' }">
    <div class="description">DTSTART</div>
    <div class="description">DTEND</div>
    <div class="description">TZID</div>
    <input type="text" id="DTSTART" name="DTSTART" placeholder="DTSTART" value="{ DTSTART if DTSTART else '' }">
    <input type="text" id="DTEND" name="DTEND" placeholder="DTEND" value="{ DTEND if DTEND else '' }">
    <input type="text" id="DTSTARTZID" name="DTSTARTZID" placeholder="Africa/Cairo" value="{ DTSTARTZID if DTSTARTZID else 'Europe/Paris' }">
  </div>
  <div class="grid-container next-two-a">
    <div class="description">SUMMARY</div>
    <input type="text" id="SUMMARY" name="SUMMARY" placeholder="SUMMARY" value="{ SUMMARY if SUMMARY else '' }">
  </div>
  <div class="grid-container first-two-disc">
    <div class="description">DESCRIPTION</div>
    <textarea id="DESCRIPTION" name="DESCRIPTION" placeholder="DESCRIPTION">{ DESCRIPTION if DESCRIPTION else '' }</textarea>
  </div>
  <div class="grid-container first-two-rows">
    <div class="description">LOCATION</div>
    <div class="description">GEO</div>
    <div class="description">URL</div>
    <input type="text" id="LOCATION" name="LOCATION" placeholder="Panoramapunkt 2" value="{ LOCATION if LOCATION else '' }">
    <input type="text" id="GEO" name="GEO" placeholder="29.9753;31.1376" value="{ GEO if GEO else '' }">
    <input type="text" id="URL" name="URL" placeholder="URL" value="{ URL if URL else '' }">
    <div class="description">UID</div>
    <div class="description">DTSTAMP</div>
    <div class="description">TRANSP</div>
    <input type="text" id="UID" name="UID" placeholder="UID" value="{ UID if UID else '' }">
    <input type="text" id="DTSTAMP" name="DTSTAMP" placeholder="DTSTAMP" value="{ DTSTAMP if DTSTAMP else '' }">
    <input type="text" id="TRANSP" name="TRANSP" placeholder="OPAQUE" value="{ TRANSP if TRANSP else '' }">
    <div class="description">PRIORITY</div>
    <div class="description">STATUS</div>
    <div class="description">VALARM</div>
    <input type="text" id="PRIORITY" name="PRIORITY" placeholder="PRIORITY" value="{ PRIORITY if PRIORITY else '' }">
    <input type="text" id="STATUS" name="STATUS" placeholder="STATUS" value="{ STATUS if STATUS else '' }">
    <input type="text" id="VALARM" name="VALARM" placeholder="&#123;&#39;TRIGGER&#39;: &#39;-PT15M&#39;, &#39;ACTION&#39;: &#39;DISPLAY&#39;, &#39;DESCRIPTION&#39;: &#39;Ring&#39;&#125;" value="{ VALARM if VALARM else '' }">
    <div class="description">RRULE</div>
    <div class="description">RRULEND</div>
    <div class="description">RRULEXTRA</div>
    <input type="text" id="RRULE" name="RRULE" placeholder="FREQ=DAILY WEEKLY YEARLY MINUTELY HOURLY" value="{ RRULE if RRULE else '' }">
    <input type="text" id="RRULEND" name="RRULEND" placeholder="UNTIL=19971224T000000 INTERVAL=2 ;COUNT=10" value="{ RRULEND if RRULEND else '' }">
    <input type="text" id="RRULEXTRA" name="RRULEXTRA" placeholder="WKST=SU; BYDAY=TU,TH BYMONTHDAY=2,15 BYMONTH=6,7 BYHOUR=9,10,11,12," value="{ RRULEXTRA if RRULEXTRA else '' }">
    <div class="description">CLASS</div>
    <div class="description">ATTACH2</div>
    <div class="description">TMP</div>
    <input type="text" id="CLASS" name="CLASS" placeholder="CLASS" value="{ CLASS if CLASS else '' }">
    <input type="text" id="ATTACH2" name="ATTACH2" placeholder="ATTACH2" value="{ ATTACH2 if ATTACH2 else '' }">
    <input type="text" id="TMP" name="TMP" placeholder="TMP" value="{ TMP if TMP else '' }">
  </div>
  <div class="grid-container buttons">
    <input type="button" value="Insert" onclick="senden(); setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
    <input type="button" value="DELETE" onclick="if(confirm('Möchtest du fortfahren?')) senden_del_uid() ; setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
    <input type="button" value="Export" onclick="senden_ex(); setTimeout(function() {{ window.location.href='month.html'; }}, 4000); return true;">
    <input type="button" value="Back" onclick="senden_back(); setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
  </div>
</form>
"""
    sql_dump_html = sql_dump()
    script = """

<script>
function senden_back() {
    var url = "caldit://create?single=yes&";
    window.open(url, '_self');
}
</script>
<script>
function senden_ex() {
    var UID = document.getElementById('UID').value;
    var url = "caldit://export_ics?what=single&" +
              "UID=" + encodeURIComponent(UID);
    window.open(url, '_self');
}
</script>
<script>
function senden_del_uid() {
    var UID = document.getElementById('UID').value;
    var url = "caldit://delete_termin?" +
              "UID=" + encodeURIComponent(UID);
    window.open(url, '_self');
}
</script>
<script>
function senden() {
    var UID = document.getElementById('UID').value;
    var DTSTAMP = document.getElementById('DTSTAMP').value;
    var CREATED = document.getElementById('CREATED').value;
    var LASTMODIFIED = document.getElementById('LASTMODIFIED').value;
    var DTSTARTZID = document.getElementById('DTSTARTZID').value;
    var DTSTART = document.getElementById('DTSTART').value;
    var DTEND = document.getElementById('DTEND').value;
    var SUMMARY = document.getElementById('SUMMARY').value;
    var DESCRIPTION = document.getElementById('DESCRIPTION').value;
    var LOCATION = document.getElementById('LOCATION').value;
    var GEO = document.getElementById('GEO').value;
    var ORGANIZER = document.getElementById('ORGANIZER').value;
    var ATTENDEE = document.getElementById('ATTENDEE').value;
    var URL = document.getElementById('URL').value;
    var STATUS = document.getElementById('STATUS').value;
    var VALARM = document.getElementById('VALARM').value;
    var RRULE = document.getElementById('RRULE').value;
    var RRULEND = document.getElementById('RRULEND').value;
    var RRULEXTRA = document.getElementById('RRULEXTRA').value;
    var CLASS = document.getElementById('CLASS').value;
    var TRANSP = document.getElementById('TRANSP').value;
    var PRIORITY = document.getElementById('PRIORITY').value;
    var CATEGORIES = document.getElementById('CATEGORIES').value;
    var ATTACH = document.getElementById('ATTACH').value;
    var ATTACH2 = document.getElementById('ATTACH2').value;
    var TMP = document.getElementById('TMP').value;

    var url = "caldit://save_termin?" +
              "UID=" + encodeURIComponent(UID) +
              "&DTSTAMP=" + encodeURIComponent(DTSTAMP) +
              "&CREATED=" + encodeURIComponent(CREATED) +
              "&LASTMODIFIED=" + encodeURIComponent(LASTMODIFIED) +
              "&DTSTARTZID=" + encodeURIComponent(DTSTARTZID) +
              "&DTSTART=" + encodeURIComponent(DTSTART) +
              "&DTEND=" + encodeURIComponent(DTEND) +
              "&SUMMARY=" + encodeURIComponent(SUMMARY) +
              "&DESCRIPTION=" + encodeURIComponent(DESCRIPTION) +
              "&LOCATION=" + encodeURIComponent(LOCATION) +
              "&GEO=" + encodeURIComponent(GEO) +
              "&ORGANIZER=" + encodeURIComponent(ORGANIZER) +
              "&ATTENDEE=" + encodeURIComponent(ATTENDEE) +
              "&URL=" + encodeURIComponent(URL) +
              "&STATUS=" + encodeURIComponent(STATUS) +
              "&VALARM=" + encodeURIComponent(VALARM) +
              "&RRULE=" + encodeURIComponent(RRULE) +
              "&RRULEND=" + encodeURIComponent(RRULEND) +
              "&RRULEXTRA=" + encodeURIComponent(RRULEXTRA) +
              "&CLASS=" + encodeURIComponent(CLASS) +
              "&TRANSP=" + encodeURIComponent(TRANSP) +
              "&PRIORITY=" + encodeURIComponent(PRIORITY) +
              "&CATEGORIES=" + encodeURIComponent(CATEGORIES) +
              "&ATTACH=" + encodeURIComponent(ATTACH) +
              "&ATTACH2=" + encodeURIComponent(ATTACH2) +
              "&TMP=" + encodeURIComponent(TMP);

    window.open(url, '_self');
}
</script>
</body>
</html>
"""
    file_path = dbasepath + 'page2.html'
    with open(file_path, 'w') as file:
        page2 = head + body + sql_dump_html + script
        file.write(page2)

# needed 4 rr_freq, create_body
def calc_month_range(year, month):
    first_day = datetime(year, month, 1)
    first_day_weekday = first_day.weekday()
    last_day = first_day.replace(day=calendar.monthrange(year, month)[1])
    last_day_weekday = last_day.weekday()
    scan_von = first_day - timedelta(days=first_day_weekday)
    days_in_next_month = 6 - last_day_weekday
    scan_bis = last_day + timedelta(days=days_in_next_month)
    return scan_von, scan_bis

# gather RRULE Dates for the year
def rr_freq(m, y):
    MONTH = m
    YEAR = y
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS RRULET (UID TEXT, MONTH TEXT, YEAR TEXT, DIC_TERMIN TEXT, RRULE TEXT, DTSTART TEXT, UNIQUE (UID, YEAR));")
        cur.execute(f'SELECT UID FROM RRULET WHERE YEAR="{y}";')
        result1 = cur.fetchall()
        uids_in_result1 = {uid[0] for uid in result1}

        cur = con.cursor()
        cur.execute(f'SELECT UID, DTSTART, RRULE, RRULEND, RRULEXTRA, CATEGORIES, DTSTARTZID FROM termine WHERE RRULE IS NOT NULL AND RRULE != "" AND RRULE != "None";')
        result = cur.fetchall()
        if result:
            datum_1_jan = datetime(y, 1, 1).astimezone()
            datum_31_dez = datetime(y, 12, 31).astimezone()
            for termin in result:
                if termin[0] not in uids_in_result1:
                    if verbose > 2: logging.info("in rr result 2 insert found AND termin[0] not in uids_in_result1: ")
                    try:

                        DIC_TERMIN = {}
                        UID = termin[0]
                        DTSTARTR = termin[1]
                        ics_rule = "RRULE:" + termin[2]
                        RRULEND = termin[3]
                        RRULEXTRA = termin[4]
                        DTSTARTZID = termin[6]
                        UNTIL = ''
                        date_obj_start = parse_datetime(DTSTARTR, DTSTARTZID)
                        if date_obj_start < datum_31_dez:
                            if RRULEND not in ["None", "", None]:
                                ics_rule += ';' + RRULEND
                            if RRULEXTRA not in ["None", "", None]:
                                ics_rule +=  ';' + RRULEXTRA

                            has_until = 'UNTIL=' in ics_rule

                            if 'UNTIL=' in ics_rule:
                                parts = ics_rule.split('UNTIL=')
                                UNTIL = parts[1]
                                temp = ''
                                if len(parts) > 2:
                                    UNTIL = parts[1].split(';')[0]
                                    temp  = parts[2]
                                if not DTSTARTR.endswith('Z'):
                                     UNTIL = UNTIL + 'Z'
                                ics_rule = parts[0] + 'UNTIL=' + UNTIL + temp

                                rrule_obj = rrulestr(ics_rule, dtstart=date_obj_start)
                                all_occurrences = list(rrule_obj)
                                if all_occurrences:
                                    if all_occurrences[-1] > datum_1_jan:
                                        for occ in all_occurrences:
                                            if UID not in DIC_TERMIN:
                                                DIC_TERMIN[UID] = []
                                            DIC_TERMIN[UID].append(occ)

                                            if occ > datum_31_dez:
                                                break
                                    else:
                                        DIC_TERMIN[UID] = ['no']
                            rrule_obj = rrulestr(ics_rule, dtstart=date_obj_start)

                            has_count = 'COUNT=' in ics_rule
                            if has_count:
                                all_occurrences = list(rrule_obj)
                                if all_occurrences:
                                    for occ in all_occurrences:
                                        if UID not in DIC_TERMIN:
                                            DIC_TERMIN[UID] = []
                                        DIC_TERMIN[UID].append(occ)

                            # forever
                            if not has_count and not has_until:
                                occurrences = list(rrule_obj)
                                for occ in occurrences:
                                    if verbose > 2: logging.info("in rr forever occ compt")
                                    if datum_1_jan <= occ <= datum_31_dez:
                                        if UID not in DIC_TERMIN:
                                            DIC_TERMIN[UID] = []
                                        DIC_TERMIN[UID].append(occ)
                                    else:
                                        if occ > datum_31_dez:
                                            break

                            if len(DIC_TERMIN.get(UID, [])) == 0:
                                DIC_TERMIN[UID] = ['no']

                            cur = con.cursor()
                            insert_into_table = (
                                '"{}", "{}", "{}", "{}", "{}", "{}"'.format(
                                    UID, MONTH, YEAR, DIC_TERMIN, ics_rule, DTSTARTR
                                )
                            )
                            sql_prompt = (
                                "INSERT OR REPLACE INTO RRULET ("
                                "UID,  MONTH, YEAR, DIC_TERMIN, RRULE, DTSTART"
                                ") VALUES ({});".format(insert_into_table)
                            )
                            cur.execute(sql_prompt)

                        else:
                            DIC_TERMIN[UID] = ['no']

                            cur = con.cursor()
                            insert_into_table = (
                                '"{}", "{}", "{}", "{}", "{}", "{}"'.format(
                                    UID, MONTH, YEAR, DIC_TERMIN, ics_rule, DTSTARTR
                                )
                            )
                            sql_prompt = (
                                "INSERT OR REPLACE INTO RRULET ("
                                "UID,  MONTH, YEAR, DIC_TERMIN, RRULE, DTSTART"
                                ") VALUES ({});".format(insert_into_table)
                            )
                            cur.execute(sql_prompt)

                    except Exception as e:
                        if verbose > 1: logging.info(f" rr_freq  except Exception as e: {e} " )

        else:
            return 0

def create_body2(m, y, mode='none', kw=1):
    scan_von, scan_bis = calc_month_range(y, m)
    html_days = []
    UID2 = 'UIDcalldit' + scan_time
    tage_differenz = (scan_bis - scan_von).days
    teest = kw
    if mode == 'Week':
        first_day_of_year = datetime(y, 1, 1)
        first_monday = first_day_of_year + timedelta(days=(7-first_day_of_year.weekday()) % 7)
        scan_von = first_monday + timedelta(weeks=kw-1)
#        html_days.append(f"""<div style="display: flex; grid-column: span 7;">KW: <input type="text" id="kw" name="kw" value="{kw}" style="font-size: 16px; flex-grow: 1;">""")
        html_days.append(f"""<div style="display: flex; grid-column: span 2;"><input type="text" id="kw" name="kw" value="{kw}" style="font-size: 16px;">""")
        html_days.append("""<input type="button" value="KW" onclick="senden_kw(); setTimeout(function() { window.location.href='month.html'; }, 2000); return true;"></div>
<script>
function senden_kw() {
    var datum = document.getElementById('datum').value;
    var kw = document.getElementById('kw').value;
    var url = "caldit://refresh_site?" +
              "datum=" + encodeURIComponent(datum) +
              "&go=" + 'gokw' +
              "&kw=" + encodeURIComponent(kw) ;
    window.open(url, '_self');
}
</script>""")

        days_range = range(7)
    else:
        days_range = range(tage_differenz + 1)

    html_days.append(f'<div class="calendar"><div class="header">Mo</div><div class="header">Di</div><div class="header">Mi</div><div class="header">Do</div><div class="header">Fr</div><div class="header">Sa</div><div class="header">So</div> ')
    for i in days_range:
        day = scan_von + timedelta(days=i)
        day_t = day.day
        day_YYYYMMDD = day.strftime('%Y%m%d')
        termin = check_termin_at_date(day_YYYYMMDD)
        string_to_insert = ''

        if day_YYYYMMDD in all_termins:
            all_termins[day_YYYYMMDD] = sorted(all_termins[day_YYYYMMDD], key=lambda item: item[1])

            for termina in all_termins[day_YYYYMMDD]:
                SUMMARY  = ''
                DESCRIPTION = ''
                DTSTART = ''
                DTEND = ''
                cat = ''
                UID = termina[0]
                DTSTART = termina[1]
                DTEND = termina[2]
                SUMMARY = termina[3][:15]
                DESCRIPTION = termina[4][:15]
                cat = termina[5]
                status_day = termina[6]
                farbcode = '#E8E8E8'

                if cat in cat_farbcodes:
                    farbcode = cat_farbcodes[cat]

                if DTSTART == DTEND:
                    DTSTART = 'Today'
                    DTEND = ''

                elif status_day == 'sameday':
                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'startonday':
                    start_time = DTSTART
                    end_time = DTEND
                    difference =  end_time - start_time
                    multi_day_dic[UID] = difference.days - 1

                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.day:02d}.{DTEND.month:02d} {DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'endonday':
                    DTSTART = f'{DTSTART.day:02d}.{DTSTART.month:02d} {DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'RR':
                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'

                string_to_insert += f"""<div class="night">  <a href="caldit://goto_termin?UID={UID}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color:#41A338;">{DTSTART}</span>-<span style="color:#F67C30;">{DTEND}</span><br><span style="color:{farbcode};">{SUMMARY}<br>{DESCRIPTION}</span></a></div>"""

        day_class = "day"

        if str(day_t) + str(m) == str(int(time.strftime("%d"))) + str(int(time.strftime("%m"))):
            day_class = '"day" style="background: #696969;"'
        farbcode = '#E8E8E8'
        if day.month != m and mode != 'Week':
            farbcode = '#C45137'

        day_html =  f""" <div class={day_class}> <a href="caldit://entry_termin?UID={UID2}&DTSTART={day_YYYYMMDD + "T001122"}&CREATED={day_YYYYMMDD}&DTEND={day_YYYYMMDD + "T223344"}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color: {farbcode};">{day_t} </span></a> {string_to_insert} </div>"""
        html_days.append(day_html)

    html_days_str = "\n".join(html_days)
    return html_days_str

def create_body(m, y):
    wochentag_mapping = {
        'Mon': 'Mo',
        'Tue': 'Di',
        'Wed': 'Mi',
        'Thu': 'Do',
        'Fri': 'Fr',
        'Sat': 'Sa',
        'Sun': 'So'
    }

    html_days = []
    UID2 = 'UIDcalldit' + scan_time
    startday, num_days = calendar.monthrange(y, m)
    month_name = calendar.month_name[m]
    html_grid = f"""
    <div style='display: grid; grid-template-columns: repeat({1}, 1fr);'><span style="text-align: center;">{month_name}</span> </div>
    <div style='display: grid; grid-template-columns: repeat({num_days}, 1fr);'>
"""
    html_days.append(html_grid)
    for day in range(1, num_days + 1):
        wochentag_abkuerzung = calendar.day_abbr[startday]
        if wochentag_abkuerzung == 'Tue' or 'Wed' or 'Thu' or 'Sun':
            wochentag_abkuerzung = wochentag_mapping[wochentag_abkuerzung]
        day_YYYYMMDD = f'{y}{m:02d}{day:02d}'
        termin = check_termin_at_date(day_YYYYMMDD)
        string_to_insert = ''
        startday += 1
        if startday == 7:
            startday = 0
#        count_termins = 0
        if day_YYYYMMDD in all_termins:
            all_termins[day_YYYYMMDD] = sorted(all_termins[day_YYYYMMDD], key=lambda item: item[1])

            for termina in all_termins[day_YYYYMMDD]:
#                count_termins += 1
#                if count_termins > 5:
#                    break
                SUMMARY  = ''
                DESCRIPTION = ''
                DTSTART = ''
                DTEND = ''
                cat = ''
                UID = termina[0]
                DTSTART = termina[1]
                DTEND = termina[2]
                SUMMARY = termina[3][:10]
                DESCRIPTION = termina[4][:10]
                cat = termina[5]
                status_day = termina[6]
                farbcode = '#E8E8E8'

                if cat in cat_farbcodes:
                    farbcode = cat_farbcodes[cat]

                if DTSTART == DTEND:
                    DTSTART = 'Today'
                    DTEND = ''

                elif status_day == 'sameday':
                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'startonday':
                    start_time = DTSTART
                    end_time = DTEND
                    difference =  end_time - start_time
                    multi_day_dic[UID] = difference.days - 1

                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.day:02d}.{DTEND.month:02d} {DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'endonday':
                    DTSTART = f'{DTSTART.day:02d}.{DTSTART.month:02d} {DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'

                elif status_day == 'RR':
                    DTSTART = f'{DTSTART.hour:02d}:{DTSTART.minute:02d}'
                    DTEND = f'{DTEND.hour:02d}:{DTEND.minute:02d}'
#<br>{DESCRIPTION}
                string_to_insert += f"""<div class="night_year">  <a href="caldit://goto_termin?UID={UID}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color:#41A338;">{DTSTART}</span>-<span style="color:#F67C30;">{DTEND}</span><br><span style="color:{farbcode};">{SUMMARY}</span></a></div>"""

        day_class = "day"
        farbcode = '#E8E8E8'
        if wochentag_abkuerzung == 'Sa' or wochentag_abkuerzung == 'So':
            farbcode = '#C45137'

        day_html =  f""" <div class=day> <a href="caldit://entry_termin?UID={UID2}&DTSTART={day_YYYYMMDD + "T001122"}&CREATED={day_YYYYMMDD}&DTEND={day_YYYYMMDD + "T223344"}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color: {farbcode};">{day} {wochentag_abkuerzung}</span></a>{string_to_insert}</div>"""
        html_days.append(day_html)

    html_days.append('</div>')
    html_days_str = "\n".join(html_days)
    return html_days_str

def create_year(y):
    ppp = ''
    for i in range(1, 13):
        ppp += create_body(i, y)
    return ppp

def create_month(m, y, mode='Month', kw=0):
    modee = mode
    navigate_go_left = 'go_left'
    navigate_go_right = 'go_right'
    navigate_go_Week = 'Week'
    if modee == 'Month':
        modee = 'Year'
    elif modee == 'Year':
        modee = 'Month'
        navigate_go_left = 'go_left_year'
        navigate_go_right = 'go_right_year'
    elif modee == 'Week':
        modee = 'Month'
        navigate_go_left = 'go_left_week'
        navigate_go_right = 'go_right_week'
        navigate_go_Week = 'Year'

    monat = m
    year = y
    head = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'><rect x='3' y='3' width='28' height='28' fill='none' stroke='grey' stroke-width='3' rx='2' ry='2' /><circle cx='11' cy='7' r='4' fill='none' stroke='grey' stroke-width='2' /><circle cx='23' cy='7' r='4' fill='none' stroke='grey' stroke-width='2' /><line x1='4' y1='12' x2='31' y2='12' stroke='grey' stroke-width='3' /><path d='M 20 11 A 5 5 0 0 0 18 27' fill='none' stroke='grey' stroke-width='4' /><line x1='4' y1='27' x2='31' y2='27' stroke='grey' stroke-width='2' /></svg>">
<title>Monat</title>
<style>
.calendar {
    display: grid;
    grid-template-columns: repeat(7, 1fr); /* 7 Spalten für die Wochentage */
    grid-gap: 5px;
    margin: auto;
}
.header {
    font-weight: bold;
    text-align: center;
    background: #696969;
}
.day {
    border: 1px solid #ddd;
    text-align: center;
    padding: 1px;
    grid-row: span 3;
    border-color: #696969;
}
.night {
    border: 1px solid #ddd;
    text-align: left;
    padding: 1px;
    grid-row: span 3;
    border-color: #696969;
}
.night_year {
    border: 1px solid #ddd;
    text-align: left;
    padding: 0px;
    border-color: #696969;
    font-size: 9px;
}
a {
  text-decoration: none;
}
*{
background: #494949;
color: #E8E8E8;
border-color: #696969;
}
input[type="text"], select {
    border: 1px solid #696969;
    min-width: 30px;
}
input[type="button"] {
    background-color: #3D3D3D;
    cursor: pointer;
    font-size: 16px;
    min-width: 30px;
}
.lineone {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    margin: 1px;
}
.year {
    display: grid;
    grid-template-columns: repeat(31, 1fr);
    margin: 1px;
}
</style>
</head>
<body>
<form id="meinFormular2" class="lineone">
<input type="button" value="&larr;" onclick="senden_ref(\'%s\'); setTimeout(function() { window.location.href='month.html'; }, 2000); return true;">
<input type="text" id="datum" name="datum" value="%s" style="text-align: center; font-size: 18px;">
<input type="button" value="Refresh" onclick="senden_ref('no'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
<input type="button" value="%s" onclick="senden_ref(\'%s\'); setTimeout(function() { window.location.href='month.html'; }, 3000); return true;"> 
<input type="button" value="%s" onclick="senden_ref(\'%s\'); setTimeout(function() { window.location.href='month.html'; }, 3000); return true;"> 
<input type="text" id="optins_ex_cat" name="optins_ex_cat"  placeholder="CATEGORIES:birthday" value="/home/debian/combobox.ics"> 
<div style="display: flex; grid-column: span 2;">
<input type="button" value="Import" style="flex-grow: 1;" onclick="import_ics(); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;"> 
<input type="button" value="Export filter" style="flex-grow: 1;" onclick="export_ics('cat'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
<input type="button" value="Export All" style="flex-grow: 1;" onclick="export_ics('all'); setTimeout(function() { window.location.href='month.html'; }, 4000); return true;"> 
</div>
<div style="display: grid; grid-template-columns: span 1;">
<input type="button" value="&rarr;" onclick="senden_ref(\'%s\'); setTimeout(function() { window.location.href='month.html'; }, 2000); return true;">
</div>
</form>
<script>
function senden_ref(input) {
    var datum = document.getElementById('datum').value;
    var test = \'%s\'
    var mode = \'%s\'
    var url = "caldit://refresh_site?" +
              "datum=" + encodeURIComponent(datum) +
              "&go=" + encodeURIComponent(input) +
              "&kw=" + test +
              "&mode=" + mode;
    window.open(url, '_self');
}
</script>
<script>
function export_ics(input) {
    var optins_ex_cat = document.getElementById('optins_ex_cat').value;
    var url = "caldit://export_ics?" +
              "optins_ex_cat=" + encodeURIComponent(optins_ex_cat) +
              "&what=" + encodeURIComponent(input);
    window.open(url, '_self');
}
</script>
<script>
function import_ics() {
    var optins_ex_cat = document.getElementById('optins_ex_cat').value;
    var url = "caldit://import_ics?" +
              "optins_ex_cat=" + encodeURIComponent(optins_ex_cat);
    window.open(url, '_self');
}
</script>
""" % (navigate_go_left, str(monat) + '.' + str(year), modee, modee, navigate_go_Week, navigate_go_Week, navigate_go_right, str(kw), mode)
    if mode == 'Year':
        body_insert = create_year(year)
    elif mode == 'Week':
        body_insert = create_body2(monat, year, mode, kw)
    else:
        body_insert = create_body2(monat, year)
    tail = """
</div>
</body>
</html>
"""
    month_created = head + body_insert + tail
    file_path = dbasepath + 'month.html'
    with open(file_path, 'w') as file:
        file.write(month_created)

# needed 4 import.ics
def read_cal_file(file_path):
    event_start = "BEGIN:VEVENT"
    event_end = "END:VEVENT"
    valarm_start = "BEGIN:VALARM"
    valarm_end = "END:VALARM"
    termine = []
    current_event = None
    inside_valarm = False
    valarm_info = {}

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if event_start in line:
                current_event = {}
            elif event_end in line and current_event is not None:
                if valarm_info:
                    current_event['VALARM'] = valarm_info
                termine.append(current_event)
                current_event = None
                valarm_info = {}
            elif valarm_start in line:
                inside_valarm = True
            elif valarm_end in line and inside_valarm:
                inside_valarm = False
            elif current_event is not None:
                key_val = line.split(':', 1)
                if len(key_val) >= 2:
                    if inside_valarm:
                        valarm_info[key_val[0]] = key_val[1]
                    else:
                        current_event[key_val[0]] = key_val[1]
    return termine

def read_and_insert_ics_file(ics_file_path):
    valid_entries = ["UID", "DTSTAMP", "CREATED", "LASTMODIFIED", "DTSTARTZID", "DTSTART", "DTEND", "SUMMARY", "DESCRIPTION", "LOCATION", "GEO", "ORGANIZER", "ATTENDEE", "URL", "STATUS", "VALARM", "RRULE", "RRULEND", "RRULEXTRA", "CLASS", "TRANSP", "PRIORITY", "CATEGORIES", "ATTACH", "ATTACH2"]

    termine = read_cal_file(ics_file_path)
    for termin in termine:
        current_termin = {}
        TMP = []
        inside_valarm = False
        valarm_info = []

        for key, value in termin.items():
            if key == 'LAST-MODIFIED':
                current_termin['LASTMODIFIED'] = value

            elif key.startswith('DTSTART;'):
                _, tzid = key.split(';', 1)
                current_termin['DTSTARTZID'] = tzid
                current_termin['DTSTART'] = value

            elif key == 'DTSTART':
                current_termin['DTSTART'] = value
                current_termin['DTSTARTZID'] = None

            elif key.startswith('DTEND;'):
                _, tzid = key.split(';', 1)
                current_termin['DTEND'] = value

            elif key == 'DTEND':
                current_termin['DTEND'] = value

            elif key == 'RRULE':
                parts = value.split(';', 2)

                while len(parts) < 3:
                    parts.append('')
                for item in parts:
                    if item.startswith('FREQ='):
                        current_termin['RRULE'] = item
                    if item.startswith('UNTIL=') or item.startswith('COUNT') or item.startswith('INTERVAL'):
                        current_termin['RRULEND'] = item
                    if item.startswith('BY') or item.startswith('WKST'):
                        current_termin['RRULEXTRA'] = item

            elif key == 'BEGIN' and value == 'VALARM':
                inside_valarm = True
            elif key == 'END' and value == 'VALARM':
                inside_valarm = False
                # VALARM als String zu 'current_termin'
                current_termin['VALARM'] = ' '.join(valarm_info)
                valarm_info = []
            elif inside_valarm:
                if key != 'DESCRIPTION':
                    valarm_info.append(f"{key}={value}")
            else:
                for valid_key in valid_entries:
                    if key.startswith(valid_key):
                        current_termin[valid_key] = value
                        found = True
                        break

                if not found:
                    TMP.append(key)

        insert_termin(**current_termin, TMP=TMP)

def export_to_ics_file(mode, UID=None):
    if mode == 'single':
        file_path = f"{dbasepath}backup{UID}{scan_time}.ics"
    if mode == 'all':
        file_path = f"{dbasepath}backup{scan_time}.ics"
    if mode != 'all' and mode != 'single':
        file_path = f"{dbasepath}backupfiltered{scan_time}.ics"
        try:
            split_mode = mode.split(':')
            first_arg = split_mode[0]
            second_arg = split_mode[1]
        except (IndexError):
            first_arg = mode
            second_arg = '*'

    with open(file_path, 'w') as file:
        head = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ThisisSparta//Caldit//DE

NAME:Caldit
X-WR-CALNAME:Caldit
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VTIMEZONE
TZID:{local_time_zone}
BEGIN:STANDARD
DTSTART:20201025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
END:STANDARD
BEGIN:DAYLIGHT
DTSTART:20200329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
END:DAYLIGHT
END:VTIMEZONE

"""
        file.write(head)
        with con:
            cur = con.cursor()
            cur.execute(f"PRAGMA table_info(termine)")
            available_columns = [row[1] for row in cur.fetchall()]

            if 'TMP' in available_columns:
                available_columns.remove('TMP')

            if mode == "single":
                cur.execute(f'SELECT * FROM termine where UID="{UID}"')
            if mode == "all":
                cur.execute(f'SELECT * FROM termine')
            if mode != 'all' and mode != 'single':
                cur.execute(f'SELECT * FROM termine where {first_arg}="{second_arg}"')
            result = cur.fetchall()
            if result:
                for termin in result:
                    file.write("BEGIN:VEVENT\n")

                    for col, val in zip(available_columns, termin):
                        if val is not None and val != 'None' and val != '':
                            if col == 'LASTMODIFIED':
                                col = 'LAST-MODIFIED'
                            if col == 'VALARM':
                                try:
                                    # Versuche, die Zeichenkette in ein Dictionary umzuwandeln
                                    valarm_dict = ast.literal_eval(val)
                                    if isinstance(valarm_dict, dict):
                                        # Beginne die VALARM-Komponente
                                        file.write("BEGIN:VALARM\n")
                                        for key, alarm_val in valarm_dict.items():
                                            file.write(f"{key}:{alarm_val}\n")
                                        # Beende die VALARM-Komponente
                                        file.write("END:VALARM\n")
                                except (ValueError, SyntaxError):
                                    if verbose > 2: logging.info(f"VALARM Daten: {val} fehler in export_to_ics_file")

                            else:
                                file.write(f"{col}:{val}\n")
                    file.write("END:VEVENT\n\n")
            file.write("END:VCALENDAR\n")

# needed 4 caldit://goto_termin
def single_termin_as_dic(UID):
    with con:
        cur = con.cursor()
        cur.execute(f"PRAGMA table_info(termine);")
        table_columns_info = cur.fetchall()

        cur.execute(f'SELECT * FROM termine WHERE UID="{UID}";')
        row_values = cur.fetchone()

        result_dict = {}
        for column_info, value in zip(table_columns_info, row_values):
            column_name = column_info[1]
            if value is not None and value != ''and value != 'None':
                result_dict[column_name] = value

        if verbose > 1: logging.info(f"single_termin_as_dic erfolgreich .result_dict  {result_dict}.")
        return result_dict

def delete_termin(termin_uid):
    with con:
        cur = con.cursor()
        sql = f'DELETE FROM termine WHERE UID ="{termin_uid}"'
        cur.execute(sql)
        try:
            cur = con.cursor()
            sql = f'DELETE FROM RRULET WHERE UID ="{termin_uid}"'
            cur.execute(sql)
        except:
            con.commit()

def parse_custom_url(url):
    parts = url.split('?')
    base = parts[0]
    if os.name == 'nt':
        base = base[:-1]
    params = parts[1] if len(parts) > 1 else ''

    param_dict = {}
    if params:
        pairs = params.split('&')
        for pair in pairs:
            key, value = pair.split('=')
            param_dict[key] = value

    return base, param_dict

def start():
    # Das erste Pfad zum Skript, das zweite ist die URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
        base, params = parse_custom_url(url)
        param_dict = {}
        for key, value in params.items():
            param_dict[key] = unquote(value)

        UID = param_dict.get('UID', '19841201')
        m = int(time.strftime("%m"))
        y = int(time.strftime("%Y"))

        if verbose > 0: logging.info(f"started params dic = {param_dict}  base = {base}")

        if base == 'caldit://goto_termin':
            single_termin_dic = single_termin_as_dic(UID)
            create_single_site(**single_termin_dic)

        elif base == 'caldit://entry_termin':
            created = param_dict.get('CREATED', None)
            dtend = param_dict.get('DTEND', None)
            dtstart = param_dict.get('DTSTART', '19841201')
            create_single_site(UID, DTSTART=dtstart, CREATED=created, DTEND=dtend)

        elif base == 'caldit://save_termin':
            insert_termin(**param_dict)
            created = param_dict.get('CREATED', '20240606')
            y = int(created[:4])
            m = int(created[4:6])
            create_month(m, y)

        elif base == 'caldit://delete_termin':
            delete_termin(UID)
            create_month(m, y)

        elif base == 'caldit://import_ics':
            import_path = param_dict['meineDatei']
            read_and_insert_ics_file(import_path)
            if verbose > 2: logging.info(f" import_path {import_path} ")

        elif base == 'caldit://export_ics':
            optins_ex_cat = param_dict.get('optins_ex_cat', 'UID:*')
            what = param_dict.get('what', 'all')

            if what == "single":
                export_to_ics_file('single', UID)
            elif what == "cat":
                export_to_ics_file(optins_ex_cat)
            elif what == "all":
                export_to_ics_file("all")

        elif base == 'caldit://create':
            if verbose > 2: logging.info("create_month started")
            create_month(m, y)

        elif base == 'caldit://refresh_site':
            go = param_dict.get('go', 'no')
            month_too_refresh = param_dict.get('datum', '11.2024')
            today = datetime.now()
            kw_now = today.isocalendar()[1] 
            kw = int(param_dict.get('kw', kw_now))
            m = int(month_too_refresh.split('.')[0])
            y = int(month_too_refresh.split('.')[1])
            mode = 'Month'

            if go == 'go_left':
                m = m - 1
                if m < 1:
                    m = 12
                    y = y - 1
            elif go == 'go_right':
                m = m + 1
                if m > 12:
                    m = 1
                    y = y + 1

            elif go == 'gokw':
                mode = 'Week'

            elif go == 'Year':
                mode = 'Year'
            elif go == 'go_left_year':
                y = y - 1
                mode = 'Year'
            elif go == 'go_right_year':
                y = y + 1
                mode = 'Year'

            elif go == 'Week':
                mode = 'Week'
                kw = kw_now
            elif go == 'go_right_week':
                kw = kw + 1
                mode = 'Week'
            elif go == 'go_left_week':
                kw = kw - 1
                mode = 'Week'

            rr_freq(m, y)
            if verbose > 2: logging.info(f" caldit://refresh_site': create_month m {m} y {y}  mode {mode} kw {kw}  END ")
            create_month(m, y, mode, kw)

    else:
        if verbose > 2: logging.info("else : create_month started")
        create_month(1,2024, 'Month')

start()

#BEGIN:VCALENDAR
#VERSION:2.0
#PRODID:-//Deine Organisation//Dein Produkt//DE
#BEGIN:VEVENT
#    UID: Eindeutige Identifikationsnummer für das Ereignis.                                UID:1234567890@example.com
#    DTSTAMP: wird jedes Mal aktualisiert, wenn die iCalendar-Instanz geändert wird         DTSTAMP:20230101T000000Z  2023:01: 06:  T: (Teil des ISO 8601-Standards).090000: Uhrzeit (09:00:00 Uhr)Z:"Zulu" Zeit, die Uhrzeit in UTC (Coordinated Universal Time) angegeben ist.
#    CREATED:20230101T000000Z bleibt konstant , wann das Ereignis erstellt wurde.           CREATED:20230101T000000Z
#LAST-MODIFIED:20230102T000000Z    wann das Ereignis zuletzt geändert wurde.
#    DTSTART und DTEND: Start- und Enddatum des Ereignisses.                                DTSTART:20230106T090000Z  DTSTART;VALUE=DATE:20230106 DTEND;VALUE=DATE:20230106    tzid...  VALUE=DATE:20240101  VALUE=DATE-TIME:20240101T090000
#    SUMMARY: Der Titel oder die Zusammenfassung des Ereignisses.                           SUMMARY:Wöchentliches Meeting
#    DESCRIPTION: Eine ausführlichere Beschreibung des Ereignisses.                         DESCRIPTION:Dies ist ein wöchentliches Planungstreffen. Bitte seien Sie pünkt
#    LOCATION: Der Ort, an dem das Ereignis stattfindet.                                    LOCATION:Konferenzraum 3
#GEO:37.386013;-122.082932
#ORGANIZER;CN=Organisator Name:mailto:organisator@example.com
#    ATTENDEE: Teilnehmer des Ereignisses mit Kontaktdaten.                                 ATTENDEE;CN=Max Mustermann:mailto:max@example.com
#URL:https://example.com/meetings/123
#STATUS:CONFIRMED
#    VALARM: Eine Erinnerung, die 15 Minuten vor dem Ereignis ausgelöst wird.               BEGIN:VALARM TRIGGER:-PT15M ACTION:DISPLAY DESCRIPTION:Erinnerung an das wöchentliche Meeting END:VALARM
#    RRULE: Regel für die Wiederholung des Ereignisses (hier jeden Montag und Freitag).     RRULE:FREQ=WEEKLY;BYDAY=MO,FR
#    CLASS PUBLIC: Das Ereignis ist öffentlich PRIVATE CONFIDENTIAL: Ähnlich wie PRIVATE    CLASS:PRIVATE
#    TRANSP: als beschäftigt (OPAQUE) oder verfügbar (TRANSPARENT)                          TRANSP:OPAQUE
#    PRIORITY: Die Priorität auf einer Skala von 0 (undefiniert) bis 9 (höchste Priorität)  PRIORITY:2
#    CATEGORIES: Kategorien, die dem Ereignis zugeordnet sind.                              CATEGORIES:Besprechung, Wichtig
#    ATTACH: Ein Anhang oder Link zu einer relevanten Datei oder Ressource.                 ATTACH;FMTTYPE=application/pdf:https://example.com/dokument.pdf
#END:VEVENT
#END:VCALENDAR
