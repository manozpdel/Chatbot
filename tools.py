#Importing the dependencies
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from event import create_event
import re
from datetime import datetime, timedelta


# Function to send an email notification for a new appointment request
def send_email_tool(name, phone, email, appointment_date):
    # Sender and receiver email details
    sender_email = "manojrajpdel@gmail.com"
    receiver_email = email  # Email of the recipient (e.g., user who requested the appointment)
    password = " "  # Sender's email password (use app password for security)

    # Email subject and body content
    subject = "New Appointment Request"
    body = (
        f"Dear {name},\n\n"
        f"You have received a new appointment request.\n\n"
        f"Details:\n"
        f"Name: {name}\n"
        f"Phone Number: {phone}\n"
        f"Email: {email}\n"
        f"Appointment Date: {appointment_date}\n\n"
        f"Best regards,\n"
        f"Your Chatbot"
    )

    # Construct the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))  # Attach the body content as plain text

    try:
        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            server.login(sender_email, password)  # Login using the sender's email credentials (app password)
            server.sendmail(sender_email, receiver_email, message.as_string())  # Send the email
        return "Email sent successfully!"  # Success message if the email is sent
    except Exception as e:
        return f"Error sending email: {str(e)}"  # Error message if email sending fails

# Tool to create an event (appointment) in the system
def create_event_tool(appointment_date, name, phone, email):
    # Call the 'create_event' function to schedule the appointment
    response = create_event(appointment_date, name, name, phone, email)
    
    # Check if the event was created successfully and return the appropriate message
    if response:
        return f"Appointment scheduled for {appointment_date}."  # Success message
    else:
        return "Failed to schedule the appointment."  # Error message if event creation fails

# Tool to parse relative days (appointment date) based on user input
def parse_relative_day_tool(user_input):
    today = datetime.today()
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    match = re.match(r"(this|next)?\s*(\w+)", user_input.lower())
    if match:
        prefix, day = match.groups()
        day = day.strip()
        if day in weekdays:
            day_index = weekdays.index(day)
            current_day_index = today.weekday()

            if prefix == "next":
                days_until = (day_index - current_day_index + 7) % 7 or 7
            else:
                days_until = (day_index - current_day_index + 7) % 7

            appointment_date = today + timedelta(days=days_until)
            appointment_date = appointment_date.replace(hour=10, minute=0, second=0, microsecond=0)
            return appointment_date

    return None


