from google import genai
from dotenv import load_dotenv
import sys

def prompt_model(model: str, prompt: str) -> str:
    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    return response.text

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <model> <prompt>")
        sys.exit(1)

    load_dotenv()
    model = sys.argv[1]
    prompt = sys.argv[2]
    response = prompt_model(model, prompt)
    print(response)


if __name__ == "__main__":
    main()