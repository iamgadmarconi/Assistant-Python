import os
import dateparser

from typing import Optional
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from O365 import Account, MSGraphProtocol
from O365.utils import Query

from src.utils.files import find
from src.utils.tools import get_context, html_to_text

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
        f"To: {', '.join([recipient for recipient in recipients])}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"Attachments: {', '.join([attachment for attachment in attachments]) if attachments else 'None'}"
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
        
        message_body = html_to_text(message.body)

        email_report = (f"From: {message.sender}\n"
                        f"Subject: {message.subject}\n"
                        f"Received: {message.received}\n"
                        f"Body: {message_body}\n")
        
        email_reports.append(email_report)

    email_reports = "\n".join(email_reports)

    return email_reports
    
def getCalendar(upto: Optional[str] = None):

    account = O365Auth(SCOPES)

    if upto is None:
        upto = datetime.now() + timedelta(days=7)
        
    else:
        time = get_context(upto, ["TIME", "DATE"])
        if time == "":
            time = "7 days"
            
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

def writeCalendarEvent(subject: str, start: str, end: Optional[str], location: Optional[str], body: Optional[str], recurrence: False):
    
    settings = {"PREFER_DATES_FROM": "future"}

    start_time = get_context(start, ["TIME", "DATE"])
    if start_time != "":
        start_time_str = dateparser.parse(start_time, settings=settings).strftime("%d/%m/%Y, %H:%M:%S")
    else:
        start_time_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    if end:
        end_time = get_context(end, ["TIME", "DATE"])
        if end_time != "":
            end_time_str = dateparser.parse(end_time, settings=settings).strftime("%d/%m/%Y, %H:%M:%S")
        else:
            end_time_str = (datetime.now() + timedelta(hours=1)).strftime("%d/%m/%Y, %H:%M:%S")

    start_end_str = f"Start: {start_time_str}, End: {end_time_str}" if end else f"Start: {start_time_str}\n"
    location_str = f"Location: {location}" if location else ""
    recurrence_str = f"Recurrence: {recurrence}" if recurrence else ""

    # Simplified f-string
    calendar_report = (
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"{start_end_str}"
        f"{location_str}"
        f"{recurrence_str}"
    )

    return calendar_report

def createCalendarEvent(subject: str, start: str, end: Optional[str], location: Optional[str], body: Optional[str], recurrence: False):
    account = O365Auth(SCOPES)
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    event = calendar.new_event()

    start = dateparser.parse(start)

    if end:
        end = dateparser.parse(end)
    else:
        end = start + timedelta(hours=1)

    event.start = start
    event.end = end

    event.subject = subject

    if body:
        event.body = body

    if location:
        event.location = location

    # if recurrence:
    #     event.is_all_day = True
    #     event.recurrence = True

    event.save()

    return "Event created successfully"


def query():
    pass

def getContacts(name: Optional[str]):
    threshold = 80
    account = O365Auth(SCOPES)
    contacts = account.address_book().get_contacts()

    if not name:
        contact_reports = []

        for contact in contacts:
            email_addresses = ', '.join([email.address for email in contact.emails])

            home_phones = ', '.join(contact.home_phones) if contact.home_phones else 'None'
            business_phones = ', '.join(contact.business_phones) if contact.business_phones else 'None'
            
            contact_report = (f"Name: {contact.full_name}\n"
                              f"Email: {email_addresses}\n"
                              f"Phone: {home_phones}, {business_phones}")
            
            contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)
    
    else:
        contact_reports = []
        for contact in contacts:
            # Calculate the fuzzy match score
            match_score = fuzz.ratio(contact.full_name.lower(), name.lower())
            
            if match_score >= threshold:
                email_addresses = ', '.join([email.address for email in contact.emails])

                home_phones = ', '.join(contact.home_phones) if contact.home_phones else 'None'
                business_phones = ', '.join(contact.business_phones) if contact.business_phones else 'None'
                
                contact_report = (f"Name: {contact.full_name}\n"
                                f"Email: {email_addresses}\n"
                                f"Phone: {home_phones}, {business_phones}\n"
                                f"__Match_Score: {match_score}")
                
                contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)

    return contact_reports