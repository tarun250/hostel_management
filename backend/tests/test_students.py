def test_register_and_fetch_student(client, make_student):
    created = make_student(full_name="Ananya Rao", roll_no="24BCS0042")
    assert created["room_id"] is None

    resp = client.get(f"/api/students/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Ananya Rao"

    listing = client.get("/api/students", params={"search": "ananya"}).json()
    assert [s["roll_no"] for s in listing] == ["24BCS0042"]


def test_duplicate_roll_number_rejected(client, make_student):
    make_student(roll_no="24BCS0001", email="a@college.edu")
    resp = client.post(
        "/api/students",
        json={"roll_no": "24BCS0001", "full_name": "Copy", "email": "b@college.edu", "course": "ECE"},
    )
    assert resp.status_code == 409


def test_invalid_student_payload_returns_422(client):
    resp = client.post("/api/students", json={"roll_no": "X1", "full_name": "No Email", "course": "ME"})
    assert resp.status_code == 422


def test_update_and_delete_student(client, make_student):
    student = make_student()
    resp = client.put(f"/api/students/{student['id']}", json={"year": 3, "phone": "9876543210"})
    assert resp.status_code == 200
    assert resp.json()["year"] == 3

    assert client.delete(f"/api/students/{student['id']}").status_code == 204
    assert client.get(f"/api/students/{student['id']}").status_code == 404
