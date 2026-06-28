# Resume Skill Gap Analyzer

A containerized full-stack application with frontend, backend, and AI model integration that analyzes resumes to identify skill gaps.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Setup

1. Clone the repository.
2. Create a `.env` file in the root directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

1. Start the application:

```bash
docker compose up --build
```

2. Open your browser and navigate to `http://localhost:8000`.
3. Upload a resume in **PDF format**.
4. Type `find skill gaps` in the chat to receive an AI-generated skill gap analysis.
   - Any other input will prompt the AI to respond based on your message.

---

## API Reference

### `POST /chat`

Sends a message and optional resume text to the AI backend.

**Request Payload**

```json
{
  "message": "string",
  "pdf_text": "string"
}
```

**Response**

```json
{
  "type": "string",
  "message": "string"
}
```

---

## Frontend Functions

| Function | Description |
|---|---|
| `SendMessage` | Sends a request to the backend `POST /chat` endpoint |
| `appendMessageToUI` | Appends a message to the chat UI by creating a new DOM element |

---

## Data & Assumptions

- Resumes must be uploaded in **PDF format**.

---

## Limitations

- The AI chatbot does **not** retain memory between messages — each conversation turn is stateless.

---

## Architecture

This project uses a **microservices architecture**, enabling independent deployment and scaling of each service.

### Future Improvements

- Add conversational memory to the chatbot to improve multi-turn dialogue quality.

