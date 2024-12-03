# Import necessary libraries for date/time handling, Streamlit, and Google Calendar API
import datetime
import os.path
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the required scopes for the Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def check_event_exists(service, target_date):
    """
    Check if there's an event on the given date (target_date).
    It converts the target date to a datetime object and checks for events between midnight and midnight of the next day.
    """
    target_datetime = datetime.datetime.combine(target_date, datetime.time.min)  # Convert to start of the day
    end_datetime = target_datetime + datetime.timedelta(days=1)  # Add one day for the end time

    # Convert the times to ISO format (required by Google API)
    timeMin = target_datetime.isoformat() + "Z"
    timeMax = end_datetime.isoformat() + "Z"

    # Query the Google Calendar API for events between the specified time window
    events_result = (
        service.events()
        .list(
            calendarId="primary",  # Use the primary calendar
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,  # Only return individual events (not recurring series)
            orderBy="startTime",  # Order events by start time
        )
        .execute()
    )
    events = events_result.get("items", [])  # Get the events from the API response

    # Return True if events are found, otherwise False
    return len(events) > 0

def check_credentials():
    """
    Check if the credentials are valid and refresh them if necessary.
    If no valid credentials are found, it prompts the user to authenticate.
    """
    creds = None
    # Check if a 'token.json' file exists, indicating that the user has authenticated before
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)  # Load credentials from the file

    # If credentials are not available or expired, refresh them or start the authentication flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Refresh expired credentials
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES  # Start OAuth flow to get new credentials
            )
            creds = flow.run_local_server(port=0)  # Local server for user to authenticate

        # Save the refreshed or new credentials to 'token.json' for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds  # Return the valid credentials

def suggest_alternate_date(service, event_date):
    """
    Suggest an alternate date within the same week if the event already exists on the given date.
    It checks for available dates by iterating through the week and checking for free days.
    """
    start_of_week = event_date - datetime.timedelta(days=event_date.weekday())  # Start of the week (Monday)

    # Iterate through the next 7 days (the entire week)
    for i in range(7):
        suggested_date = start_of_week + datetime.timedelta(days=i)
        if not check_event_exists(service, suggested_date):  # Check if the suggested date is free
            return suggested_date  # Return the first available date
    
    return None  # If no free days are found, return None

def create_event(event_date, event_name, name, phone, email):
    """
    Create an event on the specified date if no event exists on that day.
    If an event already exists, suggest an alternate date within the same week.
    """
    try:
        # Initialize a session state for storing responses to display in the UI
        if 'responses' not in st.session_state:
            st.session_state.responses = []

        # Check credentials and create the Google Calendar service object
        creds = check_credentials()
        service = build("calendar", "v3", credentials=creds)

        # Check if an event already exists on the specified date
        if check_event_exists(service, event_date):
            # Notify the user that an event already exists on that date
            event_message = f"An event already exists on {event_date}. Suggesting alternate date..."
            st.session_state.responses.append((None, event_message, None))  # Display in UI

            # Suggest an alternate date if possible
            alternate_date = suggest_alternate_date(service, event_date)
            if alternate_date:
                suggested_message = f"Suggested new date: {alternate_date}"
                st.session_state.responses.append((None, suggested_message, None))  # Display in UI
            else:
                st.session_state.responses.append((None, "No available dates found in the same week.", None))  # Display in UI
            return None  # Do not create the event if a collision occurs

        # If no event exists, proceed to create the new event
        event = {
            "summary": f"{event_name} - {name}, Phone: {phone}, Email: {email}",
            "start": {
                "dateTime": datetime.datetime.combine(event_date, datetime.time.min).isoformat(),
                "timeZone": "UTC",  # Set the event's time zone to UTC
            },
            "end": {
                "dateTime": (datetime.datetime.combine(event_date, datetime.time.min) + datetime.timedelta(hours=1)).isoformat(),
                "timeZone": "UTC",  # Set the event's end time to one hour later in UTC
            },
        }

        # Insert the event into the Google Calendar
        event_result = service.events().insert(calendarId="primary", body=event).execute()
        # Display the successful creation of the event in the UI
        st.session_state.responses.append(
            (None, f"Event created: {event_result['summary']} at {event_result['start']['dateTime']}", None)
        )

        return event_result  # Return the event result for further use

    except HttpError as error:
        # Handle errors from the Google Calendar API (e.g., network issues)
        st.session_state.responses.append(
            (None, f"An error occurred while creating the event: {error}", None)
        )  # Display error message in the UI
        return None  # Return None on error

def main():
    # Example event details
    event_date = datetime.datetime(2024, 12, 10)  # Example: December 10, 2024
    event_name = "Important Meeting"
    name = "John Doe"
    phone = "+1234567890"
    email = "john.doe@example.com"

    # Call create_event function to attempt creating the event
    create_event(event_date, event_name, name, phone, email)

if __name__ == "__main__":
    main()  # Execute the main function when the script is run
