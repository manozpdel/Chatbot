import smtplib                                  # Import for sending emails
from email.mime.text import MIMEText            # For creating email body as text
from email.mime.multipart import MIMEMultipart  # For handling multipart emails (text + attachments)
from datetime import datetime, timedelta        # For date/time operations

import streamlit as st                                    # Import for Streamlit (UI framework)
from langchain_ollama import OllamaLLM, OllamaEmbeddings  # For working with Ollama model and embeddings
from langchain_chroma import Chroma                       # For working with Chroma (vector database)
from event import create_event                            # Importing the event creation logic from another module
import re                                                 # For regular expression operations
import json                                               # For handling JSON data

from document_processing import *                         # Importing from document_processing 
from chat_template import prompt_template                 # Importing a prompt template for chat 

# Tool to send an email with appointment details
def send_email_tool(inputs):
    # Debugging log to inspect received inputs
    print(f"Debug: Received inputs for send_email_tool: {inputs}")

    # Ensure inputs are a dictionary or JSON string
    if isinstance(inputs, str):
        try:
            inputs = json.loads(inputs)  # Convert string input to a dictionary
        except json.JSONDecodeError:
            return f"Error: Expected a dictionary or JSON string, but got invalid input: {inputs}"

    if not isinstance(inputs, dict):
        return f"Error: Expected a dictionary, but got {type(inputs).__name__} with content: {inputs}"

    # Validate required keys in the input dictionary
    required_keys = {"name", "phone", "email", "appointment_date"}
    missing_keys = required_keys - inputs.keys()
    if missing_keys:
        return f"Error: Missing required fields: {', '.join(missing_keys)}"

    # Extract required fields from inputs
    try:
        name = inputs["name"]
        phone = inputs["phone"]
        email = inputs["email"]
        appointment_date = inputs["appointment_date"]
    except KeyError as e:
        return f"Error: Missing required field: {str(e)}"

    # Debugging log to verify extracted fields
    print(f"Debug: Extracted fields - Name: {name}, Phone: {phone}, Email: {email}, Appointment Date: {appointment_date}")

    # Email sending logic
    sender_email = "manojrajpdel@gmail.com"  # Sender email address
    receiver_email = email  # Receiver's email from the input
    password = "slny kprg sacf hnja"  # Sender's email app password 

    # Subject and body of the email
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

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Sending email via SMTP server (Gmail)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Start TLS encryption
            server.login(sender_email, password)  # Login to the email account
            server.sendmail(sender_email, receiver_email, message.as_string())  # Send the email
        return "Success: Email sent successfully!"  # Return success message
    except Exception as e:
        return f"Error: Failed to send email due to: {str(e)}"  # Handle failure in email sending

# Tool for creating an event (appointment) after validation
def create_event_tool_safe(inputs):
    # Step 1: Check if inputs are a dictionary
    if not isinstance(inputs, dict):
        try:
            # Attempt to parse string-like dictionary input
            import ast
            inputs = ast.literal_eval(inputs)  # Convert string to dictionary
        except Exception as e:
            return f"Invalid input: Expected a dictionary, got {type(inputs).__name__}. Error: {str(e)}"

    # Step 2: Check if all required keys are present in the input
    required_keys = {"appointment_date", "name", "phone", "email"}
    missing_keys = required_keys - inputs.keys()
    if missing_keys:
        return f"Invalid input: Missing required keys: {', '.join(missing_keys)}. Provided keys: {list(inputs.keys())}"

    # Step 3: Convert appointment_date to datetime if it's a string
    appointment_date = inputs["appointment_date"]
    if isinstance(appointment_date, str):
        try:
            # Parse the string into a datetime object
            appointment_date = datetime.fromisoformat(appointment_date)
            inputs["appointment_date"] = appointment_date
        except ValueError as e:
            return f"Invalid appointment_date format: {str(e)}"

    # Step 4: Call the actual tool function if inputs are valid
    return create_event_tool(
        appointment_date=appointment_date,
        name=inputs["name"],
        phone=inputs["phone"],
        email=inputs["email"],
    )

# Actual event creation logic
def create_event_tool(appointment_date, name, phone, email):
    # Call the event creation function imported from event.py
    response = create_event(appointment_date, name, name, phone, email)
    if response:
        return f"Appointment scheduled for {appointment_date}."  # Return success message
    else:
        return "Failed to schedule the appointment."  # Return failure message

# Tool for querying documents in ChromaDB
def query_document_tool(query_text):
    embedding_function = OllamaEmbeddings(model="nomic-embed-text")  # Use Ollama embeddings model for text
    db = Chroma(persist_directory="chroma", embedding_function=embedding_function)  # ChromaDB instance

    # Perform a similarity search in ChromaDB
    results = db.similarity_search_with_score(query_text, k=5)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])  # Concatenate document content

    # Format the prompt with context and query
    prompt = prompt_template.format(context=context_text, question=query_text)

    model = OllamaLLM(model="mistral")  # Use the Mistral model for generating a response
    response_text = model.invoke(prompt)  # Get the response from the model

    return response_text

# Tool for parsing relative days (appointment date)
def parse_relative_day_tool(user_input):
    today = datetime.today()  # Get the current date
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]  # List of weekdays

    match = re.match(r"(this|next)?\s*(\w+)", user_input.lower())  # Match user input for day parsing
    if match:
        prefix, day = match.groups()  # Extract "this" or "next" and the day name
        day = day.strip()  # Clean the day string
        if day in weekdays:
            day_index = weekdays.index(day)  # Get the index of the day
            current_day_index = today.weekday()  # Get the current day index

            # Calculate the number of days to the target day
            if prefix == "next":
                days_until = (day_index - current_day_index + 7) % 7 or 7
            else:
                days_until = (day_index - current_day_index + 7) % 7

            # Set the appointment date to the target day at 10:00 AM
            appointment_date = today + timedelta(days=days_until)
            appointment_date = appointment_date.replace(hour=10, minute=0, second=0, microsecond=0)
            return appointment_date  # Return the calculated appointment date

    return None  # Return None if no valid day is found
