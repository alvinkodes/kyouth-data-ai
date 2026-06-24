import sys
import sqlite3
import json
import numpy as np
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List


OUTPUT_FILE = Path("data.json")
EMBEDDING_MODEL = "gemini-embedding-2-preview"
MODEL = "gemini-3.1-flash-lite"


class SkillGapResult(BaseModel):
	gaps: List[str]


class ResumeExtraction(BaseModel):
	job_role: str
	skills: List[str]


def embedding_job_titles(conn, client):
	cursor = conn.cursor()
	job_titles = cursor.execute("SELECT job_title FROM job").fetchall()

	embeddings = {}
	for title in job_titles:
		result = client.models.embed_content(
			model=EMBEDDING_MODEL,
			contents=[title[0]],
			config=types.EmbedContentConfig(output_dimensionality=768)
		)
		embeddings[title[0]] = result.embeddings[0].values
		print(f"Embedding: {title[0]}")
	with open(OUTPUT_FILE, "w") as f:
		json.dump(embeddings, f)


def extract_resume_skills(client, resume_text: str) -> ResumeExtraction:
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
	Frontend Engineer
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

	interaction = client.interactions.create(
		model=MODEL,
		system_instruction=SYSTEM_PROMPT,
		input=USER_PROMPT.format(resume_text=resume_text),
		response_format={
			"type": "text",
			"mime_type": "application/json",
			"schema": ResumeExtraction.model_json_schema()
		},
	)
	output = ResumeExtraction.model_validate_json(interaction.output_text)
	return output


def find_best_matches(client, resume_data: ResumeExtraction) -> List[dict]:
	result = client.models.embed_content(
		model=EMBEDDING_MODEL,
		contents=[resume_data.job_role],
		config=types.EmbedContentConfig(output_dimensionality=768)
	)
	role_vec = result.embeddings[0].values
	role_vec = np.array(role_vec)
	with open(OUTPUT_FILE, "r") as f:
		embeddings = json.load(f)

	matches = []
	for title, vec in embeddings.items():
		vec = np.array(vec)
		score = np.dot(role_vec, vec) / (np.linalg.norm(role_vec) * np.linalg.norm(vec))
		if score >= 0.8:
			matches.append({"job_title": title, "score": round(score, 2)})
	return matches


def query_db(conn, matches: List[dict]) -> List[dict]:
	target_roles = [match["job_title"] for match in matches]
	placeholder = ", ".join('?' for _ in target_roles)

	cursor = conn.cursor()
	cursor.execute(f"SELECT tech_stack FROM job WHERE job_title IN ({placeholder}) AND tech_stack != 'N/A'", target_roles)
	rows = cursor.fetchall()

	rows = [row[0] for row in rows]
	return rows


def find_skill_gaps(input_file_dir: str, db_url: str) -> SkillGapResult:
	load_dotenv()
	conn = sqlite3.connect(db_url)
	client = genai.Client()

	if not OUTPUT_FILE.exists():
		embedding_job_titles(conn, client)

	with open(input_file_dir, "r") as f:
		resume_text = f.read()
	resume_data = extract_resume_skills(client, resume_text)
	matches = find_best_matches(client, resume_data)
	rows = query_db(conn, matches)

	required_skills = {word.strip() for text in rows for word in text.split(',')}
	resume_skill = set(resume_data.skills)
	gaps = sorted(required_skills - resume_skill)
	gaps = {"gaps": [text.lower() for text in gaps]}

	conn.close()
	return SkillGapResult(**gaps)


if __name__ == "__main__":
	try:
		gaps = find_skill_gaps("resources/resume_d3.txt", "data/3_gold/jobs.db")
		print(gaps)
	except Exception as e:
		print(f"Fatal error: {e}")
