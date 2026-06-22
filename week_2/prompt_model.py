from google import genai
from dotenv import load_dotenv

def prompt_model(model: str, prompt: str) -> str:
    load_dotenv()
    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text