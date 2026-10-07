def test_create_room_and_list_available(client, make_room):
    make_room("A-101", capacity=1)
    make_room("A-102", capacity=2)
    rooms = client.get("/api/rooms").json()
    assert len(rooms) == 2
    assert all(r["vacancies"] == r["capacity"] for r in rooms)
    assert len(client.get("/api/rooms/available").json()) == 2


def test_allocate_student_updates_occupancy(client, make_room, make_student):
    room = make_room("B-201", capacity=2)
    student = make_student()

    resp = client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": student["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["occupied"] == 1 and body["vacancies"] == 1
    assert body["students"][0]["id"] == student["id"]

    assert client.get(f"/api/students/{student['id']}").json()["room_number"] == "B-201"


def test_full_room_rejects_allocation(client, make_room, make_student):
    room = make_room("C-301", capacity=1)
    first, second = make_student(), make_student()

    ok = client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": first["id"]})
    assert ok.status_code == 200

    full = client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": second["id"]})
    assert full.status_code == 409
    assert "full" in full.json()["detail"]

    available_ids = [r["id"] for r in client.get("/api/rooms/available").json()]
    assert room["id"] not in available_ids


def test_student_cannot_hold_two_rooms(client, make_room, make_student):
    r1, r2 = make_room("D-1"), make_room("D-2")
    student = make_student()
    client.post(f"/api/rooms/{r1['id']}/allocate", json={"student_id": student["id"]})
    resp = client.post(f"/api/rooms/{r2['id']}/allocate", json={"student_id": student["id"]})
    assert resp.status_code == 409


def test_deallocate_frees_bed(client, make_room, make_student):
    room = make_room("E-1", capacity=1)
    student = make_student()
    client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": student["id"]})

    # occupied rooms cannot be deleted
    assert client.delete(f"/api/rooms/{room['id']}").status_code == 409

    resp = client.post(f"/api/rooms/{room['id']}/deallocate", json={"student_id": student["id"]})
    assert resp.status_code == 200
    assert resp.json()["vacancies"] == 1
    assert client.delete(f"/api/rooms/{room['id']}").status_code == 204


def test_capacity_cannot_drop_below_occupancy(client, make_room, make_student):
    room = make_room("F-1", capacity=2)
    for s in (make_student(), make_student()):
        client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": s["id"]})
    resp = client.put(f"/api/rooms/{room['id']}", json={"capacity": 1})
    assert resp.status_code == 409


def test_allocate_unknown_student_returns_404(client, make_room):
    room = make_room()
    resp = client.post(f"/api/rooms/{room['id']}/allocate", json={"student_id": 999})
    assert resp.status_code == 404
