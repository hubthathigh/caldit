# caldit
calendar and editor designed for managing ICS standalone script does not run in background, no server


Caldit is a simple calendar and editor designed for managing ICS (iCalendar) files. It operates locally as an HTML page through a web browser. 
The entire functionality relies on the MIME type, which must be set up in the operating system beforehand, as indicated in a comment within the code. 
This program employs a method that uses Python as the backend and HTML as the frontend. 
Importing ICS files requires specifying the full path, and exporting is facilitated to the designated filepath, as indicated in line 5 of the code.

![Caldit_month](https://github.com/hubthathigh/caldit/assets/96214532/d198d810-269d-4a20-88af-74830abd2617)

![Caldit_single](https://github.com/hubthathigh/caldit/assets/96214532/98c4fabb-d9d5-406c-a32c-28191c8e1553)


Since it utilizes SQLite for storing appointments, it can be employed to insert events from various sources.
I primarily use it for my Raspberry Pi, which records actions for me. With a bookmark on 'months.html' in Firefox , it provides a rapid visual overview.

Install on Debian 12 :

```
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
open 'months.html' in browser, push export button(longest wait), accept popup. same page2.html
```

            




