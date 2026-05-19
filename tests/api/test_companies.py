def test_create_company(client):
    r = client.post("/api/v1/companies", json={
        "name": "Acme Studio",
        "style": "bold",
        "colors": {"primary": "#000", "secondary": "#fff", "background": "#eee", "text": "#111"},
        "fonts": {"heading": "Inter Bold", "body": "Inter"},
        "design_context": "Marca de moda urbana",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Acme Studio"
    assert data["slug"] == "acme-studio"


def test_list_companies(client):
    client.post("/api/v1/companies", json={"name": "A", "style": "minimal"})
    client.post("/api/v1/companies", json={"name": "B", "style": "bold"})
    r = client.get("/api/v1/companies")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_company(client):
    r = client.post("/api/v1/companies", json={"name": "Old Name", "style": "minimal"})
    company_id = r.json()["id"]
    r2 = client.put(f"/api/v1/companies/{company_id}", json={"name": "New Name", "style": "editorial"})
    assert r2.json()["name"] == "New Name"


def test_delete_company(client):
    r = client.post("/api/v1/companies", json={"name": "To Delete", "style": "minimal"})
    company_id = r.json()["id"]
    client.delete(f"/api/v1/companies/{company_id}")
    r2 = client.get("/api/v1/companies")
    assert len(r2.json()) == 0
