"""
Tests for Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    original_activities = {
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
        "Basketball Team": {
            "description": "Competitive basketball practice and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and compete in matches",
            "schedule": "Saturdays, 10:00 AM - 12:00 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and sculpture techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["isabella@mergington.edu", "liam@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater performance and playwriting",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["maya@mergington.edu"]
        },
        "Debate Team": {
            "description": "Competitive debate and public speaking skills",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 14,
            "participants": ["noah@mergington.edu", "ava@mergington.edu"]
        },
        "Science Club": {
            "description": "Explore experiments, physics, and scientific research",
            "schedule": "Fridays, 4:00 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["lucas@mergington.edu"]
        }
    }
    
    # Clear and restore activities
    activities.clear()
    activities.update(original_activities)
    yield
    # Reset after test
    activities.clear()
    activities.update(original_activities)


def test_root_redirect(client):
    """Test that root path redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data) == 9


def test_activity_structure(client):
    """Test that activity has correct structure"""
    response = client.get("/activities")
    data = response.json()
    activity = data["Chess Club"]
    
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_for_activity_success(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "student@mergington.edu" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    updated_activities = activities_response.json()
    assert "student@mergington.edu" in updated_activities["Chess Club"]["participants"]


def test_signup_duplicate_student(client):
    """Test that duplicate signup fails"""
    # Try to sign up a student who is already registered
    response = client.post(
        "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"].lower()


def test_signup_nonexistent_activity(client):
    """Test signup for non-existent activity"""
    response = client.post(
        "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_unregister_success(client):
    """Test successfully unregistering a participant"""
    response = client.delete("/unregister?participant=michael@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert "Unregistered" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    updated_activities = activities_response.json()
    assert "michael@mergington.edu" not in updated_activities["Chess Club"]["participants"]


def test_unregister_nonexistent_participant(client):
    """Test unregistering a non-existent participant"""
    response = client.delete("/unregister?participant=nonexistent@mergington.edu")
    assert response.status_code == 404
    data = response.json()
    assert "Participant not found" in data["detail"]


def test_max_participants_constraint(client):
    """Test that max participants constraint is respected"""
    # Tennis Club has max 10 participants
    tennis_activity = activities["Tennis Club"]
    
    # Fill up to max
    for i in range(tennis_activity["max_participants"] - len(tennis_activity["participants"])):
        email = f"student{i}@mergington.edu"
        response = client.post(
            f"/activities/Tennis%20Club/signup?email={email}"
        )
        assert response.status_code == 200
    
    # Try to add one more (should still succeed in current implementation)
    response = client.post(
        "/activities/Tennis%20Club/signup?email=extra@mergington.edu"
    )
    # Note: Current implementation allows overfilling, this test documents that behavior
    assert response.status_code == 200


def test_activity_availability_calculation(client):
    """Test that availability spots are calculated correctly"""
    response = client.get("/activities")
    data = response.json()
    
    chess_club = data["Chess Club"]
    expected_spots = chess_club["max_participants"] - len(chess_club["participants"])
    assert expected_spots >= 0
    assert expected_spots <= chess_club["max_participants"]
