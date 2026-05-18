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
    content = _prompt_for_text()
elif topic:
    mode = "topic"
    content = topic
else:
    # ni --text ni topic: error claro
    raise typer.BadParameter("Provee un tema o usa --text para pegar un artículo.")
```

### 4.3 Prompt interactivo `_prompt_for_text()`

```python
def _prompt_for_text() -> str:
    console.print("\n[bold]Pega el texto y presiona Enter dos veces cuando termines:[/bold]\n")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()
```

Condición de cierre: dos líneas vacías consecutivas (estándar para entrada multilinea en terminal).

---

## 5. Validación

| Situación | Comportamiento |
|-----------|----------------|
| Ni `topic` ni `--text` | Error: "Provee un tema o usa --text" |
| `--text` con `topic` también | `--text` tiene prioridad, ignora el topic |
| Texto pegado vacío | Error: "El texto no puede estar vacío" |
| IA devuelve JSON inválido | Reintento automático (mismo mecanismo existente, máx 3 intentos) |

---

## 6. Impacto en Tests

- `tests/test_ai.py`: actualizar firma de `generate_content` en todos los calls (agregar `mode="topic"`)
- `tests/test_cli.py`: agregar test para `--text` con mock de `_prompt_for_text`
- `tests/test_ai.py`: agregar test que verifica que `mode="text"` carga `carousel_text.txt`

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
