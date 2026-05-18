# Plataforma Web — Spec de Diseño (MVP Sub-proyecto #1)
**Fecha:** 2026-05-18
**Contexto:** Transformación del CLI de carruseles en una plataforma web SaaS

---

## 1. Visión General

Convertir el CLI de generación de carruseles en una aplicación web accesible desde el browser. El MVP cubre exclusivamente carruseles de Instagram. La arquitectura está diseñada para soportar múltiples usuarios y planes de suscripción desde el inicio, aunque en la primera versión local corre con un único usuario sin autenticación obligatoria.

Sub-proyectos fuera del MVP (para fases posteriores):
- Suscripciones y billing (Stripe)
- Formatos adicionales (historias, posters, banners, brochures, tarjetas)
- Editor visual drag-and-drop (tipo Canva)
- IA que aprende del estilo del usuario a partir de diseños subidos
- API pública para el plan Ultra

---

## 2. Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Backend API | FastAPI (Python) — puerto 8000 |
| Frontend | Next.js App Router (TypeScript) — puerto 3000 |
| Base de datos | SQLite local con SQLAlchemy ORM |
| IA | Ollama local (mismo proveedor del CLI actual) |
| Storage | Filesystem local → preparado para S3 en producción |
| Auth | JWT en cookie httpOnly; Google OAuth + email/password |

---

## 3. Estructura del Repositorio

```
GeneradorDiseños/
├── api/
│   ├── main.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── companies.py
│   │   ├── carousel.py
│   │   └── images.py
│   ├── models.py
│   └── storage.py
├── web/
│   ├── app/
│   │   ├── page.tsx                    ← landing
│   │   ├── auth/login/page.tsx
│   │   ├── auth/register/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── companies/new/page.tsx
│   │   ├── companies/[id]/page.tsx
│   │   ├── designs/page.tsx
│   │   ├── designs/new/carousel/page.tsx
│   │   ├── designs/[id]/edit/page.tsx
│   │   └── designs/[id]/export/page.tsx
│   └── components/
│       ├── SlidePreview.tsx
│       ├── SlideEditor.tsx
│       ├── ImagePicker.tsx
│       ├── CompanyForm.tsx
│       └── ExportPanel.tsx
├── core/                               ← sin cambios
├── formats/                            ← sin cambios
├── companies/                          ← legacy, migrado a DB
├── storage/
│   ├── uploads/                        ← imágenes subidas por usuarios
│   ├── tmp/                            ← renders temporales (se borran tras descarga)
│   └── db.sqlite3
├── .env                                ← nunca en git
└── Makefile
```

---

## 4. Modelo de Datos

### User
```
id            TEXT PRIMARY KEY
email         TEXT UNIQUE NOT NULL
name          TEXT
avatar_url    TEXT
auth_provider TEXT   -- "google" | "email"
password_hash TEXT   -- null si auth_provider = "google"
plan          TEXT   -- "basic" | "pro" | "ultra"
created_at    DATETIME
```

### Company
```
id             TEXT PRIMARY KEY
user_id        TEXT FK → User
name           TEXT NOT NULL
slug           TEXT UNIQUE
logo_path      TEXT
colors         JSON  -- { primary, secondary, background, text }
fonts          JSON  -- { heading, body }
style          TEXT  -- "minimal" | "bold" | "editorial" | "corporate"
design_context TEXT  -- tono, audiencia, descripción libre
ai_provider    TEXT  -- "ollama" | "openai" (para escalar después)
created_at     DATETIME
```

### Design
```
id          TEXT PRIMARY KEY
user_id     TEXT FK → User
company_id  TEXT FK → Company
type        TEXT      -- "carousel" (extensible a otros formatos)
title       TEXT
slides      JSON      -- output de la IA, editable por el usuario
size_px     JSON      -- { width, height }
status      TEXT      -- "draft" | "rendered" | "exported"
created_at  DATETIME
updated_at  DATETIME
```

### Asset
```
id           TEXT PRIMARY KEY
user_id      TEXT FK → User
filename     TEXT
path_thumb   TEXT   -- 300px, para preview en editor
path_full    TEXT   -- 1080px, para render final
source       TEXT   -- "upload" | "pexels" | "pixabay"
created_at   DATETIME
```

---

## 5. Rutas de la API

### Auth
```
POST   /api/v1/auth/register           -- email + password → JWT
POST   /api/v1/auth/login              -- email + password → JWT
GET    /api/v1/auth/google             -- redirect OAuth
GET    /api/v1/auth/google/callback    -- intercambia código → JWT
POST   /api/v1/auth/logout
GET    /api/v1/auth/me                 -- perfil del usuario autenticado
```

### Empresas
```
GET    /api/v1/companies               -- listar empresas del usuario
POST   /api/v1/companies               -- crear empresa
GET    /api/v1/companies/{id}
PUT    /api/v1/companies/{id}
DELETE /api/v1/companies/{id}
```

### Diseños
```
GET    /api/v1/designs                          -- listar diseños del usuario
POST   /api/v1/designs/carousel/generate        -- IA genera slides JSON → Design "draft"
GET    /api/v1/designs/{id}                     -- obtener diseño y slides
PUT    /api/v1/designs/{id}/slides              -- usuario edita slides
POST   /api/v1/designs/{id}/render              -- renderiza SVGs → status "rendered"
GET    /api/v1/designs/{id}/export?fmt=svg|pdf|jpg  -- genera archivo → descarga → borra tmp
DELETE /api/v1/designs/{id}
```

### Imágenes
```
POST   /api/v1/assets/upload                    -- sube imagen local (comprime al recibir)
GET    /api/v1/images/search?q=&source=pexels   -- búsqueda con caché
```

---

## 6. Flujo de Generación

```
1. Usuario configura: empresa, tamaño en px, tema o texto largo, estilo visual
2. POST /carousel/generate → core/ai.py → Ollama → JSON de slides → Design "draft"
3. Pantalla del editor: preview del slide actual + formulario de edición por slide
4. Usuario edita texto, cambia imágenes (Pexels, Pixabay, o sube propia)
5. PUT /slides → actualiza JSON en DB
6. POST /render → core/renderer.py genera SVGs en storage/tmp/{design_id}/
7. GET /export?fmt= → convierte a formato solicitado → descarga → borra tmp
```

Los pasos 3-6 pueden repetirse. El render se dispara con debounce desde el editor para preview en vivo.

---

## 7. Editor de Slides

Pantalla `/designs/{id}/edit` — la más importante del MVP.

```
┌─────────────────────────────────────────────────────┐
│  Preview (SVG del slide actual)  │  Panel edición   │
│                                  │  Slide 1: Cover  │
│  [← anterior]    [siguiente →]   │  Título: [    ]  │
│                                  │  Subtítulo: [ ]  │
│                                  │  [Imagen]        │
│                                  │  [Pexels][Subir] │
└─────────────────────────────────────────────────────┘
     [Regenerar con IA]                [Exportar →]
```

- Cada tipo de slide (`cover`, `content`, `content_icon`, `stat`, `cta`) tiene su propio formulario
- El ImagePicker abre un modal: búsqueda en Pexels/Pixabay o upload local
- "Regenerar con IA" llama de nuevo a `/generate` con el mismo contexto

---

## 8. Estrategia de Storage

### Principio: solo guardar lo que no se puede regenerar

| Dato | ¿Se guarda? | Forma |
|---|---|---|
| Slides JSON | Sí | DB (KB por diseño) |
| Imágenes subidas por usuario | Sí | Filesystem comprimido (thumb 300px + full 1080px) |
| Logo de empresa | Sí | Filesystem |
| SVGs renderizados | No | Generados on-demand, borrados tras descarga |
| PDFs | No | Generados on-demand, borrados tras descarga |
| Imágenes de Pexels/Pixabay | No | Solo URL/ID en el JSON del slide |

### Imágenes subidas
Al recibir upload: generar `thumb_300px` + `optimized_1080px`, borrar original.

### Renders temporales
Ciclo de vida: `POST /render` → archivos en `storage/tmp/{design_id}/` → usuario descarga → job de limpieza borra archivos mayores a 1 hora.

### Límites por plan (cuando se implemente billing)
| Plan | Empresas | Storage imágenes propias |
|---|---|---|
| Basic | 1 | 100 MB |
| Pro | 5 | 500 MB |
| Ultra | ilimitado | 5 GB |

---

## 9. Autenticación

### Google OAuth + Email/Password
```
Email/Password:
  - Registro: bcrypt hash en DB → JWT
  - Login: verifica hash → JWT

Google OAuth:
  - Redirect a Google → callback con código de autorización
  - Backend intercambia código por perfil (email, nombre, avatar)
  - Si email existe en DB: login; si no: crea User → login
  - Devuelve JWT igual que flujo email

JWT:
  - Almacenado en cookie httpOnly (no accesible desde JS)
  - Payload: { user_id, plan, exp }
  - En producción: 1h access token + refresh token
```

### Usuario local para desarrollo
Si no hay token, el sistema opera con `user_id = "local"`. Permite usar la app sin registro durante desarrollo. Cuando se implemente auth, este fallback se elimina.

---

## 10. Integración con el Código Existente

| Módulo | Cambio |
|---|---|
| `core/ai.py` | Sin cambios — la API lo importa directamente |
| `core/renderer.py` | Sin cambios |
| `core/config.py` | Sin cambios |
| `formats/` | Sin cambios |
| `companies/` | Queda como legacy; datos migran a tabla `Company` en DB |
| `cli.py` | Se mantiene funcional en paralelo |

La API importa `core/` directamente — no hay subprocess.

---

## 11. Variables de Entorno

```bash
# .env (nunca en git)
PEXELS_API_KEY=
PIXABAY_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
JWT_SECRET=
DATABASE_URL=sqlite:///./storage/db.sqlite3
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 12. Dev Setup

```bash
# Requiere: Python 3.11+, Node 18+, Ollama corriendo

make dev
# Arranca FastAPI en :8000 (uvicorn --reload)
# Arranca Next.js en :3000 (next dev)
# Crea storage/db.sqlite3 si no existe
```

---

## 13. Sub-proyectos Futuros (no en este MVP)

1. **Billing** — Stripe, planes Basic/Pro/Ultra, límites de empresas y storage
2. **Más formatos** — historias, posters, banners, brochures, tarjetas de presentación
3. **Fotos de stock mejoradas** — caché de búsquedas con Redis, rate limiting por usuario
4. **IA aprende del estilo** — usuario sube diseños de referencia, extrae paleta/composición, usa como contexto adicional
5. **API pública** — endpoints autenticados por API key para el plan Ultra
6. **Deploy en AWS** — EC2 + RDS (PostgreSQL) + S3 + mejor modelo de IA (Bedrock o similar)
