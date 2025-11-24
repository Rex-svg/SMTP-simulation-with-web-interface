# Project Name
SMTP Email System

## Table of Contents
[Installation](#installation)
[Usage](#usage)
[Features](#features)
[Contributing](#contributing)
[License](#license)
## Installation
1. Clone the repo:
```bash
git clone (https://github.com/Rex-svg/SMTP-simulation-with-web-interface)

2. Install dependencies:

npm install
pip install flask

project structure:
smtp-email-system/
│
├── server/
│   └── smtp_server.py
│
├── client/
│   └── smtp_client.py
│
├── web/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── styles.css
│       └── script.js
│
└── data/
    └── mailboxes/




Usage

1. Start the SMTP Server
python server/smtp_server.py

2. Start the Web Interface
python web/app.py


Opens at:

http://127.0.0.1:5000/

4. Send Email From Terminal (Optional)
python client/smtp_client.py

Run the project with:

python server.py

Features

Features
✔ Custom SMTP server

Handles:

HELO

MAIL FROM

RCPT TO

DATA

QUIT

✔ Web-based mailbox

Read inbox messages

Messages loaded from user's mailbox file

✔ Fixed left-side compose window

Clean, organized UI for composing messages.

✔ Real SMTP-like workflow

Simulates real email transfer for learning purposes.

✔ Simple file-based storage

Each user gets a mailbox file containing their received emails.


Contributing

contributions are welcomed

License

This project is licensed under the Shahriar.inc
Contact

Your Name
