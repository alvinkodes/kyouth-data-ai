from week_2.find_skill_gaps import find_skill_gaps
from week_2.prompt_model import prompt_model
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class ChatRequest(BaseModel):
	message: str
	pdf_text: str | None = None

BACKEND_URL = os.getenv("BACKEND_URL")

app = FastAPI()

app.mount("/static", StaticFiles(directory="../frontend/src/static"), name="static")
templates = Jinja2Templates(directory="../frontend/src/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
	return templates.TemplateResponse(
		request=request, name="index.html"
	)

@app.post("/chat", response_class=JSONResponse)
async def chat(request: ChatRequest):
	if request.pdf_text:
		result = find_skill_gaps(request.pdf_text, "src/week_2/data/3_gold/jobs.db")
		json_compatible_result = jsonable_encoder(result)
		return JSONResponse(
			status_code=200,
			content={"type": "skill_gaps", "message": json_compatible_result["gaps"]}
		)
	else:
		response = prompt_model("gemini-3.1-flash-lite", request.message)
		return JSONResponse(
			status_code=200,
			content={"type": "chat", "message": response}
		)
