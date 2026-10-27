from io import BytesIO
from fastapi.testclient import TestClient
from app.main import app


def login(client):
    response = client.post("/auth/login", json={"email": "student@civicfix.edu", "password": "Student@123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_and_login():
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        assert client.post("/auth/login", json={"email": "student@civicfix.edu", "password": "wrong-password"}).status_code == 401
        assert login(client)["Authorization"].startswith("Bearer ")


def test_submit_and_list_report():
    with TestClient(app) as client:
        headers = login(client)
        response = client.post("/reports", headers=headers, data={
            "description": "Large pothole outside the library entrance.", "category": "Pothole", "location_name": "Central Library",
        }, files={"image": ("pothole.png", BytesIO(b"fake image bytes"), "image/png")})
        assert response.status_code == 201
        assert response.json()["status"] == "AI Verified"
        assert response.json()["priority_score"] is not None
        assert response.json()["ai_provider"] == "mock-explainable-v1"
        assert client.get("/reports", headers=headers).status_code == 200


def test_analysis_endpoint_returns_explainable_priority():
    with TestClient(app) as client:
        headers = login(client)
        report = client.post("/reports", headers=headers, data={
            "description": "A deep pothole is dangerous at night and could cause an accident.", "category": "Pothole", "location_name": "Main Library",
        }, files={"image": ("pothole.png", BytesIO(b"fake image bytes"), "image/png")}).json()
        result = client.post(f"/reports/{report['id']}/analyze", headers=headers)
        assert result.status_code == 200
        data = result.json()
        assert data["severity"] >= 7
        assert sum(data["priority_breakdown"].values()) == data["priority_score"]


def test_duplicate_support_and_admin_workflow():
    with TestClient(app) as client:
        student_headers = login(client)
        create = lambda description: client.post("/reports", headers=student_headers, data={"description": description, "category": "Pothole", "location_name": "Central Library"}, files={"image": ("p.png", BytesIO(b"image"), "image/png")})
        original = create("A deep pothole outside the library entrance is dangerous.").json()
        matches = client.post("/reports/duplicate-check", headers=student_headers, json={"category": "Pothole", "location_name": "Central Library", "description": "Dangerous deep pothole at the library entrance."})
        assert matches.status_code == 200 and matches.json()[0]["report"]["id"] == original["id"]
        supported = client.post(f"/reports/{original['id']}/support", headers=student_headers)
        assert supported.json()["support_count"] == 1
        admin_login = client.post("/auth/login", json={"email": "admin@civicfix.edu", "password": "Admin@123"}).json()
        admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
        assert client.put(f"/admin/reports/{original['id']}/assignment", headers=admin_headers, json={"assigned_to": "Facilities Team A"}).json()["status"] == "Assigned"
        resolved = client.put(f"/admin/reports/{original['id']}/status", headers=admin_headers, json={"status": "Resolved", "resolution_note": "Road surface repaired."})
        assert resolved.json()["resolution_note"] == "Road surface repaired."


def test_map_and_analytics_feeds():
    with TestClient(app) as client:
        headers = login(client)
        client.post("/reports", headers=headers, data={"description": "Overflowing waste bin beside the canteen entrance.", "category": "Garbage overflow", "location_name": "Canteen"}, files={"image": ("g.png", BytesIO(b"image"), "image/png")})
        assert client.get("/map/reports", headers=headers).json()[0]["latitude"] is not None
        analytics = client.get("/analytics", headers=headers).json()
        assert analytics["reports_by_category"][0]["name"] == "Garbage overflow"


def test_prediction_fallback_is_clearly_marked_demo_data():
    with TestClient(app) as client:
        prediction = client.get("/predictions", headers=login(client)).json()
        assert prediction["is_demo_data"] is True
        assert "demo" in prediction["method"]


def test_campus_isolation():
    with TestClient(app) as client:
        main_student = login(client)
        main_report = client.post("/reports", headers=main_student, data={
            "description": "A large pothole outside the main library entrance.", "category": "Pothole", "location_name": "Main Library",
        }, files={"image": ("p.png", BytesIO(b"image"), "image/png")}).json()

        north_login = client.post("/auth/login", json={"email": "student.north@civicfix.edu", "password": "Student@123"}).json()
        assert north_login["user"]["campus_id"] == "north-campus"
        north_student = {"Authorization": f"Bearer {north_login['access_token']}"}

        # A North Gate student must never see a Main Campus report.
        assert main_report["id"] not in [r["id"] for r in client.get("/reports", headers=north_student).json()]

        north_admin_login = client.post("/auth/login", json={"email": "admin.north@civicfix.edu", "password": "Admin@123"}).json()
        north_admin = {"Authorization": f"Bearer {north_admin_login['access_token']}"}

        # Nor may a North Gate admin see, assign, or resolve it, even by ID.
        assert main_report["id"] not in [r["id"] for r in client.get("/admin/dashboard", headers=north_admin).json()["priority_queue"]]
        assert client.put(f"/admin/reports/{main_report['id']}/assignment", headers=north_admin, json={"assigned_to": "Someone"}).status_code == 404

        # The Main Campus admin can, since it is their own campus.
        main_admin_login = client.post("/auth/login", json={"email": "admin@civicfix.edu", "password": "Admin@123"}).json()
        main_admin = {"Authorization": f"Bearer {main_admin_login['access_token']}"}
        assert client.put(f"/admin/reports/{main_report['id']}/assignment", headers=main_admin, json={"assigned_to": "Facilities Team A"}).status_code == 200


def test_rejects_unauthorized_and_invalid_file():
    with TestClient(app) as client:
        assert client.get("/reports").status_code == 403
        response = client.post("/reports", headers=login(client), data={
            "description": "A broken light on the east pathway.", "category": "Broken streetlight", "location_name": "East Path",
        }, files={"image": ("invalid.pdf", BytesIO(b"no"), "application/pdf")})
        assert response.status_code == 415
