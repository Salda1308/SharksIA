from unittest.mock import patch

MOCK_SLIDES = {
    "total_slides": 2,
    "slides": [
        {"type": "cover", "title": "Test Cover", "subtitle": "Sub"},
        {"type": "cta", "heading": "Síguenos", "action": "en Instagram"},
    ],
}


def test_generate_carousel(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]

    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id,
            "mode": "topic",
            "content": "inteligencia artificial",
            "title": "Mi carrusel",
        })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "draft"
    assert len(data["slides"]) == 2


def test_update_slides(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]

    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        design_r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id, "mode": "topic",
            "content": "tema", "title": "titulo",
        })
    design_id = design_r.json()["id"]

    new_slides = [{"type": "cover", "title": "Editado", "subtitle": ""}]
    r = client.put(f"/api/v1/designs/{design_id}/slides",
                   json={"slides": new_slides})
    assert r.status_code == 200
    assert r.json()["slides"][0]["title"] == "Editado"


def _make_design(client):
    company_r = client.post("/api/v1/companies", json={
        "name": "Test Co", "style": "minimal",
        "colors": {"primary": "#000", "secondary": "#fff",
                   "background": "#fff", "text": "#000"},
        "fonts": {"heading": "Arial", "body": "Arial"},
        "design_context": "Prueba",
    })
    company_id = company_r.json()["id"]
    with patch("api.routes.carousel.generate_content", return_value=MOCK_SLIDES):
        r = client.post("/api/v1/designs/carousel/generate", json={
            "company_id": company_id, "mode": "topic",
            "content": "tema", "title": "titulo",
        })
    return r.json()["id"]


def test_render_carousel(client):
    design_id = _make_design(client)
    with patch("api.routes.carousel.render_carousel") as mock_render:
        mock_render.return_value = None
        r = client.post(f"/api/v1/designs/{design_id}/render")
    assert r.status_code == 200
    assert r.json()["status"] == "rendered"


def test_export_pdf_requires_render_first(client):
    design_id = _make_design(client)
    # No render first — should get 400
    r = client.get(f"/api/v1/designs/{design_id}/export?fmt=pdf")
    assert r.status_code == 400
