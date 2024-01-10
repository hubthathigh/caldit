#!/usr/bin/python3
# -*- coding: utf-8 -*-

dbasepath = '/home/tab/tsync/cnet/py/cal/'
verbose = 0 #3 all

"""
to connect html with python script, over mime support
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
Exec=/usr/bin/python3 /home/tab/tsync/cnet/py/cal/caldit.py %U
Icon=weather-clear
Categories=WebBrowser;
MimeType=x-scheme-handler/caldit;
sudo update-desktop-database
sudo update-mime-database /usr/share/mime
xdg-mime default caldit.desktop application/x-caldit
xdg-mime query default application/x-caldit
xdg-open "caldit://create?single=yes"
open 'months.html', push export button(longest wait), accept. same page2.html
"""

import sys
import time
import sqlite3
from datetime import datetime, timedelta
import calendar
import ast
from urllib.parse import unquote
import logging

scan_time = time.strftime("%d.%m.%Y_%H:%M")

con = sqlite3.connect('{}ical.db'.format(dbasepath))

logging.basicConfig(level=logging.INFO, filename=f"{dbasepath}cal.log", filemode='a')
if verbose > 1: logging.info(f"{dbasepath}cal.log started {scan_time}")

def erstelle_table_termine():
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS termine (" 
                    "UID TEXT, DTSTAMP TEXT, CREATED TEXT, LASTMODIFIED TEXT, "
                    "DTSTART TEXT, DTEND TEXT, SUMMARY TEXT, DESCRIPTION TEXT, "
                    "LOCATION TEXT, GEO TEXT, ORGANIZER TEXT, ATTENDEE TEXT, "
                    "URL TEXT, STATUS TEXT, VALARM TEXT, RRULE TEXT, CLASS TEXT, "
                    "TRANSP TEXT, PRIORITY INTEGER, CATEGORIES TEXT, ATTACH BLOB, "
                    "ATTACH2 BLOB, TMP TEXT, UNIQUE (UID));")
erstelle_table_termine()

def check_termin_at_date(date):
    string_to_insert = ''
    with con:
        DTSTART = ''
        DTEND = ''
        SUMMARY = ''
        DESCRIPTION = ''
        UID = ''
        cur = con.cursor()
        cur.execute(f'SELECT DTSTART, DTEND, SUMMARY, DESCRIPTION, UID FROM termine WHERE DTSTART LIKE "%{date}%" OR DTEND LIKE "%{date}%"')

        result=cur.fetchall()
        if result:

            for termin in result:
                DTSTART = termin[0][-4:]
                DTEND = termin[1][-4:]
                DTSTARTs = termin[0][4:]
                if DTSTARTs.endswith('Z'):
                    DTSTARTs = DTSTARTs[:-3]
                DTENDs = termin[1][4:]
                if DTENDs.endswith('Z'):
                    DTENDs = DTENDs[:-3]
                SUMMARY = termin[2][:15]
                DESCRIPTION = termin[3][:30]
                UID = termin[4]

                string_to_insert += f"""<div class="night">  <a href="caldit://goto_termin?UID={UID}&DTSTART={DTSTART}&DTEND={DTEND}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color:#41A338;">{DTSTARTs}</span> <span style="color:#F67C30;">{DTENDs}</span> {SUMMARY} {DESCRIPTION}</a> </div>"""

            return(string_to_insert)

def insert_termin(UID, DTSTART, DTSTAMP=None, CREATED=None, LASTMODIFIED=None,
         DTEND=None, SUMMARY=None, DESCRIPTION=None, LOCATION=None, GEO=None,
         ORGANIZER=None, ATTENDEE=None, URL=None, STATUS=None, VALARM=None,
         RRULE=None, CLASS=None, TRANSP=None, PRIORITY=None, CATEGORIES=None,
         ATTACH=None, ATTACH2=None, TMP=None):
    with con:
        cur = con.cursor()
        insert_into_table = (
            '"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", '
            '"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", '
            '"{}", "{}", "{}"'.format(
                UID, DTSTAMP, CREATED, LASTMODIFIED, DTSTART, DTEND, SUMMARY,
                DESCRIPTION, LOCATION, GEO, ORGANIZER, ATTENDEE, URL, STATUS,
                VALARM, RRULE, CLASS, TRANSP, PRIORITY, CATEGORIES, ATTACH,
                ATTACH2, TMP
            )
        )

        sql_prompt = (
            "INSERT OR REPLACE INTO termine ("
            "UID, DTSTAMP, CREATED, LASTMODIFIED, DTSTART, DTEND, SUMMARY, DESCRIPTION, "
            "LOCATION, GEO, ORGANIZER, ATTENDEE, URL, STATUS, VALARM, RRULE, CLASS, "
            "TRANSP, PRIORITY, CATEGORIES, ATTACH, ATTACH2, TMP"
            ") VALUES ({});".format(insert_into_table)
        )

        cur.execute(sql_prompt)

def create_single_site(UID, DTSTART, DTSTAMP=None, CREATED=None, LASTMODIFIED=None,
         DTEND=None, SUMMARY=None, DESCRIPTION=None, LOCATION=None, GEO=None,
         ORGANIZER=None, ATTENDEE=None, URL=None, STATUS=None, VALARM=None,
         RRULE=None, CLASS=None, TRANSP=None, PRIORITY=None, CATEGORIES=None,
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
</style>
</head>
<body>
"""
    body = f"""
<form id="meinFormular">

  <div class="grid-container first-two-rows">
    <div class="description">LASTMODIFIED</div>
    <div class="description">CATEGORIES</div>
    <div class="description">ORGANIZER</div>
    <input type="text" id="LASTMODIFIED" name="LASTMODIFIED" placeholder="LASTMODIFIED" value="{ LASTMODIFIED if LASTMODIFIED else '' }">
    <input type="text" id="CATEGORIES" name="CATEGORIES" placeholder="CATEGORIES" value="{ CATEGORIES if CATEGORIES else '' }">
    <input type="text" id="ORGANIZER" name="ORGANIZER" placeholder="ORGANIZER" value="{ ORGANIZER if ORGANIZER else '' }">
    <div class="description">DTSTART</div>
    <div class="description">DTEND</div>
    <div class="description">ATTENDEE</div>
    <input type="text" id="DTSTART" name="DTSTART" placeholder="DTSTART" value="{ DTSTART if DTSTART else '' }">
    <input type="text" id="DTEND" name="DTEND" placeholder="DTEND" value="{ DTEND if DTEND else '' }">
    <input type="text" id="ATTENDEE" name="ATTENDEE" placeholder="ATTENDEE" value="{ ATTENDEE if ATTENDEE else '' }">
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
    <div class="description">ATTACH</div>
    <div class="description">UID</div>
    <div class="description">DTSTAMP</div>
    <input type="text" id="ATTACH" name="ATTACH" placeholder="https://example.com/dokument.pdf" value="{ ATTACH if ATTACH else '' }">
    <input type="text" id="UID" name="UID" placeholder="UID" value="{ UID if UID else '' }">
    <input type="text" id="DTSTAMP" name="DTSTAMP" placeholder="DTSTAMP" value="{ DTSTAMP if DTSTAMP else '' }">
    <div class="description">CREATED</div>
    <div class="description">STATUS</div>
    <div class="description">VALARM</div>
    <input type="text" id="CREATED" name="CREATED" placeholder="CREATED" value="{ CREATED if CREATED else '' }">
    <input type="text" id="STATUS" name="STATUS" placeholder="STATUS" value="{ STATUS if STATUS else '' }">
    <input type="text" id="VALARM" name="VALARM" placeholder="&#123;&#39;TRIGGER&#39;: &#39;-PT15M&#39;, &#39;ACTION&#39;: &#39;DISPLAY&#39;, &#39;DESCRIPTION&#39;: &#39;Ring&#39;&#125;" value="{ VALARM if VALARM else '' }">
    <div class="description">RRULE</div>
    <div class="description">CLASS</div>
    <div class="description">TRANSP</div>
    <input type="text" id="RRULE" name="RRULE" placeholder="FREQ=WEEKLY;BYDAY=MO,FR" value="{ RRULE if RRULE else '' }">
    <input type="text" id="CLASS" name="CLASS" placeholder="CLASS" value="{ CLASS if CLASS else '' }">
    <input type="text" id="TRANSP" name="TRANSP" placeholder="OPAQUE" value="{ TRANSP if TRANSP else '' }">
    <div class="description">PRIORITY</div>
    <div class="description">ATTACH2</div>
    <div class="description">TMP</div>
    <input type="text" id="PRIORITY" name="PRIORITY" placeholder="PRIORITY" value="{ PRIORITY if PRIORITY else '' }">
    <input type="text" id="ATTACH2" name="ATTACH2" placeholder="ATTACH2" value="{ ATTACH2 if ATTACH2 else '' }">
    <input type="text" id="TMP" name="TMP" placeholder="TMP" value="{ TMP if TMP else '' }">
  </div>
  <div class="grid-container buttons">
    <input type="button" value="Update" onclick="senden(); setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
    <input type="button" value="DELETE" onclick="if(confirm('Möchtest du fortfahren?')) senden_del_uid() ; setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
    <input type="button" value="Export" onclick="senden_ex(); setTimeout(function() {{ window.location.href='month.html'; }}, 4000); return true;">
    <input type="button" value="Back" onclick="senden_back(); setTimeout(function() {{ window.location.href='month.html'; }}, 1000); return true;">
  </div>
</form>

"""
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
        page2 = head + body + script
        file.write(page2)

# creates months.html codebody
def eee1(m, y):

    scan_time_d = time.strftime("%d")
    month = m
    year = y

    current_utc_time = datetime.utcnow()
    formatted_utc_time = current_utc_time.strftime("%Y%m%dT%H%M%SZ")
    string_formatted_utc_time = str(formatted_utc_time)

    cal = calendar.Calendar(firstweekday=0)  # Starte die Woche mit Montag
    first_day_weekday, days_in_month = calendar.monthrange(year, month)
    month_weeks = list(cal.monthdays2calendar(year, month))

    html_days = []
    day_of_next_month = 1
    termin = ''
    for week_num, week in enumerate(month_weeks):
        for day, weekday in week:
            day_class = "day"
            UID = 'UID' + string_formatted_utc_time

            if day == 0:
                if week_num == 0:  # Die erste Woche des Monats -> Tage gehören zum Vormonat
                    prev_month = month - 1 if month > 1 else 12
                    prev_month_2char = "{:02.0f}".format(prev_month)
                    prev_year = year if month > 1 else year - 1
                    days_in_prev_month = calendar.monthrange(prev_year, prev_month)[1]
                    day = days_in_prev_month - (first_day_weekday - weekday - 1)
                    prev_day_2char = "{:02.0f}".format(day)
                    day_to_seach_termin = str(prev_year) + str(prev_month_2char) + str(prev_day_2char)
                    termin = check_termin_at_date(day_to_seach_termin) if check_termin_at_date(day_to_seach_termin) is not None else ''
                elif week_num == len(month_weeks) - 1:  # Die letzte Woche des Monats -> Tage gehören zum nächsten Monat
                    day = day_of_next_month
                    next_day_2char = "{:02.0f}".format(day)
                    day_of_next_month += 1
                    next_month = month + 1
                    next_month_2char = "{:02.0f}".format(next_month)
                    next_year = year if month < 11 else year + 1
                    day_to_seach_termin = str(next_year) + str(next_month_2char) + str(next_day_2char)
                    termin = check_termin_at_date(day_to_seach_termin) if check_termin_at_date(day_to_seach_termin) is not None else ''

                day_html =  f""" <div class={day_class}> <a href="caldit://entry_termin?UID={UID}&DTSTART={day_to_seach_termin + "T001122Z"}&CREATED={day_to_seach_termin}&DTEND={day_to_seach_termin + "T223344Z"}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"><span style="color: #C45137;">{day} </span></a> {termin} </div>"""

            else:
                day_2char = "{:02.0f}".format(day)
                month_2char = "{:02.0f}".format(month)
                day_to_seach_termin = str(year) + str(month_2char) + str(day_2char)
                termin = check_termin_at_date(day_to_seach_termin) if check_termin_at_date(day_to_seach_termin) is not None else ''
                if day_2char == scan_time_d:
                    day_class = '"day" style="background: #696969;"'
                    day_html = f""" <div class={day_class}> <a href="caldit://entry_termin?UID={UID}&DTSTART={day_to_seach_termin + "T001122Z"}&CREATED={string_formatted_utc_time}&DTEND={day_to_seach_termin + "T223344Z"}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"> {day} </a>{termin} </div>"""
                else:
                    day_html = f""" <div class={day_class}> <a href="caldit://entry_termin?UID={UID}&DTSTART={day_to_seach_termin + "T001122Z"}&CREATED={string_formatted_utc_time}&DTEND={day_to_seach_termin + "T223344Z"}" onclick="setTimeout(function(){{ window.location.href='page2.html'; }}, 1000); return true;"> {day} </a>{termin} </div>"""
            html_days.append(day_html)

    # Alle Tage als String zusammen
    html_days_str = "\n".join(html_days)
    return html_days_str

def create_month(m, y):
    monat = m
    year = y
    if verbose > 2: logging.info("started : create_month ")
    head = """
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
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
}
input[type="button"] {
    background-color: #3D3D3D;
    cursor: pointer;
    font-size: 16px;
}
.lineone {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    margin: 1px;
</style>
</head>
<body>

<form id="meinFormular2" class="lineone">
<input type="button" value="&larr;" onclick="senden_ref('go_left'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
<input type="text" id="datum" name="datum" value="%s" style="text-align: center; font-size: 18px;">
<input type="button" value="Refresh" onclick="senden_ref('no'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
<input type="text" id="meineDatei" name="meineDatei" value="/home/debian/fullp.ics"> 
<input type="button" value="Import" onclick="import_ics(); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;"> 
<input type="text" id="optins_ex_cat" name="optins_ex_cat" value="CATEGORIES:birthday"> 
<input type="button" value="Export filter" onclick="export_ics('cat'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
<input type="button" value="Export All" onclick="export_ics('all'); setTimeout(function() { window.location.href='month.html'; }, 4000); return true;"> 
<input type="button" value="&rarr;" onclick="senden_ref('go_right'); setTimeout(function() { window.location.href='month.html'; }, 1000); return true;">
</form>

<script>
function senden_ref(input) {
    var datum = document.getElementById('datum').value;
    var url = "caldit://refresh_site?" +
              "datum=" + encodeURIComponent(datum) +
              "&go=" + encodeURIComponent(input);
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
    var meineDatei = document.getElementById('meineDatei').value;
    var url = "caldit://import_ics?" +
              "meineDatei=" + encodeURIComponent(meineDatei);
    window.open(url, '_self');
}
</script>

<div class="calendar">
    <!-- Wochentagsköpfe -->
    <div class="header">Mo</div>
    <div class="header">Di</div>
    <div class="header">Mi</div>
    <div class="header">Do</div>
    <div class="header">Fr</div>
    <div class="header">Sa</div>
    <div class="header">So</div>
""" % (str(monat) + '.' + str(year))
    body_insert = eee1(monat, year)
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
                if len(key_val) == 2:
                    if inside_valarm:
                        valarm_info[key_val[0]] = key_val[1]
                    else:
                        current_event[key_val[0]] = key_val[1]
    return termine

def read_and_insert_ics_file(ics_file_path):
    valid_entries = ["UID", "DTSTART", "DTSTAMP", "CREATED", "LASTMODIFIED", "DTEND", "SUMMARY", "DESCRIPTION", "LOCATION", "GEO", "ORGANIZER", "ATTENDEE", "URL", "STATUS", "VALARM", "RRULE", "CLASS", "TRANSP", "PRIORITY", "CATEGORIES", "ATTACH", "ATTACH2"]

    termine = read_cal_file(ics_file_path)

    for termin in termine:
        current_termin = {}
        TMP = []
        inside_valarm = False
        valarm_info = []

        for key, value in termin.items():
            if key == 'LAST-MODIFIED':
                current_termin['LASTMODIFIED'] = value
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
        head = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//This is Sparta//Caldit//DE

CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Caldat
BEGIN:VTIMEZONE
TZID:Europe/Berlin
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

        return result_dict

def delete_termin(termin_uid):
    with con:
        cur = con.cursor()
        sql = f'DELETE FROM termine WHERE UID ="{termin_uid}"'
        cur.execute(sql)
        con.commit()
        if verbose > 2: logging.info("delete_termin erfolgreich ..")

def parse_custom_url(url):
    parts = url.split('?')
    base = parts[0]
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
            param_dict[key] = value

        for key in param_dict:
            param_dict[key] = unquote(param_dict[key])

        UID = param_dict.get('UID', '19841201')

        m = int(time.strftime("%m"))
        y = int(time.strftime("%Y"))

        if verbose > 1: logging.info(f"started params dic = {param_dict}")

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
            create_month(m, y)

        elif base == 'caldit://delete_termin':
            delete_termin(UID)
            create_month(m, y)

        elif base == 'caldit://import_ics':
            day_to_enter_uid = param_dict['meineDatei']
            read_and_insert_ics_file(day_to_enter_uid)
            if verbose > 2: logging.info(day_to_enter_uid)

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
            m = int(month_too_refresh.split('.')[0])
            y = int(month_too_refresh.split('.')[1])

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

            create_month(m, y)
    else:
        if verbose > 2: logging.info("else : create_month started")
        create_month(1,2024)

start()

#BEGIN:VCALENDAR
#VERSION:2.0
#PRODID:-//Deine Organisation//Dein Produkt//DE
#BEGIN:VEVENT
#    UID: Eindeutige Identifikationsnummer für das Ereignis.                                UID:1234567890@example.com
#    DTSTAMP: wird jedes Mal aktualisiert, wenn die iCalendar-Instanz geändert wird         DTSTAMP:20230101T000000Z  2023:01: 06:  T: (Teil des ISO 8601-Standards).090000: Uhrzeit (09:00:00 Uhr)Z:"Zulu" Zeit, die Uhrzeit in UTC (Coordinated Universal Time) angegeben ist.
#    CREATED:20230101T000000Z bleibt konstant , wann das Ereignis erstellt wurde.           CREATED:20230101T000000Z
#LAST-MODIFIED:20230102T000000Z    wann das Ereignis zuletzt geändert wurde.
#    DTSTART und DTEND: Start- und Enddatum des Ereignisses.                                DTSTART:20230106T090000Z  DTSTART;VALUE=DATE:20230106 DTEND;VALUE=DATE:20230106
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
