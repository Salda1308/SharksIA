from unittest.mock import patch
import io


def test_upload_image(client):
    fake_image = io.BytesIO(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
        b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    r = client.post(
        "/api/v1/assets/upload",
        files={"file": ("test.png", fake_image, "image/png")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data["source"] == "upload"


def test_search_pexels(client):
    mock_response = {
        "photos": [
            {"id": 1, "src": {"medium": "http://img.pexels.com/1.jpg", "small": "http://img.pexels.com/1s.jpg"},
             "photographer": "Test", "alt": "coffee"}
        ]
    }
    with patch("api.routes.images.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        r = client.get("/api/v1/images/search?q=coffee&source=pexels")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == "pexels-1"
