from datetime import date, timedelta


def test_maintenance_request_lifecycle(client, make_room):
    room = make_room("G-12")
    resp = client.post(
        "/api/maintenance",
        json={
            "room_id": room["id"],
            "title": "Ceiling fan not working",
            "category": "ELECTRICAL",
            "priority": "HIGH",
        },
    )
    assert resp.status_code == 201
    req = resp.json()
    assert req["status"] == "OPEN" and req["room_number"] == "G-12"

    patched = client.patch(f"/api/maintenance/{req['id']}/status", json={"status": "IN_PROGRESS"})
    assert patched.json()["status"] == "IN_PROGRESS"

    client.put(f"/api/maintenance/{req['id']}", json={"status": "RESOLVED"})
    assert client.get("/api/maintenance", params={"status": "OPEN"}).json() == []
    assert len(client.get("/api/maintenance", params={"status": "RESOLVED"}).json()) == 1


def test_maintenance_rejects_unknown_status(client, make_room):
    room = make_room()
    req = client.post("/api/maintenance", json={"room_id": room["id"], "title": "Leaking tap"}).json()
    resp = client.patch(f"/api/maintenance/{req['id']}/status", json={"status": "DONE_MAYBE"})
    assert resp.status_code == 422


def test_complaint_crud(client, make_student):
    student = make_student(full_name="Rahul Verma")
    resp = client.post(
        "/api/complaints",
        json={"student_id": student["id"], "subject": "Mess food served cold", "category": "MESS"},
    )
    assert resp.status_code == 201
    complaint = resp.json()
    assert complaint["student_name"] == "Rahul Verma"

    updated = client.put(f"/api/complaints/{complaint['id']}", json={"status": "CLOSED"})
    assert updated.json()["status"] == "CLOSED"

    assert client.delete(f"/api/complaints/{complaint['id']}").status_code == 204
    assert client.get("/api/complaints").json() == []


def test_complaint_for_missing_student_404(client):
    resp = client.post("/api/complaints", json={"student_id": 404, "subject": "Noise"})
    assert resp.status_code == 404


def test_visitor_check_in_and_out(client, make_student):
    student = make_student()
    entry = client.post(
        "/api/visitors",
        json={"student_id": student["id"], "visitor_name": "Mr. Sharma", "relation": "Father"},
    ).json()
    assert entry["check_out"] is None
    assert len(client.get("/api/visitors", params={"inside": True}).json()) == 1

    out = client.post(f"/api/visitors/{entry['id']}/checkout")
    assert out.status_code == 200 and out.json()["check_out"] is not None
    assert client.post(f"/api/visitors/{entry['id']}/checkout").status_code == 409
    assert client.get("/api/visitors", params={"inside": True}).json() == []


def test_fee_status_and_mark_paid(client, make_student):
    student = make_student()
    fee = client.post(
        "/api/fees",
        json={"student_id": student["id"], "term": "2026-SEM1", "amount": "27000.00",
              "due_date": str(date.today() - timedelta(days=3))},
    ).json()
    assert fee["status"] == "PENDING" and fee["overdue"] is True

    paid = client.put(f"/api/fees/{fee['id']}/pay", json={"payment_ref": "UPI-77812"})
    assert paid.status_code == 200
    body = paid.json()
    assert body["status"] == "PAID" and body["paid_on"] == str(date.today()) and body["overdue"] is False

    assert client.put(f"/api/fees/{fee['id']}/pay").status_code == 409
    assert client.get(f"/api/students/{student['id']}/fees").json()[0]["payment_ref"] == "UPI-77812"


def test_dashboard_summary(client, make_room, make_student):
    room = make_room("H-1", capacity=4)
    s1, s2 = make_student(), make_student()
    client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": s1["id"]})
    client.post("/api/complaints", json={"student_id": s2["id"], "subject": "Wi-Fi drops at night"})
    client.post("/api/maintenance", json={"room_id": room["id"], "title": "Broken window latch"})
    client.post(
        "/api/fees",
        json={"student_id": s2["id"], "term": "2026-SEM1", "amount": 25000, "due_date": "2099-01-01"},
    )

    summary = client.get("/api/stats/summary").json()
    assert summary["students"] == 2
    assert summary["unallocated_students"] == 1
    assert summary["total_beds"] == 4 and summary["occupied_beds"] == 1
    assert summary["occupancy_pct"] == 25.0
    assert summary["open_complaints"] == 1
    assert summary["open_maintenance"] == 1
    assert summary["pending_fees_count"] == 1
    assert float(summary["pending_fees_amount"]) == 25000.0
