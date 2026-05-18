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
