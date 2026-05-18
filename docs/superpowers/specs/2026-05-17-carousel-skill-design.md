# Generador de Diseños — Spec de Diseño
**Fecha:** 2026-05-17
**Formato inicial:** Carrusel de Instagram
**Expansión futura:** Posters, historias (misma arquitectura)

---

## 1. Visión General

CLI en Python que genera carruseles de Instagram listos para editar en Adobe Illustrator o Canva. Dado un tema en texto, usa un modelo de IA local (Ollama) para decidir la estructura narrativa, cantidad de slides y distribución de contenido. Aplica la identidad visual de la empresa mediante un archivo de configuración y plantillas SVG con Jinja2.

---

## 2. Arquitectura

```
generador-disenos/
├── cli.py                        # Punto de entrada CLI (Typer)
├── core/
│   ├── ai.py                     # Interfaz común de IA
│   ├── providers/
│   │   ├── ollama.py             # Implementación Ollama (default)
│   │   └── claude.py             # Implementación Claude API (futura)
│   ├── config.py                 # Carga y valida brand.yaml
│   └── renderer.py               # Renderiza plantillas Jinja2 → SVG
├── formats/
│   └── carousel/
│       ├── layouts/
│       │   ├── minimal/          # Estilo: espacio en blanco, tipografía protagonista
│       │   ├── bold/             # Estilo: fondos sólidos, alto contraste
│       │   ├── editorial/        # Estilo: asimétrico, tipo revista
│       │   └── corporate/        # Estilo: limpio, estructurado
│       └── prompts/
│           └── carousel.txt      # Prompt base para decisiones de layout
├── companies/
│   └── {empresa}/
│       ├── brand.yaml
│       └── assets/
│           ├── logo.svg
│           ├── images/           # Imágenes provistas por el usuario
│           └── icons/            # Íconos vectoriales reutilizables
└── output/
    └── {empresa}/
        └── {fecha}-{tema-slug}/
            ├── 01_cover.svg
            ├── 02_content.svg
            ├── ...
            └── summary.json
```

---

## 3. Config de Empresa (`brand.yaml`)

```yaml
company: "Nombre Empresa"
ai_provider: ollama          # ollama | claude
ollama_model: llama3.2

brand:
  style: minimal             # minimal | bold | editorial | corporate
  colors:
    primary: "#1A1A2E"
    secondary: "#E94560"
    background: "#F5F5F5"
    text: "#333333"
  fonts:
    heading: "Montserrat Bold"
    body: "Inter Regular"
  logo: "assets/logo.svg"
  design_context: |
    Descripción libre del estilo y personalidad de la marca.
    Guía a la IA en tono y decisiones de contenido.

resources:
  images: "assets/images/"
  icons: "assets/icons/"
```

**Validación:** `config.py` verifica que existan los campos requeridos (`company`, `brand.style`, `brand.colors`, `brand.fonts`, `brand.logo`) y que el logo y las rutas de assets existan en disco antes de continuar.

---

## 4. Flujo de IA

### 4.1 Entrada al modelo

`ai.py` construye un prompt con:
- El tema ingresado por el usuario
- El `design_context` de la empresa
- El estilo visual seleccionado
- Los tipos de slide disponibles con sus descripciones

### 4.2 Respuesta esperada (JSON estricto)

```json
{
  "total_slides": 5,
  "slides": [
    {
      "type": "cover",
      "title": "Título principal",
      "subtitle": "Subtítulo opcional"
    },
    {
      "type": "content",
      "heading": "Punto clave",
      "body": "Desarrollo del punto en 2-3 líneas.",
      "use_image": false
    },
    {
      "type": "content",
      "heading": "Otro punto",
      "body": "Texto de apoyo.",
      "use_image": true,
      "image_hint": "descripción de la imagen ideal"
    },
    {
      "type": "content_icon",
      "heading": "Punto con ícono",
      "body": "Texto de apoyo.",
      "icon_hint": "nombre o descripción del ícono (ej: 'check', 'rocket', 'team')"
    },
    {
      "type": "stat",
      "number": "87%",
      "label": "de los equipos remotos reportan mayor productividad"
    },
    {
      "type": "cta",
      "heading": "¿Listo para el cambio?",
      "action": "Escríbenos en el link de la bio"
    }
  ]
}
```

El modelo debe responder **únicamente JSON válido**, sin texto adicional. Si la respuesta no es parseable, el sistema reintenta hasta 2 veces antes de abortar con mensaje de error.

### 4.3 Abstracción de proveedor

`ai.py` expone una única función:
```python
def generate_content(topic: str, brand_config: dict) -> dict
```

`config.py` determina qué proveedor instanciar según `ai_provider` en `brand.yaml`. Agregar Claude en el futuro = crear `providers/claude.py` con la misma firma. No se modifica nada más.

---

## 5. Sistema de Plantillas

### 5.1 Tipos de slide

| Tipo | Descripción |
|------|-------------|
| `cover` | Portada: título grande, subtítulo, logo |
| `content` | Texto con o sin imagen lateral |
| `content_icon` | Texto con ícono vectorial pequeño |
| `stat` | Número grande + label descriptivo |
| `cta` | Llamada a la acción + cierre |

### 5.2 Estilos visuales

| Estilo | Características |
|--------|-----------------|
| `minimal` | Mucho espacio en blanco, tipografía como elemento visual |
| `bold` | Fondos de color sólido, contrastes fuertes, formas geométricas |
| `editorial` | Asimétrico, grid roto, estética de revista |
| `corporate` | Limpio, márgenes generosos, estructura predecible |

Cada estilo tiene su propio directorio con las 5 plantillas (una por tipo de slide). Los estilos son compartidos entre todas las empresas — el `brand.yaml` diferencia el resultado final.

### 5.3 Estructura de plantillas

Las plantillas son **puramente estructurales y visuales** — no contienen texto hardcodeado. Definen:
- Fondos, formas y áreas de color
- Posición y tamaño del logo (`<image href="{{ brand.logo }}">`)
- Áreas de imagen con dimensiones fijas (`<image href="{{ slide.image_path }}">`)
- Posiciones y estilos de texto vacíos (`<text>{{ slide.title }}</text>`)

Todo el contenido textual viene de la respuesta JSON de la IA e inyectado por Jinja2.

### 5.4 Variables disponibles en plantillas

Cada plantilla recibe un contexto con:
- `brand` — colores, fuentes, ruta del logo
- `slide` — contenido específico del slide (título, body, número, imagen resuelta, ícono resuelto)
- `company` — nombre de la empresa
- `assets` — rutas resueltas a imágenes e íconos

### 5.5 Dimensiones

Formato cuadrado Instagram: **1080 × 1080 px**

---

## 6. CLI

### Comandos

```bash
# Generar carrusel
generate carousel "tema o descripción" --company nombre-empresa

# Listar empresas disponibles
generate companies

# Listar estilos disponibles
generate styles
```

### Flags opcionales
- `--company` — nombre de la carpeta en `companies/`. Si solo hay una empresa configurada, se usa por defecto.
- `--output` — directorio de salida personalizado (default: `output/`)

---

## 7. Output

Por cada ejecución se crea un directorio con:

```
output/{empresa}/{fecha}-{tema-slug}/
├── slides/
│   ├── 01_cover.svg
│   ├── 02_content.svg
│   ├── 03_content.svg
│   ├── 04_stat.svg
│   └── 05_cta.svg
├── carousel.pdf          # PDF multipágina: un artboard por slide
└── summary.json
```

**SVGs individuales:** útiles para editar un slide específico en Illustrator sin abrir todo el carrusel.

**PDF multipágina (`carousel.pdf`):** archivo principal de trabajo. Illustrator lo abre con cada slide en su propio artboard. Canva lo importa como presentación multipágina. Permite revisar y editar el carrusel completo en un solo archivo.

`summary.json` contiene la decisión completa de la IA (útil para regenerar o auditar).

**Manejo de imágenes:** Las plantillas que incluyen área de imagen tienen un tag `<image>` con dimensiones y posición ya definidas por el diseño. El renderer busca en `assets/images/` el archivo cuyo nombre tenga mayor similitud con el `image_hint` de la IA (comparación de substring, case-insensitive). Si encuentra un match, inserta la imagen. Si no encuentra nada, muestra el área con el texto del `image_hint` como indicación visual para el editor.

**Manejo de íconos:** Mismo mecanismo — el renderer busca en `assets/icons/` por nombre coincidente con `icon_hint`. Si no hay match, muestra un rectángulo con el hint.

---

## 8. Manejo de Errores

| Situación | Comportamiento |
|-----------|----------------|
| `brand.yaml` incompleto | Error claro indicando el campo faltante |
| Logo o assets no encontrados | Error con la ruta esperada |
| Ollama no está corriendo | Mensaje indicando cómo iniciar Ollama |
| Respuesta IA no es JSON válido | Reintento automático (máx. 2). Si falla, error con respuesta cruda |
| Tipo de slide desconocido en respuesta IA | Se omite el slide y se advierte al usuario |

---

## 9. Dependencias Python

```
typer          # CLI
jinja2         # Renderizado de plantillas SVG
pyyaml         # Lectura de brand.yaml
ollama         # Cliente Ollama (python-ollama)
rich           # Output de terminal legible
cairosvg       # Conversión SVG → PDF para el archivo combinado
```

---

## 10. Expansión Futura

Para agregar un nuevo formato (poster, historia):
1. Crear `formats/poster/layouts/{estilo}/` con las nuevas plantillas SVG
2. Crear `formats/poster/prompts/poster.txt` con el prompt específico
3. Agregar el comando `generate poster` en `cli.py`

No se modifica el core (`ai.py`, `config.py`, `renderer.py`).
