import os
from week_2.find_skill_gaps import find_skill_gaps
from week_2.prompt_model import prompt_model
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path)

class ChatRequest(BaseModel):
	message: str
	pdf_text: str | None = None

app = FastAPI()

frontend_origin = os.getenv("FRONTEND_ORIGIN")

origins = [
	"http://localhost:8000"
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.post("/chat", response_class=JSONResponse)
async def chat(request: ChatRequest):
	if request.pdf_text and request.message == "find skill gaps":
		result = find_skill_gaps(request.pdf_text, "src/week_2/data/3_gold/jobs.db")
		json_compatible_result = jsonable_encoder(result)
		return JSONResponse(
			status_code=200,
			content={"type": "skill_gaps", "message": json_compatible_result["gaps"]}
		)
	else:
		message = request.message + " " + request.pdf_text if request.pdf_text else request.message
		response = prompt_model("gemini-3.1-flash-lite", message)
		return JSONResponse(
			status_code=200,
			content={"type": "chat", "message": response}
		)
