# app/

Purpose:
This is the entry point of the whole application.

Responsibility:
- Start the application
- Receive requests from UI
- Send requests to LangGraph
- Return responses back to user

Files:

main.py
What happens:
- Starts FastAPI server
- Creates API endpoints
- Receives student messages
- Calls graph workflow
- Returns final output

Flow:

Student
 ↓
API Request
 ↓
LangGraph
 ↓
Response
