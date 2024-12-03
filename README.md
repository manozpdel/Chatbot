# Chatbot

This project is a **Streamlit-based chatbot** application that integrates with **LangChain** to handle **conversational queries** and provides **appointment booking functionality**. The chatbot leverages AI models and tools to provide dynamic interactions, collect user details, and manage appointments seamlessly.

## Features

- **Conversational Interface**: A friendly chatbot to handle user queries and collect information.
- **Appointment Booking**: Supports booking appointments by collecting user details such as name, email, phone number, and preferred date.
- **Email and Event Creation**: Utilizes langchain tool agents to send confirmation emails and create calendar events.
- **Document Querying**: Can search a document database for context if required.
- **Error Handling**: Provides robust error handling for a smooth user experience.

## Tech Stack

- **Python**: Core programming language.
- **Streamlit**: For creating an interactive web-based user interface.
- **LangChain**: To manage conversational AI and integrate various tools.
- **OllamaLLM**: For natural language understanding and responses.
- **Custom Tools**: Implements functions for email sending, event creation, and document querying.


## Tools Integrated

1. **Send Email**: Sends confirmation emails to users.
2. **Create Event**: Schedules events on **google calendar** using user-provided details through **API**.
3. **Query Document**: Searches for context or information in the document database.
4. **Parse Date**: Processes user-provided relative dates like "next Monday" into specific calendar dates.

 
