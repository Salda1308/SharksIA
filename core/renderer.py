import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
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


def _generate_pdf(svg_paths: list, output_path: Path) -> None:
    import cairosvg  # lazy import — requires native cairo library at runtime
    writer = PdfWriter()
    for svg_path in svg_paths:
        pdf_bytes = cairosvg.svg2pdf(url=str(svg_path))
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer.add_page(reader.pages[0])
    with open(output_path, "wb") as f:
        writer.write(f)


def wrap_text(text: str, chars_per_line: int) -> list:
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
    hint_words = hint_lower.split()
    for asset in sorted(assets_dir.iterdir()):
        name_lower = asset.stem.lower()
        if hint_lower in name_lower or any(w in name_lower for w in hint_words):
            return str(asset)
    return None
