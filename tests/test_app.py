"""Test cases for the Mergington High School Activities API."""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test."""
    # Store original activities
    from app import activities
    original = {name: details.copy() for name, details in activities.items()}
    original = {name: {**details, "participants": details["participants"].copy()} 
                for name, details in original.items()}
    yield
    # Reset to original state after test
    activities.clear()
    activities.update({name: {**details, "participants": details["participants"].copy()} 
                       for name, details in original.items()})


class TestGetActivities:
    """Tests for getting activities."""

    def test_get_activities(self, client):
        """Test retrieving all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) > 0

    def test_activities_structure(self, client):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_activities_have_participants(self, client):
        """Test that activities have participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have participants
        assert len(data["Chess Club"]["participants"]) >= 1
        assert isinstance(data["Chess Club"]["participants"][0], str)


class TestSignupForActivity:
    """Tests for signing up for activities."""

    def test_signup_success(self, client, reset_activities):
        """Test successfully signing up for an activity."""
        email = "test@mergington.edu"
        response = client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds participant to activity."""
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Tennis Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Tennis%20Club/signup?email={email}")
        
        # Check participant was added
        response = client.get("/activities")
        new_count = len(response.json()["Tennis Club"]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()["Tennis Club"]["participants"]

    def test_signup_duplicate_fails(self, client, reset_activities):
        """Test that signing up twice fails."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for nonexistent activity fails."""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]


class TestUnregisterFromActivity:
    """Tests for unregistering from activities."""

    def test_unregister_success(self, client, reset_activities):
        """Test successfully unregistering from an activity."""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity."""
        email = "michael@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Unregister
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Check participant was removed
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity fails."""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_registered_fails(self, client, reset_activities):
        """Test that unregistering when not registered fails."""
        email = "notregistered@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static files."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]
