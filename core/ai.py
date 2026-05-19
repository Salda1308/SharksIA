import json
from pathlib import Path


SLIDE_TYPES = {"cover", "content", "content_icon", "stat", "cta"}


def generate_content(topic: str, brand_config: dict, formats_dir: Path, mode: str = "topic") -> dict:
    provider = _build_provider(brand_config)
    prompt = _build_prompt(topic, brand_config, formats_dir, mode)

    last_raw = ""
    for _ in range(3):
        last_raw = provider.complete(prompt)
        try:
            result = json.loads(last_raw)
            result["slides"] = _normalize_slides(result.get("slides", []))
            return result
        except json.JSONDecodeError:
            continue

    raise ValueError(
        f"La IA no devolvió JSON válido después de 3 intentos.\n"
        f"Última respuesta:\n{last_raw}"
    )


def _normalize_slides(slides: list) -> list:
    normalized = []
    for slide in slides:
        if "type" in slide:
            normalized.append(slide)
            continue
        # AI returned {"cover": {"title": ...}} — unwrap it
        for key in slide:
            if key in SLIDE_TYPES:
                flat = {"type": key}
                flat.update(slide[key] if isinstance(slide[key], dict) else {})
                normalized.append(flat)
                break
    return normalized


def _build_provider(brand_config: dict):
    provider_name = brand_config.get("ai_provider", "ollama")
    if provider_name == "ollama":
        from .providers.ollama import OllamaProvider
        return OllamaProvider(brand_config.get("ollama_model", "llama3.2"))
    raise ValueError(f"Proveedor de IA desconocido: '{provider_name}'")


def _build_prompt(topic: str, brand_config: dict, formats_dir: Path, mode: str = "topic") -> str:
    if mode == "text":
        prompt_file = "carousel_text.txt"
    else:
        prompt_file = "carousel_topic.txt" if (formats_dir / "carousel" / "prompts" / "carousel_topic.txt").exists() else "carousel.txt"
    prompt_path = formats_dir / "carousel" / "prompts" / prompt_file
    template = prompt_path.read_text(encoding="utf-8")
    return template.format(
        topic=topic,
        content=topic,
        design_context=brand_config["brand"].get("design_context", ""),
        style=brand_config["brand"]["style"],
    )
