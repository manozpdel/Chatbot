import streamlit as st
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from langchain_ollama import OllamaLLM

# Import custom functions for document processing and agent tools
from document_processing import *
from agent_tools import *

# Define a list of phrases that trigger appointment booking process
contact_phrases = ["call me", "book appointment","appointment", "contact me", "i want to book appointment", "reach out", "get in touch"]

# Function to initialize the LangChain agent with various tools
def initialize_chatbot_agent():
    # Define the tools the agent will use
    tools = [
        Tool(
            name="Send Email",  # Tool to send an email
            func=send_email_tool,  # Function to send confirmation email
            description="Sends confirmation email to the user. Requires a dictionary with keys: name, phone, email, appointment_date."
        ),
        Tool(
            name="Create Event",  # Tool to create an event
            func=create_event_tool_safe,  # Function to create event
            description="Creates an event for the user. Requires a dictionary with keys: appointment_date, name, phone, email."
        ),
        Tool(
            name="Query Document",  # Tool to query documents for context
            func=query_document_tool,  # Function to query document
            description="Searches the document database for context. Input: query_text."
        ),
        Tool(
            name="Parse Date",  # Tool to parse date or day mentioned by the user
            func=parse_relative_day_tool,  # Function to parse date
            description="Parses relative day or date mentioned by the user. Input: user_input."
        ),
    ]

    # Initialize the LangChain model
    try:
        llm = OllamaLLM(model="mistral")  # Specify the model for LangChain
    except Exception as e:
        raise ValueError(f"Failed to initialize LLM: {e}")

    # Initialize the agent with the specified tools and model
    try:
        agent = initialize_agent(
            tools,  # List of tools
            llm,  # LangChain LLM
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # Zero-shot agent type
            verbose=True,  # Enable verbose output
            handle_parsing_errors=True  # Handle parsing errors gracefully
        )
        return agent  # Return the initialized agent
    except Exception as e:
        raise ValueError(f"Failed to initialize LangChain agent: {e}")

# Main function to run the chatbot interface
def main():
    st.title("Chatbot with Appointment Booking")  # Display the title of the app

    # Initialize session states to store conversation and user details
    if "responses" not in st.session_state:
        st.session_state.responses = []  # Store conversation history

    if "query_text" not in st.session_state:
        st.session_state.query_text = ""  # Store current query

    if "form_stage" not in st.session_state:
        st.session_state.form_stage = 0  # Track progress in the user input form

    if "user_details" not in st.session_state:
        st.session_state.user_details = {"Name": "", "Email": "", "Phone Number": "", "Appointment Date": ""}  # Store user details

    # Initialize the LangChain agent
    agent = initialize_chatbot_agent()

    # Display chat history
    st.write("### Chat History")
    for query, response, _ in st.session_state.responses:
        if query:
            st.markdown(
                f"""
                <div style="text-align: right; background-color: #e8f0fe; padding: 10px; margin: 5px; border-radius: 10px;">
                {query}
                </div>
                """,
                unsafe_allow_html=True,
            )
        if response:
            st.markdown(
                f"""
                <div style="text-align: left; background-color: #e6f4ea; padding: 10px; margin: 5px; border-radius: 10px;">
                {response}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Dynamically change the form based on the conversation stage
    with st.form(key="chat_form"):
        if st.session_state.form_stage == 0:
            query_text = st.text_input("Your prompt:", key="query_input")  # User inputs query
            submit_button = st.form_submit_button("Send")  # Send button to submit query

            if submit_button and query_text:
                # Check if query contains phrases indicating an appointment request
                if any(phrase in query_text.lower() for phrase in contact_phrases):
                    st.session_state.form_stage = 1  # Move to next stage (ask for name)
                    st.session_state.responses.append((query_text, "Sure! What's your name?", None))  # Respond asking for name
                else:
                    try:
                        response = agent.run(query_text)  # Get agent's response
                        st.session_state.responses.append((query_text, response, None))  # Store response
                    except Exception as e:
                        st.session_state.responses.append(
                            (query_text, f"An error occurred: {str(e)}", None)  # Error handling
                        )
                st.rerun()  # Rerun to refresh the interface

        # Handle subsequent form stages to collect user details
        elif st.session_state.form_stage == 1:
            name = st.text_input("Your name:")  # Collect user name
            submit_button = st.form_submit_button("Send")

            if submit_button and name.strip():
                st.session_state.user_details["Name"] = name  # Save user name
                st.session_state.responses.append((name, f"Nice to meet you, {name}! What's your email?", None))
                st.session_state.form_stage += 1  # Move to next form stage (email)
                st.rerun()

        elif st.session_state.form_stage == 2:
            email = st.text_input("Your email:")  # Collect user email
            submit_button = st.form_submit_button("Send")

            if submit_button and email.strip():
                st.session_state.user_details["Email"] = email  # Save email
                st.session_state.responses.append((email, "Got it! What's your phone number?", None))
                st.session_state.form_stage += 1  # Move to next form stage (phone)
                st.rerun()

        elif st.session_state.form_stage == 3:
            phone = st.text_input("Your phone number:")  # Collect user phone number
            submit_button = st.form_submit_button("Send")

            if submit_button and phone.strip():
                st.session_state.user_details["Phone Number"] = phone  # Save phone number
                st.session_state.responses.append((phone, "Thanks! When should we schedule the appointment?", None))
                st.session_state.form_stage += 1  # Move to next form stage (appointment date)
                st.rerun()

        elif st.session_state.form_stage == 4:
            appointment_text = st.text_input("When should we schedule the appointment?")  # Collect appointment date
            submit_button = st.form_submit_button("Send")

            if submit_button and appointment_text.strip():
                # Prepare agent query for booking appointment and sending confirmation
                try:
                    user_details = st.session_state.user_details
                    agent_query = (
                        f"Book an appointment and send a confirmation email with the following details:\n"
                        f"- Name: {user_details['Name']}\n"
                        f"- Email: {user_details['Email']}\n"
                        f"- Phone: {user_details['Phone Number']}\n"
                        f"- Preferred date: {appointment_text}\n"
                        f"Ensure that the appointment is created, and the user receives an email confirmation with all the details."
                    )

                    # Execute the agent's response
                    agent_response = agent.run(agent_query)
                    st.session_state.responses.append((appointment_text, agent_response, None))

                    # Reset form state after successful completion
                    st.session_state.form_stage = 0

                except Exception as e:
                    st.session_state.responses.append(
                        (appointment_text, f"An error occurred while scheduling: {str(e)}", None)  # Error handling
                    )
                st.rerun()

# Run the chatbot app when this script is executed
if __name__ == "__main__":
    main()
