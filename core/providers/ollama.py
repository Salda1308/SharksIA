import ollama as ollama_client


class OllamaProvider:
    def __init__(self, model: str):
        self.model = model

    def complete(self, prompt: str) -> str:
        try:
            response = ollama_client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                format="json",
            )
            return response["message"]["content"]
        except Exception as e:
            raise ConnectionError(
                f"No se pudo conectar con Ollama. ¿Está corriendo? "
                f"Inicia con: ollama serve\nError: {e}"
            )
