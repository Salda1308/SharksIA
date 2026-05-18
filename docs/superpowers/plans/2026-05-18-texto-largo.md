# Modo Texto Largo — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar modo `--text` al CLI para que el usuario pueda pegar un artículo largo y la IA extraiga los puntos clave en vez de inventar contenido.

**Architecture:** `generate_content` recibe un nuevo parámetro `mode` ("topic"|"text") y elige el archivo de prompt según el modo. El CLI agrega el flag `--text`, selección interactiva de empresa y un prompt de entrada de texto multilinea. Los tests existentes se actualizan para la nueva firma.

**Tech Stack:** Python 3.11+, Typer, Rich (existentes)

---

## Archivos modificados / creados

| Acción | Archivo |
|--------|---------|
| Modificar | `core/ai.py` |
| Renombrar + editar | `formats/carousel/prompts/carousel.txt` → `carousel_topic.txt` |
| Crear | `formats/carousel/prompts/carousel_text.txt` |
| Modificar | `cli.py` |
| Modificar | `tests/test_ai.py` |
| Modificar | `tests/test_cli.py` |

---

## Task 1: Actualizar `core/ai.py` y renombrar prompt de tema

**Files:**
- Modify: `core/ai.py`
- Rename+edit: `formats/carousel/prompts/carousel.txt` → `formats/carousel/prompts/carousel_topic.txt`
- Modify: `tests/test_ai.py`

- [ ] **Step 1: Actualizar tests existentes con nueva firma**

Reemplazar el contenido de `tests/test_ai.py`:

```python
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
def test_generate_content_topic_returns_valid_structure(mock_client):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_RESPONSE)}
    }
    result = generate_content("topic", "trabajo remoto", BRAND_CONFIG, FORMATS_DIR)
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
    result = generate_content("topic", "tema", BRAND_CONFIG, FORMATS_DIR)
    assert "slides" in result
    assert mock_client.chat.call_count == 3


@patch("core.providers.ollama.ollama_client")
def test_raises_after_three_failed_attempts(mock_client):
    mock_client.chat.return_value = {"message": {"content": "no es json"}}
    with pytest.raises(ValueError, match="JSON"):
        generate_content("topic", "tema", BRAND_CONFIG, FORMATS_DIR)
    assert mock_client.chat.call_count == 3


@patch("core.providers.ollama.ollama_client")
def test_raises_on_ollama_connection_error(mock_client):
    mock_client.chat.side_effect = Exception("connection refused")
    with pytest.raises(ConnectionError, match="Ollama"):
        generate_content("topic", "tema", BRAND_CONFIG, FORMATS_DIR)


@patch("core.providers.ollama.ollama_client")
def test_text_mode_loads_text_prompt(mock_client):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_RESPONSE)}
    }
    result = generate_content(
        "text",
        "Un artículo de prueba sobre productividad en equipos remotos.",
        BRAND_CONFIG,
        FORMATS_DIR,
    )
    assert "slides" in result
```

- [ ] **Step 2: Verificar que los tests fallan**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest tests/test_ai.py -v 2>&1 | tail -15
```

Expected: `TypeError` — `generate_content()` recibe argumentos incorrectos.

- [ ] **Step 3: Renombrar el archivo de prompt y cambiar `{topic}` a `{content}`**

```bash
mv formats/carousel/prompts/carousel.txt formats/carousel/prompts/carousel_topic.txt
```

Editar `formats/carousel/prompts/carousel_topic.txt` — cambiar línea 4 de:
```
TEMA: {topic}
```
a:
```
TEMA: {content}
```

- [ ] **Step 4: Implementar nueva versión de `core/ai.py`**

Reemplazar el contenido completo de `core/ai.py`:

```python
import json
from pathlib import Path


def generate_content(
    mode: str,
    content: str,
    brand_config: dict,
    formats_dir: Path,
) -> dict:
    provider = _build_provider(brand_config)
    prompt = _build_prompt(mode, content, brand_config, formats_dir)

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


def _build_prompt(
    mode: str,
    content: str,
    brand_config: dict,
    formats_dir: Path,
) -> str:
    filename = "carousel_topic.txt" if mode == "topic" else "carousel_text.txt"
    prompt_path = formats_dir / "carousel" / "prompts" / filename
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(
        content=content,
        design_context=brand_config["brand"].get("design_context", ""),
        style=brand_config["brand"]["style"],
    )
```

- [ ] **Step 5: Verificar que los tests pasan**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest tests/test_ai.py -v 2>&1
```

Expected: 5 tests PASSED. El último (`test_text_mode_loads_text_prompt`) fallará con `FileNotFoundError` porque `carousel_text.txt` aún no existe — eso es esperado, se crea en Task 2.

- [ ] **Step 6: Commit**

```bash
git add core/ai.py tests/test_ai.py formats/carousel/prompts/carousel_topic.txt
git commit -m "feat: add mode param to generate_content, rename topic prompt"
```

---

## Task 2: Crear prompt para modo texto largo

**Files:**
- Create: `formats/carousel/prompts/carousel_text.txt`

- [ ] **Step 1: Crear `formats/carousel/prompts/carousel_text.txt`**

```
Eres un experto en diseño de contenido para redes sociales.
El usuario te entrega un texto o artículo. Tu tarea es transformarlo
en la estructura de un carrusel de Instagram.

TEXTO ORIGINAL:
{content}

CONTEXTO DE MARCA: {design_context}

ESTILO VISUAL: {style}

INSTRUCCIONES:
- NO inventes información que no esté en el texto original
- Extrae entre 3 y 6 puntos clave del texto
- Condensa cada punto a lenguaje directo y conciso para leer en mobile
- Mantén el orden narrativo del original si tiene sentido
- Si el texto incluye datos o estadísticas, úsalos en slides tipo "stat"
- El primer slide siempre es cover, el último siempre es cta

TIPOS DE SLIDE DISPONIBLES:
- cover: Portada. Campos: title (máx 8 palabras), subtitle (opcional, máx 12 palabras)
- content: Slide de contenido. Campos: heading (máx 6 palabras), body (máx 25 palabras), use_image (true/false), image_hint (si use_image es true)
- content_icon: Contenido con ícono. Campos: heading (máx 6 palabras), body (máx 20 palabras), icon_hint (nombre del ícono en inglés)
- stat: Estadística destacada. Campos: number (ej: "87%", "3x"), label (máx 12 palabras)
- cta: Cierre. Campos: heading (máx 8 palabras), action (máx 10 palabras)

Responde ÚNICAMENTE con JSON válido, sin explicaciones, sin markdown.

FORMATO DE RESPUESTA:
{{"total_slides": <n>, "slides": [...]}}
```

- [ ] **Step 2: Verificar que todos los tests de AI pasan**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest tests/test_ai.py -v 2>&1
```

Expected: 5 tests PASSED.

- [ ] **Step 3: Commit**

```bash
git add formats/carousel/prompts/carousel_text.txt
git commit -m "feat: add long text prompt for carousel generation"
```

---

## Task 3: Actualizar `cli.py`

**Files:**
- Modify: `cli.py`

- [ ] **Step 1: Reemplazar el contenido completo de `cli.py`**

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
    topic: str = typer.Argument(None, help="Tema corto del carrusel"),
    text: bool = typer.Option(False, "--text", "-t", help="Pegar texto largo de forma interactiva"),
    company: str = typer.Option(None, "--company", "-c", help="Carpeta en companies/"),
):
    """Genera un carrusel de Instagram para una empresa."""
    from core.config import load_brand_config
    from core.ai import generate_content
    from core.renderer import render_carousel

    if text:
        mode = "text"
        company_dir = _resolve_company_interactive(company)
        brand_config = load_brand_config(company_dir)
        content = _prompt_for_text()
    elif topic:
        mode = "topic"
        company_dir = _resolve_company(company)
        brand_config = load_brand_config(company_dir)
        content = topic
    else:
        raise typer.BadParameter("Provee un tema o usa --text para pegar un artículo.")

    preview = content[:60] + ("..." if len(content) > 60 else "")
    console.print(f"\n[bold]Generando carrusel:[/bold] {preview}")
    console.print(
        f"[dim]Empresa: {brand_config['company']} · Estilo: {brand_config['brand']['style']}[/dim]\n"
    )

    with console.status("Generando contenido con IA..."):
        slides_data = generate_content(mode, content, brand_config, FORMATS_DIR)

    slug = re.sub(r"[^a-z0-9]+", "-", content[:40].lower()).strip("-")
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


def _resolve_company_interactive(company_name: str | None) -> Path:
    if company_name:
        return _resolve_company(company_name)

    dirs = [d for d in sorted(COMPANIES_DIR.iterdir()) if d.is_dir()] \
           if COMPANIES_DIR.exists() else []

    if not dirs:
        raise typer.BadParameter(f"Sin empresas configuradas. Agrega una en {COMPANIES_DIR}")
    if len(dirs) == 1:
        console.print(f"[dim]Empresa: {dirs[0].name}[/dim]")
        return dirs[0]

    console.print("\n[bold]¿Para qué empresa generamos el carrusel?[/bold]")
    for i, d in enumerate(dirs, 1):
        console.print(f"  {i}. {d.name}")

    choice = typer.prompt("Selecciona", type=int)
    if not 1 <= choice <= len(dirs):
        raise typer.BadParameter("Opción inválida.")
    return dirs[choice - 1]


def _prompt_for_text() -> str:
    console.print("\n[bold]Pega el texto y presiona Enter dos veces cuando termines:[/bold]\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    result = "\n".join(lines).strip()
    if not result:
        raise typer.BadParameter("El texto no puede estar vacío.")
    return result


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Verificar que los tests existentes de CLI siguen pasando**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest tests/test_cli.py -v 2>&1
```

Expected: 3 tests PASSED (los tests existentes aún usan el modo topic con `--company`).

- [ ] **Step 3: Commit**

```bash
git add cli.py
git commit -m "feat: add --text flag, interactive company selection, multiline text input"
```

---

## Task 4: Tests para modo texto largo en CLI

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Agregar tests al final de `tests/test_cli.py`**

Añadir estas funciones al final del archivo existente:

```python
@patch("core.providers.ollama.ollama_client")
@patch("cli._prompt_for_text")
def test_carousel_text_mode_creates_output(mock_prompt, mock_client, company_dir, tmp_path):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_SLIDES_RESPONSE)}
    }
    mock_prompt.return_value = "Este es un artículo largo sobre trabajo remoto y productividad."
    result = runner.invoke(app, ["carousel", "--text", "--company", "acme"])
    assert result.exit_code == 0, result.output
    assert "Done!" in result.output


@patch("core.providers.ollama.ollama_client")
@patch("cli._prompt_for_text")
def test_carousel_text_mode_auto_selects_single_company(mock_prompt, mock_client, company_dir, tmp_path):
    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_SLIDES_RESPONSE)}
    }
    mock_prompt.return_value = "Artículo de prueba."
    result = runner.invoke(app, ["carousel", "--text"])
    assert result.exit_code == 0, result.output
    assert "Done!" in result.output


@patch("core.providers.ollama.ollama_client")
@patch("cli._prompt_for_text")
def test_carousel_text_mode_asks_company_when_multiple(mock_prompt, mock_client, tmp_path, monkeypatch):
    for name in ["empresa-a", "empresa-b"]:
        co = tmp_path / "companies" / name
        (co / "assets").mkdir(parents=True)
        (co / "assets" / "logo.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"></svg>'
        )
        cfg = {
            "company": name.title(),
            "ai_provider": "ollama",
            "ollama_model": "llama3.2",
            "brand": {
                "style": "minimal",
                "colors": {"primary": "#000", "secondary": "#F00", "background": "#FFF", "text": "#333"},
                "fonts": {"heading": "Arial Bold", "body": "Arial"},
                "logo": "assets/logo.svg",
                "design_context": "Test.",
            },
            "resources": {"images": "assets/images/", "icons": "assets/icons/"},
        }
        import yaml as _yaml
        (co / "brand.yaml").write_text(_yaml.dump(cfg))

    import cli
    monkeypatch.setattr(cli, "COMPANIES_DIR", tmp_path / "companies")
    monkeypatch.setattr(cli, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(cli, "FORMATS_DIR", Path(__file__).parent.parent / "formats")

    mock_client.chat.return_value = {
        "message": {"content": json.dumps(VALID_SLIDES_RESPONSE)}
    }
    mock_prompt.return_value = "Artículo de prueba sobre productividad."

    result = runner.invoke(app, ["carousel", "--text"], input="1\n")
    assert result.exit_code == 0, result.output
    assert "Done!" in result.output


def test_carousel_no_args_shows_error(company_dir):
    result = runner.invoke(app, ["carousel"])
    assert result.exit_code != 0
    assert "tema" in result.output.lower() or "text" in result.output.lower()
```

- [ ] **Step 2: Verificar que los tests nuevos fallan antes de implementar**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest tests/test_cli.py -v 2>&1 | tail -15
```

Expected: los 3 tests nuevos PASSED (el CLI ya fue implementado en Task 3). Si alguno falla, revisar el mock.

- [ ] **Step 3: Correr suite completa**

```bash
DYLD_LIBRARY_PATH=/opt/homebrew/lib python3 -m pytest -v 2>&1
```

Expected: 25 tests PASSED (21 anteriores + 4 nuevos).

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py tests/test_ai.py
git commit -m "test: add tests for --text mode and interactive company selection"
```
