import pytest
import json
from pathlib import Path
from unittest.mock import patch
from core.ai import generate_content

FORMATS_DIR = Path(__file__).parent.parent / "formats"

BRAND_CONFIG = {
    "ai_provider": "ollama",
    "ollama_model": "llama3.2",
    "brand": {
        "style": "minimal",
        "design_context": "Marca tecnológica minimalista.",
    },
}

VALID_RESPONSE = {
    "total_slides": 3,
    "slides": [
        {"type": "cover", "title": "Título", "subtitle": "Subtítulo"},
        {"type": "content", "heading": "Punto", "body": "Texto.", "use_image": False},
        {"type": "cta", "heading": "¿Listo?", "action": "Escríbenos"},
    ],
}


@patch("core.providers.ollama.ollama_client")
def test_generate_content_returns_valid_structure(mock_client):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_RESPONSE)}
    }
    result = generate_content("trabajo remoto", BRAND_CONFIG, FORMATS_DIR)
    assert "slides" in result
    assert result["total_slides"] == 3
    assert result["slides"][0]["type"] == "cover"


@patch("core.providers.ollama.ollama_client")
def test_retries_on_invalid_json(mock_client):
    mock_client.chat.side_effect = [
        {"message": {"content": "no es json"}},
        {"message": {"content": "tampoco"}},
        {"message": {"content": json.dumps(VALID_RESPONSE)}},
    ]
    result = generate_content("tema", BRAND_CONFIG, FORMATS_DIR)
    assert "slides" in result
    assert mock_client.chat.call_count == 3


@patch("core.providers.ollama.ollama_client")
def test_raises_after_three_failed_attempts(mock_client):
    mock_client.chat.return_value = {"message": {"content": "no es json"}}
    with pytest.raises(ValueError, match="JSON"):
        generate_content("tema", BRAND_CONFIG, FORMATS_DIR)
    assert mock_client.chat.call_count == 3


@patch("core.providers.ollama.ollama_client")
def test_raises_on_ollama_connection_error(mock_client):
    mock_client.chat.side_effect = Exception("connection refused")
    with pytest.raises(ConnectionError, match="Ollama"):
        generate_content("tema", BRAND_CONFIG, FORMATS_DIR)
