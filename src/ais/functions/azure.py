import os
import dateparser

from typing import Optional
from datetime import datetime, timedelta
from O365 import Account, MSGraphProtocol, Message

from src.utils.files import find
from src.utils.tools import get_context

SCOPES = ["basic", "message_all", "calendar_all", "address_book_all", "tasks_all"]


def O365Auth(scopes_helper: list[str] = SCOPES):
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

def writeEmail(recipients: list, subject: str, body: str, attachments: Optional[list] = None):
    
    email_report = (
        f"To: {", ".join([recipient for recipient in recipients])}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"Attachments: {', '.join([attachment for attachment in attachments]) if attachments else "None"}"
    )

    return email_report


def sendEmail(recipients: list, subject: str, body: str, attachments: Optional[list] = None):
    try:
        account = O365Auth(SCOPES)
        m = account.new_message()
        m.to.add(recipients)
        m.subject = subject
        m.body = body
        m.body_type = "HTML"

        if attachments:

            for attachment_path in attachments:
                path = find(attachment_path, r'files/mail')
                m.attachments.add(path)
        
        m.send()
        
        return "Email sent successfully"
    
    except:
        return "Failed to send email"

def readEmail():
    
    account = O365Auth(SCOPES)

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
        
    email_reports = "\n".join(email_reports)

    return email_reports
    
def getCalendar(upto: Optional[str] = None):

    account = O365Auth(SCOPES)

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

    cal_reports = "\n".join(cal_reports)

    return cal_reports

def addCalendarEvent():
    pass

def query():
    pass