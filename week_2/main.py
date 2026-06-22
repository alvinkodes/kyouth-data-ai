from prompt_model import prompt_model
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python main.py <model> <prompt>")
        sys.exit(1)
    
    model = sys.argv[1]
    prompt = sys.argv[2]
    response = prompt_model(model, prompt)
    print(response)


if __name__ == "__main__":
    main()
