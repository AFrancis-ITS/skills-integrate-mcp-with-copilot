"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
import os
from pathlib import Path
import json
from typing import Optional
import secrets

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Session management for teachers
teacher_sessions = {}  # token -> username

# Load teacher credentials
def load_teachers():
    teachers_path = Path(__file__).parent / "teachers.json"
    with open(teachers_path, "r") as f:
        return json.load(f)

teachers_data = load_teachers()

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/login")
def login(username: str, password: str):
    """Login endpoint for teachers"""
    # Check credentials
    for teacher in teachers_data["teachers"]:
        if teacher["username"] == username and teacher["password"] == password:
            # Create session token
            token = secrets.token_hex(16)
            teacher_sessions[token] = username
            response = JSONResponse({"message": "Login successful", "token": token})
            response.set_cookie("teacher_token", token, max_age=3600)
            return response
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/logout")
def logout(teacher_token: Optional[str] = Cookie(None)):
    """Logout endpoint for teachers"""
    if teacher_token and teacher_token in teacher_sessions:
        del teacher_sessions[teacher_token]
    
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("teacher_token")
    return response


@app.get("/teacher-status")
def get_teacher_status(teacher_token: Optional[str] = Cookie(None)):
    """Check if user is logged in as a teacher"""
    if teacher_token and teacher_token in teacher_sessions:
        return {"is_teacher": True, "username": teacher_sessions[teacher_token]}
    return {"is_teacher": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher_token: Optional[str] = Cookie(None)):
    """Sign up a student for an activity - only teachers can perform this action"""
    # Check if user is a teacher
    if not teacher_token or teacher_token not in teacher_sessions:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can sign up students for activities. Please log in."
        )
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Teacher {teacher_sessions[teacher_token]} signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher_token: Optional[str] = Cookie(None)):
    """Unregister a student from an activity - only teachers can perform this action"""
    # Check if user is a teacher
    if not teacher_token or teacher_token not in teacher_sessions:
        raise HTTPException(
            status_code=403,
            detail="Only teachers can unregister students from activities. Please log in."
        )
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Teacher {teacher_sessions[teacher_token]} unregistered {email} from {activity_name}"}
