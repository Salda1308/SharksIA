# Modo Texto Largo — Spec de Diseño
**Fecha:** 2026-05-18
**Contexto:** Extensión del Generador de Carruseles v1

---

## 1. Visión General

Agregar un segundo modo de entrada al CLI: además del tema corto actual, el usuario puede pegar un artículo o texto largo directamente en la terminal. La IA extrae y condensa los puntos clave en vez de inventar contenido. Ambos modos coexisten y comparten el mismo pipeline de renderizado.

---

## 2. Cambios de Arquitectura

### 2.1 `core/ai.py`

La firma de `generate_content` cambia de:

```python
def generate_content(topic: str, brand_config: dict, formats_dir: Path) -> dict
```

A:

```python
def generate_content(
    mode: str,       # "topic" | "text"
    content: str,    # tema corto O texto largo según el modo
    brand_config: dict,
    formats_dir: Path
) -> dict
```

Internamente selecciona el archivo de prompt según `mode`:

| mode    | archivo de prompt              |
|---------|-------------------------------|
| `topic` | `carousel_topic.txt` (actual) |
| `text`  | `carousel_text.txt` (nuevo)   |

### 2.2 Archivos de prompt

```
formats/carousel/prompts/
├── carousel_topic.txt   # renombrado desde carousel.txt
└── carousel_text.txt    # nuevo
```

El contenido de `carousel_topic.txt` es idéntico al `carousel.txt` actual, con un cambio: la variable `{topic}` se renombra a `{content}` para que `_build_prompt` use siempre el mismo nombre de variable independientemente del modo. Así `.format(content=content, ...)` funciona igual para los dos archivos.

---

## 3. Prompt para Texto Largo (`carousel_text.txt`)

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

---

## 4. Cambios al CLI (`cli.py`)

### 4.1 Firma del comando `carousel`

```python
@app.command()
def carousel(
    topic: str = typer.Argument(None, help="Tema corto del carrusel"),
    text: bool = typer.Option(False, "--text", "-t", help="Pegar texto largo de forma interactiva"),
    company: str = typer.Option(None, "--company", "-c", help="Carpeta en companies/"),
):
```

`topic` pasa de requerido a opcional (`None` por defecto).

### 4.2 Lógica de resolución de modo

```python
if text:
    mode = "text"
    company_dir = _resolve_company_interactive(company)   # primero empresa
    content = _prompt_for_text()                          # luego texto
elif topic:
    mode = "topic"
    company_dir = _resolve_company(company)               # comportamiento actual
    content = topic
else:
    raise typer.BadParameter("Provee un tema o usa --text para pegar un artículo.")
```

### 4.3 Selección interactiva de empresa `_resolve_company_interactive()`

Se invoca solo en modo `--text`. Si `--company` ya fue pasado, lo usa directamente (mismo comportamiento actual). Si no, lista las empresas disponibles y pide al usuario que elija:

```
¿Para qué empresa generamos el carrusel?
  1. ejemplo
  2. acme-studio
Selecciona (1-2):
```

```python
def _resolve_company_interactive(company_name: str | None) -> Path:
    if company_name:
        return _resolve_company(company_name)   # reutiliza lógica existente

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
```

### 4.4 Prompt interactivo de texto `_prompt_for_text()`

```python
def _prompt_for_text() -> str:
    console.print("\n[bold]Pega el texto y presiona Enter dos veces cuando termines:[/bold]\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    text = "\n".join(lines).strip()
    if not text:
        raise typer.BadParameter("El texto no puede estar vacío.")
    return text
```

Condición de cierre: dos líneas vacías consecutivas (estándar para entrada multilinea en terminal).

---

## 5. Validación

| Situación | Comportamiento |
|-----------|----------------|
| Ni `topic` ni `--text` | Error: "Provee un tema o usa --text" |
| `--text` con `topic` también | `--text` tiene prioridad, ignora el topic |
| `--text` sin `--company`, una sola empresa | Auto-selecciona, muestra nombre en pantalla |
| `--text` sin `--company`, varias empresas | Pregunta interactivamente antes del texto |
| Texto pegado vacío | Error: "El texto no puede estar vacío" |
| IA devuelve JSON inválido | Reintento automático (mismo mecanismo existente, máx 3 intentos) |

---

## 6. Impacto en Tests

- `tests/test_ai.py`: actualizar firma de `generate_content` en todos los calls (agregar `mode="topic"`)
- `tests/test_ai.py`: agregar test que verifica que `mode="text"` carga `carousel_text.txt`
- `tests/test_cli.py`: agregar test para `--text` con mock de `_prompt_for_text` y `_resolve_company_interactive`
- `tests/test_cli.py`: agregar test de selección interactiva de empresa cuando hay varias configuradas

---

## 7. Archivos Modificados / Creados

| Acción | Archivo |
|--------|---------|
| Modificar | `core/ai.py` |
| Renombrar | `formats/carousel/prompts/carousel.txt` → `carousel_topic.txt` |
| Crear | `formats/carousel/prompts/carousel_text.txt` |
| Modificar | `cli.py` |
| Modificar | `tests/test_ai.py` |
| Modificar | `tests/test_cli.py` |
