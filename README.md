# caldit
calendar and editor running in Python as standalone script, operating offline in the browser, serverless.

Caldit is a simple calendar and editor designed for managing ICS (iCalendar) files. It operates locally as an HTML page through a web browser. 
The entire functionality relies on the MIME type, which must be set up in the operating system beforehand, as indicated in a comment within the code. 
This program employs a method that uses Python as the backend and HTML as the frontend. 
Importing ICS files requires specifying the full path, and exporting is facilitated to the designated filepath, as indicated in line 5 of the code.

![month](https://github.com/hubthathigh/caldit/assets/96214532/6650bc03-c9b2-41c7-9794-e91cf0c846c9)

![year](https://github.com/hubthathigh/caldit/assets/96214532/63360fe1-c35f-45d3-8d87-4d87f194dc3b)

![single](https://github.com/hubthathigh/caldit/assets/96214532/61d93827-3d7d-437e-9cdb-f8009fd5b322)

Since it utilizes SQLite for storing appointments, it can be employed to insert events from various sources.
I primarily use it for my Raspberry Pi, which records actions for me. With a bookmark on 'months.html' in Firefox , it provides a rapid visual overview.


req : pip install python-dateutil  for RRULE.
to connect html with python script, over mime support
Install on Debian 12 :

```
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
Exec=/usr/bin/python3 /home/tab/tsync/cnet/py/cal/caldit.py %U
Icon=weather-clear
Categories=WebBrowser;
MimeType=x-scheme-handler/caldit;
sudo update-desktop-database
sudo update-mime-database /usr/share/mime
xdg-mime default caldit.desktop application/x-caldit
xdg-mime query default application/x-caldit
xdg-open "caldit://create?single=yes"
open 'months.html' in browser, push export button(longest wait), accept popup. same page2.html
```
Install on Windows :
```
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
```

            




