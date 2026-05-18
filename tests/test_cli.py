import pytest
import yaml
import json
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch
from cli import app

runner = CliRunner()

VALID_SLIDES_RESPONSE = {
    "total_slides": 2,
    "slides": [
        {"type": "cover", "title": "Título", "subtitle": "Subtítulo"},
        {"type": "cta", "heading": "¿Listo?", "action": "Contáctanos"},
    ],
}


@pytest.fixture
def company_dir(tmp_path, monkeypatch):
    companies = tmp_path / "companies" / "acme"
    (companies / "assets").mkdir(parents=True)
    (companies / "assets" / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"></svg>'
    )
    config = {
        "company": "Acme",
        "ai_provider": "ollama",
        "ollama_model": "llama3.2",
        "brand": {
            "style": "minimal",
            "colors": {"primary": "#000", "secondary": "#F00", "background": "#FFF", "text": "#333"},
            "fonts": {"heading": "Arial Bold", "body": "Arial"},
            "logo": "assets/logo.svg",
            "design_context": "Prueba.",
        },
        "resources": {"images": "assets/images/", "icons": "assets/icons/"},
    }
    (companies / "brand.yaml").write_text(yaml.dump(config))

    import cli
    monkeypatch.setattr(cli, "COMPANIES_DIR", tmp_path / "companies")
    monkeypatch.setattr(cli, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(cli, "FORMATS_DIR", Path(__file__).parent.parent / "formats")
    return companies


@patch("core.providers.ollama.ollama_client")
def test_carousel_command_creates_output(mock_client, company_dir, tmp_path):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_SLIDES_RESPONSE)}
    }
    result = runner.invoke(app, ["carousel", "trabajo remoto", "--company", "acme"])
    assert result.exit_code == 0, result.output
    assert "Done!" in result.output


def test_companies_command_lists_companies(company_dir):
    result = runner.invoke(app, ["companies"])
    assert result.exit_code == 0
    assert "Acme" in result.output


def test_styles_command_lists_all_styles(company_dir):
    result = runner.invoke(app, ["styles"])
    assert result.exit_code == 0
    for style in ["minimal", "bold", "editorial", "corporate"]:
        assert style in result.output
