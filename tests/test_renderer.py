import pytest
from pathlib import Path
from core.renderer import wrap_text, find_asset, render_carousel

# --- wrap_text ---

def test_wrap_text_short_string_stays_one_line():
    assert wrap_text("Hola mundo", 20) == ["Hola mundo"]

def test_wrap_text_splits_long_string():
    lines = wrap_text("Una frase bastante larga que no cabe en una sola línea", 20)
    assert len(lines) > 1
    for line in lines:
        assert len(line) <= 25

def test_wrap_text_empty_string():
    assert wrap_text("", 20) == []

# --- find_asset ---

def test_find_asset_exact_match(tmp_path):
    (tmp_path / "equipo.jpg").touch()
    result = find_asset(tmp_path, "equipo")
    assert result is not None
    assert "equipo" in result

def test_find_asset_partial_match(tmp_path):
    (tmp_path / "foto-equipo-remoto.jpg").touch()
    result = find_asset(tmp_path, "equipo remoto")
    assert result is not None

def test_find_asset_no_match(tmp_path):
    (tmp_path / "logo.svg").touch()
    result = find_asset(tmp_path, "cohete espacial")
    assert result is None

def test_find_asset_missing_dir():
    result = find_asset(Path("/no/existe"), "algo")
    assert result is None

# --- render_carousel ---

BRAND_CONFIG = {
    "company": "Test Co",
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
    },
}

SLIDES = [
    {"type": "cover", "title": "Título de prueba", "subtitle": "Subtítulo"},
    {"type": "cta", "heading": "¿Listo?", "action": "Escríbenos"},
]


def test_render_creates_svg_files(tmp_path):
    company_dir = tmp_path / "empresa"
    (company_dir / "assets").mkdir(parents=True)
    (company_dir / "assets" / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"></svg>'
    )
    output_dir = tmp_path / "output"
    formats_dir = Path(__file__).parent.parent / "formats"

    render_carousel(SLIDES, BRAND_CONFIG, company_dir, output_dir, formats_dir)

    slides_dir = output_dir / "slides"
    assert slides_dir.exists()
    assert (slides_dir / "01_cover.svg").exists()
    assert (slides_dir / "02_cta.svg").exists()


def test_render_creates_pdf(tmp_path):
    company_dir = tmp_path / "empresa"
    (company_dir / "assets").mkdir(parents=True)
    (company_dir / "assets" / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"></svg>'
    )
    output_dir = tmp_path / "output"
    formats_dir = Path(__file__).parent.parent / "formats"

    render_carousel(SLIDES, BRAND_CONFIG, company_dir, output_dir, formats_dir)

    assert (output_dir / "carousel.pdf").exists()
    assert (output_dir / "carousel.pdf").stat().st_size > 0
