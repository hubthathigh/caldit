# caldit
calendar and editor designed for managing ICS


Caldit is a simple calendar and editor designed for managing ICS (iCalendar) files. It operates locally as an HTML page through a web browser. 
The entire functionality relies on the MIME type, which must be set up in the operating system beforehand, as indicated in a comment within the code. 
This program employs a method that uses Python as the backend and HTML as the frontend. 
Importing ICS files requires specifying the full path, and exporting is facilitated to the designated filepath, as indicated in line 5 of the code.

![Caldit_month](https://github.com/hubthathigh/caldit/assets/96214532/d9884933-1914-4086-b097-05b6055abefb)


![Caldit_single](https://github.com/hubthathigh/caldit/assets/96214532/6b8a3189-f119-451c-affb-d24e9e01f4f3)


Since it utilizes SQLite for storing appointments, it can be employed to insert events from various sources.
I primarily use it for my Raspberry Pi, which records actions for me. With a bookmark on 'months.html' in Firefox , it provides a rapid visual overview.
