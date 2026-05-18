import pytest
import yaml
from pathlib import Path
from core.config import load_brand_config

@pytest.fixture
def valid_company_dir(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    config = {
        "company": "Test Co",
        "ai_provider": "ollama",
        "ollama_model": "llama3.2",
        "brand": {
            "style": "minimal",
            "colors": {
                "primary": "#000000",
                "secondary": "#FF0000",
                "background": "#FFFFFF",
                "text": "#333333",
            },
            "fonts": {"heading": "Arial Bold", "body": "Arial"},
            "logo": "assets/logo.svg",
            "design_context": "Marca de prueba.",
        },
        "resources": {"images": "assets/images/", "icons": "assets/icons/"},
    }
    (tmp_path / "brand.yaml").write_text(yaml.dump(config))
    return tmp_path

def test_load_valid_config(valid_company_dir):
    config = load_brand_config(valid_company_dir)
    assert config["company"] == "Test Co"
    assert config["brand"]["style"] == "minimal"
    assert config["brand"]["colors"]["primary"] == "#000000"

def test_missing_brand_yaml(tmp_path):
    with pytest.raises(FileNotFoundError, match="brand.yaml"):
        load_brand_config(tmp_path)

def test_missing_required_field(valid_company_dir):
    data = yaml.safe_load((valid_company_dir / "brand.yaml").read_text())
    del data["brand"]["style"]
    (valid_company_dir / "brand.yaml").write_text(yaml.dump(data))
    with pytest.raises(ValueError, match="brand.style"):
        load_brand_config(valid_company_dir)

def test_invalid_style(valid_company_dir):
    data = yaml.safe_load((valid_company_dir / "brand.yaml").read_text())
    data["brand"]["style"] = "neon-punk"
    (valid_company_dir / "brand.yaml").write_text(yaml.dump(data))
    with pytest.raises(ValueError, match="neon-punk"):
        load_brand_config(valid_company_dir)

def test_logo_not_found(valid_company_dir):
    data = yaml.safe_load((valid_company_dir / "brand.yaml").read_text())
    data["brand"]["logo"] = "assets/no-existe.svg"
    (valid_company_dir / "brand.yaml").write_text(yaml.dump(data))
    with pytest.raises(FileNotFoundError, match="no-existe.svg"):
        load_brand_config(valid_company_dir)
