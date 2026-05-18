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
