# Generador de Carruseles — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CLI en Python que genera carruseles de Instagram como SVGs editables + PDF multipágina, usando Ollama para decidir contenido y estructura narrativa, con plantillas Jinja2 por estilo visual y config de empresa en YAML.

**Architecture:** El CLI (Typer) orquesta tres módulos independientes: `config.py` carga y valida el `brand.yaml` de la empresa; `ai.py` llama a Ollama con un prompt estructurado y devuelve JSON con la estructura del carrusel; `renderer.py` inyecta ese JSON en plantillas SVG Jinja2 y exporta SVGs individuales + un PDF multipágina. Las plantillas son archivos `.svg.j2` puramente visuales — sin texto hardcodeado.

**Tech Stack:** Python 3.11+, Typer, Jinja2, PyYAML, ollama (python-ollama), Rich, cairosvg, pypdf

---

## Estructura de archivos

```
generador-disenos/
├── cli.py
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── ai.py
│   ├── config.py
│   ├── renderer.py
│   └── providers/
│       ├── __init__.py
│       └── ollama.py
├── formats/
│   └── carousel/
│       ├── prompts/
│       │   └── carousel.txt
│       └── layouts/
│           ├── minimal/
│           │   ├── cover.svg.j2
│           │   ├── content.svg.j2
│           │   ├── content_icon.svg.j2
│           │   ├── stat.svg.j2
│           │   └── cta.svg.j2
│           ├── bold/        (mismos 5 archivos)
│           ├── editorial/   (mismos 5 archivos)
│           └── corporate/   (mismos 5 archivos)
├── companies/
│   └── ejemplo/
│       ├── brand.yaml
│       └── assets/
│           ├── logo.svg
│           ├── images/
│           └── icons/
├── output/
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_ai.py
    ├── test_renderer.py
    └── test_cli.py
```

---

## Task 1: Setup del proyecto

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `core/providers/__init__.py`
- Create: `tests/__init__.py`
- Create: directorios de estructura

- [ ] **Step 1: Crear estructura de directorios**

```bash
cd /Users/apple/Documents/ClaudeSkills/GeneradorDiseños
mkdir -p core/providers tests formats/carousel/prompts output companies/ejemplo/assets/images companies/ejemplo/assets/icons
mkdir -p formats/carousel/layouts/minimal formats/carousel/layouts/bold formats/carousel/layouts/editorial formats/carousel/layouts/corporate
touch core/__init__.py core/providers/__init__.py tests/__init__.py
```

- [ ] **Step 2: Crear requirements.txt**

```
typer[all]>=0.9.0
jinja2>=3.1.0
pyyaml>=6.0.0
ollama>=0.2.0
rich>=13.0.0
cairosvg>=2.7.0
pypdf>=4.0.0
pytest>=8.0.0
```

- [ ] **Step 3: Instalar dependencias del sistema (macOS)**

```bash
brew install cairo
```

- [ ] **Step 4: Instalar dependencias Python**

```bash
pip install -r requirements.txt
```

Expected: todas las dependencias instaladas sin error.

- [ ] **Step 5: Commit**

```bash
git init
git add requirements.txt core/__init__.py core/providers/__init__.py tests/__init__.py
git commit -m "chore: project setup and dependencies"
```

---

## Task 2: Config loader (`core/config.py`)

**Files:**
- Create: `core/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Escribir tests**

Crear `tests/test_config.py`:

```python
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
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError` o `ImportError` — `core.config` no existe aún.

- [ ] **Step 3: Implementar `core/config.py`**

```python
import yaml
from pathlib import Path

REQUIRED_FIELDS = [
    ("company",),
    ("brand", "style"),
    ("brand", "colors", "primary"),
    ("brand", "colors", "secondary"),
    ("brand", "colors", "background"),
    ("brand", "colors", "text"),
    ("brand", "fonts", "heading"),
    ("brand", "fonts", "body"),
    ("brand", "logo"),
]

VALID_STYLES = {"minimal", "bold", "editorial", "corporate"}


def load_brand_config(company_dir: Path) -> dict:
    yaml_path = company_dir / "brand.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"brand.yaml not found at {yaml_path}")

    with open(yaml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate_required_fields(config, yaml_path)
    _validate_style(config)
    _validate_logo(config, company_dir)
    return config


def _get_nested(data: dict, keys: tuple) -> object:
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def _validate_required_fields(config: dict, yaml_path: Path) -> None:
    for field_path in REQUIRED_FIELDS:
        if _get_nested(config, field_path) is None:
            field_str = ".".join(field_path)
            raise ValueError(f"Missing required field '{field_str}' in {yaml_path}")


def _validate_style(config: dict) -> None:
    style = config["brand"]["style"]
    if style not in VALID_STYLES:
        raise ValueError(
            f"Invalid style '{style}'. Valid options: {', '.join(sorted(VALID_STYLES))}"
        )


def _validate_logo(config: dict, company_dir: Path) -> None:
    logo_path = company_dir / config["brand"]["logo"]
    if not logo_path.exists():
        raise FileNotFoundError(f"Logo not found at {logo_path}")
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
pytest tests/test_config.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: config loader with validation"
```

---

## Task 3: Módulo de IA (`core/ai.py`, `core/providers/ollama.py`, `formats/carousel/prompts/carousel.txt`)

**Files:**
- Create: `core/ai.py`
- Create: `core/providers/ollama.py`
- Create: `formats/carousel/prompts/carousel.txt`
- Create: `tests/test_ai.py`

- [ ] **Step 1: Escribir tests**

Crear `tests/test_ai.py`:

```python
import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
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
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
pytest tests/test_ai.py -v
```

Expected: ImportError — módulos no existen aún.

- [ ] **Step 3: Crear el prompt `formats/carousel/prompts/carousel.txt`**

```
Eres un experto en diseño de contenido para redes sociales.
Genera la estructura de un carrusel de Instagram sobre el siguiente tema.

TEMA: {topic}

CONTEXTO DE MARCA: {design_context}

ESTILO VISUAL: {style}

TIPOS DE SLIDE DISPONIBLES:
- cover: Portada. Campos: title (máx 8 palabras), subtitle (opcional, máx 12 palabras)
- content: Slide de contenido. Campos: heading (máx 6 palabras), body (máx 25 palabras), use_image (true/false), image_hint (si use_image es true)
- content_icon: Contenido con ícono. Campos: heading (máx 6 palabras), body (máx 20 palabras), icon_hint (nombre del ícono en inglés, ej: "rocket", "check", "team")
- stat: Estadística destacada. Campos: number (ej: "87%", "3x", "2M"), label (máx 12 palabras)
- cta: Cierre y llamada a la acción. Campos: heading (máx 8 palabras), action (máx 10 palabras)

REGLAS:
- Entre 4 y 8 slides en total
- El primer slide siempre es cover, el último siempre es cta
- Los slides deben fluir narrativamente como una historia
- Usa content_icon para listas de beneficios o características
- Usa stat solo si el tema lo permite con datos reales o estimados
- Usa use_image: true solo cuando una imagen aporte valor real
- Textos concisos y directos, pensados para leer en mobile
- Responde ÚNICAMENTE con JSON válido, sin explicaciones, sin markdown

FORMATO DE RESPUESTA:
{{"total_slides": <n>, "slides": [...]}}
```

- [ ] **Step 4: Implementar `core/providers/ollama.py`**

```python
import ollama as ollama_client


class OllamaProvider:
    def __init__(self, model: str):
        self.model = model

    def complete(self, prompt: str) -> str:
        try:
            response = ollama_client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            return response["message"]["content"]
        except Exception as e:
            raise ConnectionError(
                f"No se pudo conectar con Ollama. ¿Está corriendo? "
                f"Inicia con: ollama serve\nError: {e}"
            )
```

- [ ] **Step 5: Implementar `core/ai.py`**

```python
import json
from pathlib import Path


def generate_content(topic: str, brand_config: dict, formats_dir: Path) -> dict:
    provider = _build_provider(brand_config)
    prompt = _build_prompt(topic, brand_config, formats_dir)

    last_raw = ""
    for _ in range(3):
        last_raw = provider.complete(prompt)
        try:
            return json.loads(last_raw)
        except json.JSONDecodeError:
            continue

    raise ValueError(
        f"La IA no devolvió JSON válido después de 3 intentos.\n"
        f"Última respuesta:\n{last_raw}"
    )


def _build_provider(brand_config: dict):
    provider_name = brand_config.get("ai_provider", "ollama")
    if provider_name == "ollama":
        from .providers.ollama import OllamaProvider
        return OllamaProvider(brand_config.get("ollama_model", "llama3.2"))
    raise ValueError(f"Proveedor de IA desconocido: '{provider_name}'")


def _build_prompt(topic: str, brand_config: dict, formats_dir: Path) -> str:
    prompt_path = formats_dir / "carousel" / "prompts" / "carousel.txt"
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(
        topic=topic,
        design_context=brand_config["brand"].get("design_context", ""),
        style=brand_config["brand"]["style"],
    )
```

- [ ] **Step 6: Verificar que los tests pasan**

```bash
pytest tests/test_ai.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add core/ai.py core/providers/ollama.py formats/carousel/prompts/carousel.txt tests/test_ai.py
git commit -m "feat: AI module with Ollama provider and retry logic"
```

---

## Task 4: Renderer (`core/renderer.py`)

**Files:**
- Create: `core/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Escribir tests**

Crear `tests/test_renderer.py`:

```python
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
        assert len(line) <= 25  # tolerancia por palabras largas

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

# --- render_carousel (integración con plantilla real) ---

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
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
pytest tests/test_renderer.py -v
```

Expected: ImportError — `core.renderer` no existe.

- [ ] **Step 3: Implementar `core/renderer.py`**

```python
import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import cairosvg
from pypdf import PdfWriter, PdfReader


def render_carousel(
    slides: list,
    brand_config: dict,
    company_dir: Path,
    output_dir: Path,
    formats_dir: Path,
) -> None:
    style = brand_config["brand"]["style"]
    layouts_dir = formats_dir / "carousel" / "layouts" / style

    env = Environment(loader=FileSystemLoader(str(layouts_dir)))
    env.filters["wrap_text"] = wrap_text

    slides_dir = output_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    svg_paths = []
    for i, slide in enumerate(slides, start=1):
        slide = _resolve_assets(slide, company_dir)
        template = env.get_template(f"{slide['type']}.svg.j2")
        svg_content = template.render(
            brand=brand_config["brand"],
            slide=slide,
            company=brand_config["company"],
        )
        svg_path = slides_dir / f"{i:02d}_{slide['type']}.svg"
        svg_path.write_text(svg_content, encoding="utf-8")
        svg_paths.append(svg_path)

    _generate_pdf(svg_paths, output_dir / "carousel.pdf")


def _resolve_assets(slide: dict, company_dir: Path) -> dict:
    slide = slide.copy()
    images_dir = company_dir / "assets" / "images"
    icons_dir = company_dir / "assets" / "icons"

    if slide.get("use_image") and "image_hint" in slide:
        slide["image_path"] = find_asset(images_dir, slide["image_hint"])
    if "icon_hint" in slide:
        slide["icon_path"] = find_asset(icons_dir, slide["icon_hint"])

    return slide


def _generate_pdf(svg_paths: list[Path], output_path: Path) -> None:
    writer = PdfWriter()
    for svg_path in svg_paths:
        pdf_bytes = cairosvg.svg2pdf(url=str(svg_path))
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer.add_page(reader.pages[0])
    with open(output_path, "wb") as f:
        writer.write(f)


def wrap_text(text: str, chars_per_line: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    lines, current = [], []
    for word in words:
        line_len = sum(len(w) for w in current) + len(current)
        if line_len + len(word) <= chars_per_line:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def find_asset(assets_dir: Path, hint: str) -> str | None:
    if not assets_dir.exists():
        return None
    hint_lower = hint.lower()
    for asset in sorted(assets_dir.iterdir()):
        name_lower = asset.stem.lower()
        if hint_lower in name_lower or any(w in name_lower for w in hint_lower.split()):
            return str(asset)
    return None
```

- [ ] **Step 4: Verificar que los tests pasan (los que no necesitan plantillas)**

```bash
pytest tests/test_renderer.py::test_wrap_text_short_string_stays_one_line tests/test_renderer.py::test_wrap_text_splits_long_string tests/test_renderer.py::test_wrap_text_empty_string tests/test_renderer.py::test_find_asset_exact_match tests/test_renderer.py::test_find_asset_partial_match tests/test_renderer.py::test_find_asset_no_match tests/test_renderer.py::test_find_asset_missing_dir -v
```

Expected: 7 tests PASSED. Los tests de `render_carousel` fallarán hasta que existan las plantillas (Task 5).

- [ ] **Step 5: Commit**

```bash
git add core/renderer.py tests/test_renderer.py
git commit -m "feat: renderer with text wrapping, asset resolution and PDF export"
```

---

## Task 5: Plantillas del estilo `minimal`

**Files:**
- Create: `formats/carousel/layouts/minimal/cover.svg.j2`
- Create: `formats/carousel/layouts/minimal/content.svg.j2`
- Create: `formats/carousel/layouts/minimal/content_icon.svg.j2`
- Create: `formats/carousel/layouts/minimal/stat.svg.j2`
- Create: `formats/carousel/layouts/minimal/cta.svg.j2`

- [ ] **Step 1: Crear `formats/carousel/layouts/minimal/cover.svg.j2`**

```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="80" y="200" width="80" height="6" fill="{{ brand.colors.secondary }}"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="50" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="88" fill="{{ brand.colors.primary }}">
    {% set lines = slide.title | wrap_text(16) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 380 + loop.index0 * 100 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% if slide.subtitle %}
  <text font-family="{{ brand.fonts.body }}" font-size="36" fill="{{ brand.colors.text }}" opacity="0.7">
    {% set lines = slide.subtitle | wrap_text(30) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 380 + (slide.title | wrap_text(16) | length) * 100 + 60 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% endif %}
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.text }}" opacity="0.4">{{ company }}</text>
</svg>
```

- [ ] **Step 2: Crear `formats/carousel/layouts/minimal/content.svg.j2`**

```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  {% if slide.image_path %}
  <image href="{{ slide.image_path }}" x="540" y="180" width="460" height="500" preserveAspectRatio="xMidYMid slice"/>
  <rect x="540" y="180" width="460" height="500" fill="{{ brand.colors.background }}" opacity="0.15"/>
  {% elif slide.use_image %}
  <rect x="540" y="180" width="460" height="500" fill="{{ brand.colors.primary }}" opacity="0.06" rx="8"/>
  <text x="770" y="450" font-family="{{ brand.fonts.body }}" font-size="18" fill="{{ brand.colors.text }}" opacity="0.35" text-anchor="middle">{{ slide.image_hint }}</text>
  {% endif %}
  <image href="{{ brand.logo }}" x="80" y="60" height="38" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="60" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(18) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 280 + loop.index0 * 72 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="80" y="{{ 280 + (slide.heading | wrap_text(18) | length) * 72 + 12 }}" width="50" height="4" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.text }}">
    {% set lines = slide.body | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 280 + (slide.heading | wrap_text(18) | length) * 72 + 80 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.text }}" opacity="0.4">{{ company }}</text>
</svg>
```

- [ ] **Step 3: Crear `formats/carousel/layouts/minimal/content_icon.svg.j2`**

```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <image href="{{ brand.logo }}" x="80" y="60" height="38" preserveAspectRatio="xMinYMid meet"/>
  {% if slide.icon_path %}
  <image href="{{ slide.icon_path }}" x="80" y="260" width="100" height="100" preserveAspectRatio="xMidYMid meet"/>
  {% else %}
  <rect x="80" y="260" width="100" height="100" fill="{{ brand.colors.secondary }}" opacity="0.15" rx="12"/>
  <text x="130" y="325" font-family="{{ brand.fonts.body }}" font-size="14" fill="{{ brand.colors.secondary }}" text-anchor="middle">{{ slide.icon_hint }}</text>
  {% endif %}
  <text font-family="{{ brand.fonts.heading }}" font-size="60" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(18) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 440 + loop.index0 * 72 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="80" y="{{ 440 + (slide.heading | wrap_text(18) | length) * 72 + 12 }}" width="50" height="4" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.text }}">
    {% set lines = slide.body | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 440 + (slide.heading | wrap_text(18) | length) * 72 + 80 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.text }}" opacity="0.4">{{ company }}</text>
</svg>
```

- [ ] **Step 4: Crear `formats/carousel/layouts/minimal/stat.svg.j2`**

```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="0" y="0" width="1080" height="8" fill="{{ brand.colors.secondary }}"/>
  <image href="{{ brand.logo }}" x="80" y="60" height="38" preserveAspectRatio="xMinYMid meet"/>
  <text x="540" y="540" font-family="{{ brand.fonts.heading }}" font-size="200" fill="{{ brand.colors.primary }}" text-anchor="middle">{{ slide.number }}</text>
  <rect x="440" y="570" width="200" height="5" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="36" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.label | wrap_text(32) %}
    {% for line in lines %}
    <tspan x="540" y="{{ 650 + loop.index0 * 48 }}" text-anchor="middle">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.text }}" opacity="0.4">{{ company }}</text>
</svg>
```

- [ ] **Step 5: Crear `formats/carousel/layouts/minimal/cta.svg.j2`**

```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.primary }}"/>
  <rect x="80" y="780" width="920" height="2" fill="{{ brand.colors.secondary }}" opacity="0.4"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="50" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="72" fill="{{ brand.colors.background }}">
    {% set lines = slide.heading | wrap_text(18) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 380 + loop.index0 * 86 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="80" y="{{ 380 + (slide.heading | wrap_text(18) | length) * 86 + 20 }}" width="60" height="5" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="38" fill="{{ brand.colors.secondary }}">
    {% set lines = slide.action | wrap_text(26) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 380 + (slide.heading | wrap_text(18) | length) * 86 + 100 + loop.index0 * 50 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.background }}" opacity="0.4">{{ company }}</text>
</svg>
```

- [ ] **Step 6: Verificar tests de render con plantillas minimal**

```bash
pytest tests/test_renderer.py -v
```

Expected: todos los tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add formats/carousel/layouts/minimal/
git commit -m "feat: minimal style SVG templates for all slide types"
```

---

## Task 6: CLI (`cli.py`)

**Files:**
- Create: `cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Escribir tests**

Crear `tests/test_cli.py`:

```python
import pytest
import yaml
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
    import json
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_SLIDES_RESPONSE)}
    }
    result = runner.invoke(app, ["carousel", "trabajo remoto", "--company", "acme"])
    assert result.exit_code == 0, result.output
    assert "Done!" in result.output or "slides" in result.output.lower()


def test_companies_command_lists_companies(company_dir):
    result = runner.invoke(app, ["companies"])
    assert result.exit_code == 0
    assert "Acme" in result.output


def test_styles_command_lists_all_styles(company_dir):
    result = runner.invoke(app, ["styles"])
    assert result.exit_code == 0
    for style in ["minimal", "bold", "editorial", "corporate"]:
        assert style in result.output
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
pytest tests/test_cli.py -v
```

Expected: ImportError — `cli.py` no existe.

- [ ] **Step 3: Implementar `cli.py`**

```python
import json
import re
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Generador de carruseles para Instagram.")
console = Console()

BASE_DIR = Path(__file__).parent
COMPANIES_DIR = BASE_DIR / "companies"
FORMATS_DIR = BASE_DIR / "formats"
OUTPUT_DIR = BASE_DIR / "output"

STYLE_DESCRIPTIONS = {
    "minimal": "Espacio en blanco, tipografía protagonista",
    "bold": "Fondos sólidos, alto contraste, formas geométricas",
    "editorial": "Asimétrico, grid roto, estética de revista",
    "corporate": "Limpio, márgenes generosos, estructura predecible",
}


@app.command()
def carousel(
    topic: str = typer.Argument(..., help="Tema o descripción del carrusel"),
    company: str = typer.Option(None, "--company", "-c", help="Carpeta en companies/"),
):
    """Genera un carrusel de Instagram para una empresa."""
    from core.config import load_brand_config
    from core.ai import generate_content
    from core.renderer import render_carousel

    company_dir = _resolve_company(company)
    brand_config = load_brand_config(company_dir)

    console.print(f"\n[bold]Generando carrusel:[/bold] {topic}")
    console.print(
        f"[dim]Empresa: {brand_config['company']} · Estilo: {brand_config['brand']['style']}[/dim]\n"
    )

    with console.status("Generando contenido con IA..."):
        slides_data = generate_content(topic, brand_config, FORMATS_DIR)

    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower())[:40].strip("-")
    output_dir = OUTPUT_DIR / company_dir.name / f"{date.today()}-{slug}"

    with console.status("Renderizando slides..."):
        render_carousel(
            slides_data["slides"], brand_config, company_dir, output_dir, FORMATS_DIR
        )

    (output_dir / "summary.json").write_text(
        json.dumps(slides_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    count = len(slides_data["slides"])
    console.print(f"[green]Done![/green] {count} slides generados.")
    console.print(f"  SVGs: [dim]{output_dir / 'slides'}[/dim]")
    console.print(f"  PDF:  [dim]{output_dir / 'carousel.pdf'}[/dim]\n")


@app.command()
def companies():
    """Lista las empresas configuradas."""
    from core.config import load_brand_config

    if not COMPANIES_DIR.exists():
        console.print("[yellow]No hay empresas configuradas.[/yellow]")
        console.print(f"Agrega una carpeta en: {COMPANIES_DIR}")
        return

    dirs = [d for d in sorted(COMPANIES_DIR.iterdir()) if d.is_dir()]
    if not dirs:
        console.print("[yellow]No hay empresas configuradas.[/yellow]")
        return

    table = Table(title="Empresas configuradas")
    table.add_column("Carpeta", style="cyan")
    table.add_column("Empresa")
    table.add_column("Estilo")

    for d in dirs:
        try:
            cfg = load_brand_config(d)
            table.add_row(d.name, cfg["company"], cfg["brand"]["style"])
        except Exception as e:
            table.add_row(d.name, f"[red]Error: {e}[/red]", "")

    console.print(table)


@app.command()
def styles():
    """Lista los estilos visuales disponibles."""
    table = Table(title="Estilos disponibles")
    table.add_column("Estilo", style="cyan")
    table.add_column("Descripción")
    for style, desc in STYLE_DESCRIPTIONS.items():
        table.add_row(style, desc)
    console.print(table)


def _resolve_company(company_name: str | None) -> Path:
    if company_name:
        path = COMPANIES_DIR / company_name
        if not path.exists():
            raise typer.BadParameter(
                f"Empresa '{company_name}' no encontrada en {COMPANIES_DIR}"
            )
        return path

    dirs = [d for d in COMPANIES_DIR.iterdir() if d.is_dir()] if COMPANIES_DIR.exists() else []
    if len(dirs) == 1:
        return dirs[0]
    if not dirs:
        raise typer.BadParameter(f"Sin empresas configuradas. Agrega una en {COMPANIES_DIR}")
    raise typer.BadParameter("Hay varias empresas. Especifica una con --company <nombre>")


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Verificar que los tests pasan**

```bash
pytest tests/test_cli.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 5: Verificar suite completa**

```bash
pytest -v
```

Expected: todos los tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add cli.py tests/test_cli.py
git commit -m "feat: CLI with carousel, companies, and styles commands"
```

---

## Task 7: Plantillas `bold`, `editorial`, `corporate`

**Files:**
- Create: `formats/carousel/layouts/bold/*.svg.j2` (5 archivos)
- Create: `formats/carousel/layouts/editorial/*.svg.j2` (5 archivos)
- Create: `formats/carousel/layouts/corporate/*.svg.j2` (5 archivos)

> Las plantillas de cada estilo siguen la misma estructura Jinja2 que `minimal` — mismas variables, mismos filtros. Lo que cambia son los valores visuales: posiciones, tamaños, fondos y formas.

- [ ] **Step 1: Crear plantillas `bold`**

Crear los 5 archivos en `formats/carousel/layouts/bold/`. Diferencias visuales vs minimal:
- Fondo de color `brand.colors.primary` (oscuro), texto en `brand.colors.background` (claro)
- Números y títulos en tamaño mayor (cover: 96px, stat: 220px)
- Rectángulos de color sólido como bloques decorativos
- Acento en `brand.colors.secondary` más prominente (10px alto vs 6px)

`bold/cover.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.primary }}"/>
  <rect x="0" y="860" width="1080" height="220" fill="{{ brand.colors.secondary }}"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="50" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="96" fill="{{ brand.colors.background }}">
    {% set lines = slide.title | wrap_text(14) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 360 + loop.index0 * 112 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% if slide.subtitle %}
  <text font-family="{{ brand.fonts.body }}" font-size="38" fill="{{ brand.colors.background }}" opacity="0.7">
    {% set lines = slide.subtitle | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 360 + (slide.title | wrap_text(14) | length) * 112 + 60 + loop.index0 * 48 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% endif %}
  <text x="80" y="940" font-family="{{ brand.fonts.body }}" font-size="28" fill="{{ brand.colors.primary }}" font-weight="bold">{{ company }}</text>
</svg>
```

`bold/content.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.primary }}"/>
  <rect x="0" y="0" width="10" height="1080" fill="{{ brand.colors.secondary }}"/>
  {% if slide.image_path %}
  <image href="{{ slide.image_path }}" x="540" y="0" width="540" height="1080" preserveAspectRatio="xMidYMid slice"/>
  <rect x="540" y="0" width="540" height="1080" fill="{{ brand.colors.primary }}" opacity="0.6"/>
  {% elif slide.use_image %}
  <rect x="540" y="0" width="540" height="1080" fill="{{ brand.colors.secondary }}" opacity="0.12"/>
  <text x="810" y="560" font-family="{{ brand.fonts.body }}" font-size="18" fill="{{ brand.colors.background }}" opacity="0.4" text-anchor="middle">{{ slide.image_hint }}</text>
  {% endif %}
  <image href="{{ brand.logo }}" x="30" y="60" height="40" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="64" fill="{{ brand.colors.background }}">
    {% set lines = slide.heading | wrap_text(16) %}
    {% for line in lines %}
    <tspan x="30" y="{{ 260 + loop.index0 * 76 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="30" y="{{ 260 + (slide.heading | wrap_text(16) | length) * 76 + 16 }}" width="60" height="6" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.background }}" opacity="0.85">
    {% set lines = slide.body | wrap_text(24) %}
    {% for line in lines %}
    <tspan x="30" y="{{ 260 + (slide.heading | wrap_text(16) | length) * 76 + 90 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="30" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.background }}" opacity="0.3">{{ company }}</text>
</svg>
```

`bold/content_icon.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.primary }}"/>
  <rect x="0" y="0" width="10" height="1080" fill="{{ brand.colors.secondary }}"/>
  <image href="{{ brand.logo }}" x="30" y="60" height="40" preserveAspectRatio="xMinYMid meet"/>
  {% if slide.icon_path %}
  <image href="{{ slide.icon_path }}" x="30" y="220" width="120" height="120" preserveAspectRatio="xMidYMid meet"/>
  {% else %}
  <rect x="30" y="220" width="120" height="120" fill="{{ brand.colors.secondary }}" opacity="0.3" rx="8"/>
  <text x="90" y="295" font-family="{{ brand.fonts.body }}" font-size="14" fill="{{ brand.colors.secondary }}" text-anchor="middle">{{ slide.icon_hint }}</text>
  {% endif %}
  <text font-family="{{ brand.fonts.heading }}" font-size="64" fill="{{ brand.colors.background }}">
    {% set lines = slide.heading | wrap_text(16) %}
    {% for line in lines %}
    <tspan x="30" y="{{ 420 + loop.index0 * 76 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="30" y="{{ 420 + (slide.heading | wrap_text(16) | length) * 76 + 16 }}" width="60" height="6" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.background }}" opacity="0.85">
    {% set lines = slide.body | wrap_text(24) %}
    {% for line in lines %}
    <tspan x="30" y="{{ 420 + (slide.heading | wrap_text(16) | length) * 76 + 90 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="30" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.background }}" opacity="0.3">{{ company }}</text>
</svg>
```

`bold/stat.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.secondary }}"/>
  <rect x="0" y="0" width="1080" height="200" fill="{{ brand.colors.primary }}"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="50" preserveAspectRatio="xMinYMid meet"/>
  <text x="540" y="620" font-family="{{ brand.fonts.heading }}" font-size="220" fill="{{ brand.colors.primary }}" text-anchor="middle">{{ slide.number }}</text>
  <text font-family="{{ brand.fonts.body }}" font-size="40" fill="{{ brand.colors.primary }}" opacity="0.9">
    {% set lines = slide.label | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="540" y="{{ 700 + loop.index0 * 52 }}" text-anchor="middle">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.primary }}" opacity="0.5">{{ company }}</text>
</svg>
```

`bold/cta.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.secondary }}"/>
  <rect x="0" y="0" width="1080" height="300" fill="{{ brand.colors.primary }}"/>
  <image href="{{ brand.logo }}" x="80" y="120" height="50" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="80" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(16) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 420 + loop.index0 * 96 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text font-family="{{ brand.fonts.body }}" font-size="40" fill="{{ brand.colors.primary }}" font-weight="bold">
    {% set lines = slide.action | wrap_text(22) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 420 + (slide.heading | wrap_text(16) | length) * 96 + 80 + loop.index0 * 54 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.primary }}" opacity="0.5">{{ company }}</text>
</svg>
```

- [ ] **Step 2: Crear plantillas `editorial`**

Diferencias visuales: layout asimétrico con línea diagonal/rotada, tipografía más grande en cover (120px), texto en ángulo decorativo para titular.

Crear los 5 archivos en `formats/carousel/layouts/editorial/`:

`editorial/cover.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="600" y="0" width="480" height="1080" fill="{{ brand.colors.primary }}" opacity="0.06"/>
  <rect x="600" y="0" width="6" height="1080" fill="{{ brand.colors.secondary }}"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="42" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="100" fill="{{ brand.colors.primary }}">
    {% set lines = slide.title | wrap_text(12) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 340 + loop.index0 * 116 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% if slide.subtitle %}
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.text }}" opacity="0.65">
    {% set lines = slide.subtitle | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 340 + (slide.title | wrap_text(12) | length) * 116 + 60 + loop.index0 * 42 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% endif %}
  <text x="620" y="990" font-family="{{ brand.fonts.heading }}" font-size="18" fill="{{ brand.colors.secondary }}" opacity="0.5" writing-mode="tb">{{ company }}</text>
</svg>
```

`editorial/content.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="0" y="500" width="1080" height="6" fill="{{ brand.colors.secondary }}" opacity="0.3"/>
  {% if slide.image_path %}
  <image href="{{ slide.image_path }}" x="0" y="506" width="1080" height="540" preserveAspectRatio="xMidYMid slice"/>
  <rect x="0" y="506" width="1080" height="540" fill="{{ brand.colors.background }}" opacity="0.5"/>
  {% elif slide.use_image %}
  <rect x="0" y="506" width="1080" height="540" fill="{{ brand.colors.primary }}" opacity="0.04"/>
  <text x="540" y="800" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.3" text-anchor="middle">{{ slide.image_hint }}</text>
  {% endif %}
  <image href="{{ brand.logo }}" x="900" y="40" height="36" preserveAspectRatio="xMaxYMid meet"/>
  <rect x="80" y="100" width="6" height="340" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="64" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(17) %}
    {% for line in lines %}
    <tspan x="110" y="{{ 180 + loop.index0 * 76 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text font-family="{{ brand.fonts.body }}" font-size="30" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.body | wrap_text(30) %}
    {% for line in lines %}
    <tspan x="110" y="{{ 180 + (slide.heading | wrap_text(17) | length) * 76 + 50 + loop.index0 * 42 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`editorial/content_icon.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="0" y="0" width="1080" height="180" fill="{{ brand.colors.primary }}"/>
  <image href="{{ brand.logo }}" x="80" y="70" height="40" preserveAspectRatio="xMinYMid meet"/>
  {% if slide.icon_path %}
  <image href="{{ slide.icon_path }}" x="880" y="260" width="100" height="100" preserveAspectRatio="xMidYMid meet"/>
  {% else %}
  <rect x="880" y="260" width="100" height="100" fill="{{ brand.colors.secondary }}" opacity="0.2" rx="50"/>
  <text x="930" y="325" font-family="{{ brand.fonts.body }}" font-size="13" fill="{{ brand.colors.secondary }}" text-anchor="middle">{{ slide.icon_hint }}</text>
  {% endif %}
  <text font-family="{{ brand.fonts.heading }}" font-size="64" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(17) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 300 + loop.index0 * 76 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="80" y="{{ 300 + (slide.heading | wrap_text(17) | length) * 76 + 14 }}" width="40" height="4" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="32" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.body | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 300 + (slide.heading | wrap_text(17) | length) * 76 + 80 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`editorial/stat.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="0" y="0" width="540" height="1080" fill="{{ brand.colors.primary }}" opacity="0.05"/>
  <rect x="540" y="0" width="4" height="1080" fill="{{ brand.colors.secondary }}" opacity="0.6"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="38" preserveAspectRatio="xMinYMid meet"/>
  <text x="270" y="580" font-family="{{ brand.fonts.heading }}" font-size="180" fill="{{ brand.colors.primary }}" text-anchor="middle">{{ slide.number }}</text>
  <text font-family="{{ brand.fonts.body }}" font-size="36" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.label | wrap_text(22) %}
    {% for line in lines %}
    <tspan x="600" y="{{ 480 + loop.index0 * 50 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`editorial/cta.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="0" y="0" width="1080" height="540" fill="{{ brand.colors.primary }}"/>
  <image href="{{ brand.logo }}" x="80" y="80" height="44" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="76" fill="{{ brand.colors.background }}">
    {% set lines = slide.heading | wrap_text(16) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 300 + loop.index0 * 90 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="80" y="560" width="920" height="5" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="40" fill="{{ brand.colors.primary }}">
    {% set lines = slide.action | wrap_text(26) %}
    {% for line in lines %}
    <tspan x="80" y="{{ 640 + loop.index0 * 54 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="80" y="990" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

- [ ] **Step 3: Crear plantillas `corporate`**

Diferencias visuales: márgenes más amplios (120px), líneas divisorias sutiles, colores siempre sobre fondo claro, sin elementos decorativos fuertes.

Crear los 5 archivos en `formats/carousel/layouts/corporate/`:

`corporate/cover.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="120" y="120" width="840" height="840" fill="{{ brand.colors.primary }}" opacity="0.03" rx="4"/>
  <rect x="120" y="120" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.4"/>
  <rect x="120" y="958" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.4"/>
  <image href="{{ brand.logo }}" x="120" y="160" height="44" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="82" fill="{{ brand.colors.primary }}">
    {% set lines = slide.title | wrap_text(15) %}
    {% for line in lines %}
    <tspan x="120" y="{{ 400 + loop.index0 * 96 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% if slide.subtitle %}
  <rect x="120" y="{{ 400 + (slide.title | wrap_text(15) | length) * 96 + 20 }}" width="40" height="3" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="34" fill="{{ brand.colors.text }}" opacity="0.65">
    {% set lines = slide.subtitle | wrap_text(30) %}
    {% for line in lines %}
    <tspan x="120" y="{{ 400 + (slide.title | wrap_text(15) | length) * 96 + 80 + loop.index0 * 44 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  {% endif %}
  <text x="120" y="920" font-family="{{ brand.fonts.body }}" font-size="22" fill="{{ brand.colors.text }}" opacity="0.4">{{ company }}</text>
</svg>
```

`corporate/content.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="120" y="100" width="2" height="880" fill="{{ brand.colors.secondary }}" opacity="0.25"/>
  {% if slide.image_path %}
  <image href="{{ slide.image_path }}" x="560" y="200" width="400" height="400" preserveAspectRatio="xMidYMid slice"/>
  <rect x="560" y="200" width="400" height="400" fill="{{ brand.colors.background }}" opacity="0.1"/>
  {% elif slide.use_image %}
  <rect x="560" y="200" width="400" height="400" fill="{{ brand.colors.primary }}" opacity="0.04" rx="4"/>
  <text x="760" y="415" font-family="{{ brand.fonts.body }}" font-size="16" fill="{{ brand.colors.text }}" opacity="0.3" text-anchor="middle">{{ slide.image_hint }}</text>
  {% endif %}
  <image href="{{ brand.logo }}" x="800" y="60" height="36" preserveAspectRatio="xMaxYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="58" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(18) %}
    {% for line in lines %}
    <tspan x="160" y="{{ 260 + loop.index0 * 70 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="160" y="{{ 260 + (slide.heading | wrap_text(18) | length) * 70 + 16 }}" width="36" height="3" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="30" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.body | wrap_text(30) %}
    {% for line in lines %}
    <tspan x="160" y="{{ 260 + (slide.heading | wrap_text(18) | length) * 70 + 76 + loop.index0 * 42 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="160" y="960" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`corporate/content_icon.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="120" y="100" width="2" height="880" fill="{{ brand.colors.secondary }}" opacity="0.25"/>
  <image href="{{ brand.logo }}" x="800" y="60" height="36" preserveAspectRatio="xMaxYMid meet"/>
  {% if slide.icon_path %}
  <image href="{{ slide.icon_path }}" x="160" y="220" width="80" height="80" preserveAspectRatio="xMidYMid meet"/>
  {% else %}
  <rect x="160" y="220" width="80" height="80" fill="{{ brand.colors.secondary }}" opacity="0.15" rx="4"/>
  <text x="200" y="270" font-family="{{ brand.fonts.body }}" font-size="12" fill="{{ brand.colors.secondary }}" text-anchor="middle">{{ slide.icon_hint }}</text>
  {% endif %}
  <text font-family="{{ brand.fonts.heading }}" font-size="58" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(18) %}
    {% for line in lines %}
    <tspan x="160" y="{{ 380 + loop.index0 * 70 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="160" y="{{ 380 + (slide.heading | wrap_text(18) | length) * 70 + 16 }}" width="36" height="3" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="30" fill="{{ brand.colors.text }}" opacity="0.8">
    {% set lines = slide.body | wrap_text(30) %}
    {% for line in lines %}
    <tspan x="160" y="{{ 380 + (slide.heading | wrap_text(18) | length) * 70 + 76 + loop.index0 * 42 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="160" y="960" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`corporate/stat.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="120" y="140" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.3"/>
  <rect x="120" y="940" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.3"/>
  <image href="{{ brand.logo }}" x="120" y="180" height="38" preserveAspectRatio="xMinYMid meet"/>
  <text x="540" y="580" font-family="{{ brand.fonts.heading }}" font-size="190" fill="{{ brand.colors.primary }}" text-anchor="middle">{{ slide.number }}</text>
  <rect x="380" y="600" width="320" height="3" fill="{{ brand.colors.secondary }}" opacity="0.4"/>
  <text font-family="{{ brand.fonts.body }}" font-size="34" fill="{{ brand.colors.text }}" opacity="0.75">
    {% set lines = slide.label | wrap_text(32) %}
    {% for line in lines %}
    <tspan x="540" y="{{ 670 + loop.index0 * 46 }}" text-anchor="middle">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="120" y="900" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

`corporate/cta.svg.j2`:
```svg
<svg width="1080" height="1080" xmlns="http://www.w3.org/2000/svg">
  <rect width="1080" height="1080" fill="{{ brand.colors.background }}"/>
  <rect x="120" y="140" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.3"/>
  <rect x="120" y="940" width="840" height="2" fill="{{ brand.colors.secondary }}" opacity="0.3"/>
  <image href="{{ brand.logo }}" x="120" y="180" height="44" preserveAspectRatio="xMinYMid meet"/>
  <text font-family="{{ brand.fonts.heading }}" font-size="70" fill="{{ brand.colors.primary }}">
    {% set lines = slide.heading | wrap_text(17) %}
    {% for line in lines %}
    <tspan x="120" y="{{ 400 + loop.index0 * 84 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <rect x="120" y="{{ 400 + (slide.heading | wrap_text(17) | length) * 84 + 20 }}" width="36" height="3" fill="{{ brand.colors.secondary }}"/>
  <text font-family="{{ brand.fonts.body }}" font-size="36" fill="{{ brand.colors.secondary }}">
    {% set lines = slide.action | wrap_text(28) %}
    {% for line in lines %}
    <tspan x="120" y="{{ 400 + (slide.heading | wrap_text(17) | length) * 84 + 84 + loop.index0 * 48 }}">{{ line }}</tspan>
    {% endfor %}
  </text>
  <text x="120" y="900" font-family="{{ brand.fonts.body }}" font-size="20" fill="{{ brand.colors.text }}" opacity="0.35">{{ company }}</text>
</svg>
```

- [ ] **Step 4: Verificar suite completa**

```bash
pytest -v
```

Expected: todos los tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add formats/carousel/layouts/bold/ formats/carousel/layouts/editorial/ formats/carousel/layouts/corporate/
git commit -m "feat: bold, editorial, and corporate style templates"
```

---

## Task 8: Empresa de ejemplo + prueba de humo end-to-end

**Files:**
- Create: `companies/ejemplo/brand.yaml`
- Create: `companies/ejemplo/assets/logo.svg`

- [ ] **Step 1: Crear logo SVG de ejemplo**

Crear `companies/ejemplo/assets/logo.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="50" viewBox="0 0 200 50">
  <rect width="40" height="40" y="5" rx="4" fill="#1A1A2E"/>
  <text x="50" y="34" font-family="Arial Bold, Arial" font-size="24" font-weight="bold" fill="#1A1A2E">Ejemplo</text>
</svg>
```

- [ ] **Step 2: Crear `companies/ejemplo/brand.yaml`**

```yaml
company: "Empresa Ejemplo"
ai_provider: ollama
ollama_model: llama3.2

brand:
  style: minimal
  colors:
    primary: "#1A1A2E"
    secondary: "#E94560"
    background: "#F8F8F8"
    text: "#2D2D2D"
  fonts:
    heading: "Georgia Bold"
    body: "Arial"
  logo: "assets/logo.svg"
  design_context: |
    Empresa de servicios digitales. Tono profesional pero cercano.
    Prefiere layouts limpios con mucho espacio. Audiencia: empresarios
    y emprendedores latinoamericanos entre 30-50 años.

resources:
  images: "assets/images/"
  icons: "assets/icons/"
```

- [ ] **Step 3: Verificar que Ollama está corriendo y tiene el modelo**

```bash
ollama serve &
ollama pull llama3.2
```

Expected: modelo descargado y servidor activo.

- [ ] **Step 4: Ejecutar prueba de humo end-to-end**

```bash
python cli.py carousel "5 beneficios del trabajo remoto" --company ejemplo
```

Expected output:
```
Generando carrusel: 5 beneficios del trabajo remoto
Empresa: Empresa Ejemplo · Estilo: minimal

Done! N slides generados.
  SVGs: .../output/ejemplo/2026-05-17-5-beneficios-del-trabajo-remoto/slides
  PDF:  .../output/ejemplo/2026-05-17-5-beneficios-del-trabajo-remoto/carousel.pdf
```

- [ ] **Step 5: Verificar archivos generados**

```bash
ls output/ejemplo/
```

Expected: directorio con fecha y slug del tema, conteniendo `slides/`, `carousel.pdf` y `summary.json`.

- [ ] **Step 6: Abrir el PDF y verificar que se ve correctamente**

Abrir `carousel.pdf` con Preview o Illustrator. Verificar:
- Múltiples páginas (una por slide)
- Colores y tipografía de la empresa aplicados
- Textos legibles y dentro de sus áreas

- [ ] **Step 7: Commit final**

```bash
git add companies/ejemplo/ output/.gitkeep
git commit -m "feat: example company config and smoke test passing"
```

---

## Resumen de comandos de uso

```bash
# Generar carrusel
python cli.py carousel "tu tema aquí" --company nombre-empresa

# Ver empresas configuradas
python cli.py companies

# Ver estilos disponibles
python cli.py styles

# Correr tests
pytest -v
```
