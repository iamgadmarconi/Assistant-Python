import os
import dateparser

from typing import Optional, Tuple
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from O365 import Account, MSGraphProtocol
from O365.utils import Query

from src.utils.files import find
from src.utils.tools import get_context, html_to_text
from typing import cast

SCOPES = ["basic", "message_all", "calendar_all", "address_book_all", "tasks_all"]


def O365Auth(scopes_helper: list[str] = SCOPES) -> Account:
    """
    The O365Auth function is a helper function that will authenticate with O365 and return an account object.
    
    Parameters
    ----------
        scopes_helper: list[str]
            Pass in the list of scopes that you want to use
    
    Returns
    -------
    
        An account object, which is a subclass of the o365baseclient class
    """
    protocol = MSGraphProtocol()
    credentials: Tuple[str, str] = (
        cast(str, os.environ.get("CLIENT_ID")),
        cast(str, os.environ.get("CLIENT_SECRET"))
    )
    scopes_graph = protocol.get_scopes_for(scopes_helper)

    try:
        account = Account(credentials, protocol=protocol)

        if not account.is_authenticated:
            account.authenticate(scopes=scopes_graph)

        return account

    except:
        raise Exception("Failed to authenticate with O365")


def writeEmail(
    recipients: list, subject: str, body: str, attachments: Optional[list] = None
) -> str:
    """
    The writeEmail function takes in a list of recipients, subject line, body text and an optional list of attachments.
    It then returns a string containing the email report.

    Parameters
    ----------
        recipients: list
            Specify the recipients of the email
        subject: str
            Specify the subject of the email
        body: str
            Pass in the body of the email
        attachments: Optional[list]
            Make the attachments parameter optional

    Returns
    -------

        A string containing the email report
    """
    email_report = (
        f"To: {', '.join([recipient for recipient in recipients])}\n"
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"Attachments: {', '.join([attachment for attachment in attachments]) if attachments else 'None'}"
    )

    return email_report


def sendEmail(
    recipients: list, subject: str, body: str, attachments: Optional[list] = None
) -> str:
    """
    The sendEmail function is used to send an email using the O365 library.
        It takes in a list of recipients, subject, body and attachments as parameters.
        The function returns a string indicating whether or not the email was sent successfully.

    Parameters
    ----------
        recipients: list
            Specify the email addresses of the recipients
        subject: str
            Set the subject of the email
        body: str
            Pass the body of the email to be sent
        attachments: Optional[list]
            Specify that the attachments parameter is optional

    Returns
    -------

        A string indicating whether the email was sent successfully or not
    """
    try:
        account = O365Auth(SCOPES)
        m = account.new_message()
        m.to.add(recipients)
        m.subject = subject
        m.body = body
        m.body_type = "HTML"

        if attachments:

            for attachment_path in attachments:
                path = find(attachment_path, r"files/mail")
                m.attachments.add(path)

        m.send()

        return "Email sent successfully"

    except:
        return "Failed to send email"


def readEmail() -> str:
    """
    The readEmail function is used to read the last 5 emails in a user's inbox.
    It returns a string containing the sender, subject, received date and body of each email.

    Parameters
    ----------

    Returns
    -------

        A string of emails
    """
    account = O365Auth(SCOPES)

    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()

    messages = inbox.get_messages(limit=5)

    email_reports = []

    for message in messages:

        message_body = html_to_text(message.body)

        email_report = (
            f"From: {message.sender}\n"
            f"Subject: {message.subject}\n"
            f"Received: {message.received}\n"
            f"Body: {message_body}\n"
        )

        email_reports.append(email_report)

    email_reports = "\n".join(email_reports)

    return email_reports


def getCalendar(upto: Optional[str] = None) -> str:
    """
    The getCalendar function is used to retrieve the user's calendar events.
    It takes an optional parameter, upto, which specifies how far into the future
    the function should look for events. If no value is provided for this parameter,
    it defaults to 7 days from now.

    Parameters
    ----------
        upto: Optional[str]
            Specify the end date of the calendar events to be returned

    Returns
    -------

        A string of all the events in your calendar
    """
    # print(f"Debug--- Called getCalendar with parameters: {upto}")
    account = O365Auth(SCOPES)

    if upto is None:
        upto = datetime.now() + timedelta(days=7)  # type: ignore

    else:
        time = get_context(upto, ["TIME", "DATE"])
        if time == "":
            time = "7 days"

        diff = dateparser.parse(time, settings={"PREFER_DATES_FROM": "future"})

        if diff is not None:
            upto = diff  # type: ignore

        else:
            upto = datetime.now() + timedelta(
                days=7
            )  # Default to 7 days from now if parsing fails # type: ignore

    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    q = calendar.new_query("start").greater_equal(datetime.now())  # type: ignore
    q.chain("and").on_attribute("end").less_equal(upto)  # type: ignore

    try:
        events = calendar.get_events(query=q, include_recurring=True)  # type: ignore

    except:
        events = calendar.get_events(query=q, include_recurring=False)  # type: ignore

    cal_reports = []

    for event in events:

        cal_report = (
            f"Event: {event.subject}\n"
            f"Start: {event.start}\n"
            f"End: {event.end}\n"
            f"Location: {event.location}\n"
            f"Description: {event.body}"
        )

        cal_reports.append(cal_report)

    cal_reports = "\n".join(cal_reports)

    return cal_reports


def createCalendarEvent(
    subject: str,
    start: str,
    end: Optional[str] = None,
    location: Optional[str] = None,
    body: Optional[str] = None,
    recurrence: bool = False,
) -> str:
    # print(f"Debug--- Called writeCalendarEvent with parameters: {subject}, {start}, {end}, {location}, {body}, {recurrence}")
    """
    The createCalendarEvent function is used to create a new calendar event.

    Parameters
    ----------
        subject: str
            Pass in the subject of the calendar event
        start: str
            Define the start time of the event
        end: Optional[str]
            The end time of the event
        location: Optional[str]
            Define the location of the event
        body: Optional[str]
            A description of the event
        recurrence: bool
            Indicate whether the event is a recurring one or not

    Returns
    -------

        The calendar_report variable
    """

    start = get_context(start, ["TIME", "DATE"])
    if start:
        start_time = dateparser.parse(start, settings={"PREFER_DATES_FROM": "future"})
        if start_time:
            start_time_str = start_time.strftime("%d/%m/%Y, %H:%M:%S")
        else:
            return "Failed to parse start time. Please try again."
    else:
        start_time_str = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

    if end:
        end_time = get_context(end, ["TIME", "DATE"])
        if end_time:
            end_time = dateparser.parse(
                end_time, settings={"PREFER_DATES_FROM": "future"}
            )
            if end_time:
                end_time_str = end_time.strftime("%d/%m/%Y, %H:%M:%S")
            else:
                return "Failed to parse end time. Please try again."
        else:
            end_time_str = (datetime.now() + timedelta(hours=1)).strftime(
                "%d/%m/%Y, %H:%M:%S"
            )
    else:
        end_time_str = ""

    start_end_str = (
        f"Start: {start_time_str}, End: {end_time_str}"
        if end
        else f"Start: {start_time_str}\n"
    )
    location_str = f"Location: {location}" if location else ""
    recurrence_str = f"Recurrence: {recurrence}" if recurrence else ""

    calendar_report = (
        f"Subject: {subject}\n"
        f"Body: {body}\n"
        f"{start_end_str}"
        f"{location_str}"
        f"{recurrence_str}"
    )

    return calendar_report


def saveCalendarEvent(
    subject: str,
    start: str,
    end: Optional[str] = None,
    location: Optional[str] = None,
    body: Optional[str] = None,
    recurrence: bool = False,
) -> str:
    # print(f"Debug--- Called saveCalendarEvent with parameters: {subject}, {start}, {end}, {location}, {body}, {recurrence}")
    """
    The saveCalendarEvent function is used to save a new event in the user's Outlook calendar.

    Parameters
    ----------
        subject: str
            Pass in the subject of the event
        start: str
            Specify the start time of the event
        end: Optional[str]
            Specify the end date of the event
        location: Optional[str]
            Specify the location of the event
        body: Optional[str]
            Pass in the body of the event
        recurrence: bool
            Determine if the event is a recurring event

    Returns
    -------

        A string indicating the event was created successfully
    """
    account = O365Auth(SCOPES)
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()

    if calendar is not None:
        event = calendar.new_event()
    else:
        raise ValueError("Calendar is not available.")

    start = dateparser.parse(start)  # type: ignore [attr-defined]

    if end:
        end = dateparser.parse(end)  # type: ignore [attr-defined]
    else:
        end = start + timedelta(hours=1)  # type: ignore

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


def getContacts(name: Optional[str] = None) -> str:
    """
    The getContacts function returns a list of contacts from the user's Outlook account.
    If no name is provided, all contacts are returned. If a name is provided, only those
    contacts with names that match the given name will be returned.

    Parameters
    ----------
        name: Optional[str]
            The name of the contact to search for

    Returns
    -------

        A string containing the contact information
    """
    threshold = 80
    account = O365Auth(SCOPES)
    contacts = account.address_book().get_contacts()  # type: ignore [attr-defined]

    if not name:
        contact_reports = []

        for contact in contacts:
            email_addresses = ", ".join([email.address for email in contact.emails])

            home_phones = (
                ", ".join(contact.home_phones) if contact.home_phones else "None"
            )
            business_phones = (
                ", ".join(contact.business_phones)
                if contact.business_phones
                else "None"
            )

            contact_report = (
                f"Name: {contact.full_name}\n"
                f"Email: {email_addresses}\n"
                f"Phone: {home_phones}, {business_phones}"
            )

            contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)

    else:
        contact_reports = []
        for contact in contacts:
            # Calculate the fuzzy match score
            match_score = fuzz.ratio(contact.full_name.lower(), name.lower())

            if match_score >= threshold:
                email_addresses = ", ".join([email.address for email in contact.emails])

                home_phones = (
                    ", ".join(contact.home_phones) if contact.home_phones else "None"
                )
                business_phones = (
                    ", ".join(contact.business_phones)
                    if contact.business_phones
                    else "None"
                )

                contact_report = (
                    f"Name: {contact.full_name}\n"
                    f"Email: {email_addresses}\n"
                    f"Phone: {home_phones}, {business_phones}\n"
                    f"__Match_Score: {match_score}"
                )

                contact_reports.append(contact_report)

        contact_reports = "\n".join(contact_reports)

    return contact_reports
