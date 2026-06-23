from logging import PlaceHolder

from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompt_model import prompt_model
from pydantic import BaseModel
from typing import List
import sys
import sqlite3
import json
import numpy as np

class SkillGapResult(BaseModel):
	gaps: List[str]

class ResumeExtraction(BaseModel):
	job_role: str
	skills: List[str]


def embedding_job_titles():
	conn = sqlite3.connect("data/3_gold/jobs.db")
	cursor = conn.cursor()
	job_titles = cursor.execute("SELECT job_title FROM job").fetchall()

	client = genai.Client()

	embeddings = {}
	for title in job_titles:
		result = client.models.embed_content(
			model="gemini-embedding-2-preview",
			contents=[title[0]],
			config=types.EmbedContentConfig(output_dimensionality=768)
		)
		embeddings[title[0]] = result.embeddings[0].values
		print(f"Embedding: {title[0]}")
	with open("data.json", "w") as f:
		json.dump(embeddings, f)


def extract_resume_skills(resume_text: str, model: str) -> ResumeExtraction:
	SYSTEM_PROMPT = """
	You are a resume parser. Extract the candidate's
	current or target job role and technical skills from resumes.
	
	Rules:
	- role: the job title or role the candidate identifies as (e.g.
	"backend developer", "data scientist")
	- skills: only technical skills — programming languages, frameworks,
	tools, platforms. Exclude soft skills, languages (English), hobbies, or
	certifications.
	- Do not infer or change the role based on the technical skills section. If they
	write "Sales Engineer", the role is "Sales Engineer", regardless of their technical stack.
	Same thing applies to the skills section.
	- Normalize skill names to their canonical form. Examples: python →
	Python, MYSQL → MySQL, powershell → PowerShell
	- Return JSON only. No explanation.

	Examples:

	<resume>
	JANE DOE
	Data Engineer
	SKILLS
	Technical: React, TypeScript, CSS, Webpack
	Soft Skills: Communication
	</resume>
	{"role": "frontend engineer", "skills": ["React", "TypeScript", "CSS",
	"Webpack"]}

	<resume>
	JOHN SMITH
	SUMMARY
	5 years building data pipelines with Python and Spark.
	EXPERIENCE
	Data Engineer at Acme Corp
	- Built ETL pipelines using Apache Airflow and AWS S3
	SKILLS
	Python, SQL, Spark, Airflow, AWS
	</resume>
	{"role": "data engineer", "skills": ["Python", "SQL", "Spark", "Apache
	Airflow", "AWS"]}

	<resume>
	SAM LEE
	Full Stack Developer
	SKILLS
	NodeJS, ReactJS, MongoDB, Docker, Github Actions
	</resume>
	{"role": "full stack developer", "skills": ["Node.js", "React",
	"MongoDB", "Docker", "GitHub Actions"]}"""

	USER_PROMPT = """<resume>
	{resume_text}
	</resume>"""

	client = genai.Client()
	interaction = client.interactions.create(
		model=model,
		system_instruction=SYSTEM_PROMPT,
		input=USER_PROMPT.format(resume_text=resume_text),
		response_format={
			"type": "text",
			"mime_type": "application/json",
			"schema": ResumeExtraction.model_json_schema()
		},
	)
	try:
		output = ResumeExtraction.model_validate_json(interaction.output_text)
		#print(output)
	except Exception as e:
		print(f"Invalid JSON format: {e}")
		sys.exit(1)
	return output


def find_best_matches(resume_data: ResumeExtraction) -> List[dict]:
	client = genai.Client()
	result = client.models.embed_content(
		model="gemini-embedding-2-preview",
		contents=[resume_data.job_role],
		config=types.EmbedContentConfig(output_dimensionality=768)
	)
	role_vector = result.embeddings[0].values
	role_vector = np.array(role_vector)
	with open("data.json", "r") as f:
		embeddings = json.load(f)

	matches = []
	for title, vector in embeddings.items():
		vector = np.array(vector)
		score = np.dot(role_vector, vector) / (np.linalg.norm(role_vector) * np.linalg.norm(vector))
		if score >= 0.8:
			matches.append({"job_title": title, "score": round(score, 2)})
	matches.sort(key=lambda x: x["score"], reverse=True)
	return matches

def query_db(matches: List[dict]) -> List[dict]:
	conn = sqlite3.connect("data/3_gold/jobs.db")
	cursor = conn.cursor()

	target_roles = [match["job_title"] for match in matches]

	placeholder = ", ".join('?' for _ in target_roles)
	cursor.execute(f"SELECT tech_stack FROM job WHERE job_title IN ({placeholder})", target_roles)
	rows = cursor.fetchall()
	conn.close()
	rows = [row[0] for row in rows]
	return rows


def find_skill_gaps(input_file_dir: str, db_url: str) -> SkillGapResult:
	conn = sqlite3.connect(db_url)
	cursor = conn.cursor()

	conn.close()
	pass


if __name__ == "__main__":
	load_dotenv()
	#embedding_job_titles()
	with open("resources/resume_d3.txt", "r") as f:
		resume_text = f.read()
	resume_data = extract_resume_skills(resume_text, "gemini-3.1-flash-lite")
	#print(resume_data)
	matches = find_best_matches(resume_data)
	#print(matches)
	rows = query_db(matches)
	#print(res)
	required_skills = {word.strip() for text in rows for word in text.split(',')}
	resume_skill = set(resume_data.skills)
	gaps = sorted(required_skills - resume_skill)
	gaps = [text.lower() for text in gaps]
	print(gaps)