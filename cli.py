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
