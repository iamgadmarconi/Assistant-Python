import os
import dateparser

from typing import Optional
from datetime import datetime, timedelta
from O365 import Account, MSGraphProtocol, Message

from src.utils.files import find
from src.utils.tools import get_context


def O365Auth(scopes_helper: list[str] = ['basic']):
    protocol = MSGraphProtocol()
    credentials = (os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"))
    scopes_graph = protocol.get_scopes_for(scopes_helper)

    try:
        account = Account(credentials, protocol=protocol)

        if not account.is_authenticated:
            account.authenticate(scopes=scopes_graph)

        return account
    
    except:
        raise Exception("Failed to authenticate with O365")

def writeEmail(recipients: list[str], subject: str, body: str, attachments: Optional[list[str]] = None):
    account = O365Auth(["message_all", "basic"])
    m = Message(account=account)
    m.to.add(recipients)
    m.subject = subject
    m.body = body
    m.body_type = "HTML"

    if attachments:

        for attachment_path in attachments:
            path = find(attachment_path, r'files/mail')
            m.attachments.add(path)
    
    email_report = (
        f"From: {m.sender}\n"
        f"To: {m.to}\n"
        f"Subject: {m.subject}\n"
        f"Body: {m.body}"
        f"Attachments: {m.attachments}"
    )

    return m, email_report


def sendEmail(message):
    try:
        message.send()
        return "Email sent successfully"
    except:
        return "Failed to send email"

def readEmail():
    
    account = O365Auth(["message_all", "basic"])

    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    messages = inbox.get_messages(limit=5)

    email_reports = []

    for message in messages:
        email_report = (f"From: {message.sender}\n"
                        f"Subject: {message.subject}\n"
                        f"Received: {message.received}\n"
                        f"Body: {message.body}")
        
        email_reports.append(email_report)
        
    return email_reports
    
def getCalendar(upto: Optional[str] = None):

    account = O365Auth(["calendar_all", "basic"])

    if upto is None:
        upto = datetime.now() + timedelta(days=7)
        
    else:
        time = get_context(upto, ["TIME", "DATE"])
        settings = {"PREFER_DATES_FROM": "future"}
        diff = dateparser.parse(time, settings=settings)

        if diff is not None:
            upto = diff

        else:
            upto = datetime.now() + timedelta(days=7)  # Default to 7 days from now if parsing fails

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    q = calendar.new_query('start').greater_equal(datetime.now())
    q.chain('and').on_attribute('end').less_equal(upto)

    try:
        events = calendar.get_events(query=q, include_recurring=True)

    except:
        events = calendar.get_events(query=q, include_recurring=False)

    cal_reports = []

    for event in events:

        cal_report = (f"Event: {event.subject}\n"
                      f"Start: {event.start}\n"
                      f"End: {event.end}\n"
                      f"Location: {event.location}\n"
                      f"Description: {event.body}")
        
        cal_reports.append(cal_report)

    return cal_reports

def addCalendarEvent():
    pass

def query():
    pass