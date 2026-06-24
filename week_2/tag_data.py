from plistlib import load
import sqlite3
import json
import time
import sys
from prompt_model import prompt_model
from dotenv import load_dotenv

MAX_RETRIES = 5
BATCH_SIZE = 40
DB_URL = "data/3_gold/jobs.db"

def backoff_sleep(attempt: int) -> None:
	base = 2 ** attempt
	time.sleep(min(10, base))

def build_batch_prompt(batch: list[dict]) -> str:
	prompt = """
	You are a technical recruiter assistant specializing in extracting technology requirements from job descriptions.
	Your task is to analyze a batch of job descriptions and extract ONLY the tech stack. Return a JSON array where each element contains the source_id and tech_stack.
	
	RULES:
	- Output a valid JSON array ONLY — no explanations, markdown, or extra text in the response
	- Each object must have exactly two fields: "source_id" and "tech_stack"
	- "tech_stack" must be a comma-separated string, must not be an array
	- List only specific, nameable technologies — omit vague category words like 
	  "databases", "APIs", "Cloud", "NoSQL", "AI", "Big Data", "microservices"
	- If a specific tool is named, keep it (e.g. PostgreSQL, MongoDB, AWS, Docker)
	- Do NOT include soft skills, methodologies (Agile, Scrum), or certifications
	- Normalize all names to these canonical forms — always use exactly these strings:
	    Vue.js (not Vue, VueJS)
	    React (not ReactJS)
	    Go (not Golang)
	    Angular (not AngularJS)
	    Node.js (not NodeJS, Node)
	    Next.js (not NextJS)
	    scikit-learn (not sklearn)
	    JavaScript (not JS)
	    TypeScript (not TS)
	    .NET (not dotnet)
	    C# (not c-sharp)
	    GitHub Actions (not Github Actions)
	    GitLab CI (not Gitlab CI)
	- If a technology appears under multiple names in the same JD, list it once
	- If there is no tech stack, return a placeholder string "N/A"
	- Do NOT infer or assume technologies not explicitly mentioned in the JD
	
	---
	
	EXAMPLES:
	
	Input:
	[
	  {
	    "source_id": "JD001",
	    "description": "We are looking for a Senior Developer with strong Java and Spring Boot experience. The candidate must have worked with SAP ERP and SAP BW for enterprise reporting. Experience with REST APIs and GraphQL is required. Database knowledge in Oracle and PostgreSQL is essential. Familiarity with Kafka for event streaming is a plus."
	  },
	  {
	    "source_id": "JD002",
	    "description": "The role requires ABAP development skills for SAP S/4HANA customization. The developer will build RFC and BAPI integrations and work with SAP Fiori for UI development. Strong SQL skills are needed, and exposure to Python scripting is advantageous."
	  },
	  {
	    "source_id": "JD003",
	    "description": "Looking for a full-stack engineer proficient in JS, ReactJS, and Node. Must have experience integrating third-party APIs and working with MongoDB and Redis. Cloud experience on AWS (Lambda, S3, RDS) is required."
	  },
	  {
	    "source_id": "JD004",
	    "description": "Seeking a developer skilled in Vue, AngularJS, and NextJS. Knowledge of Golang and sklearn for backend/ML services is highly preferred. CI/CD experience with Github Actions or Gitlab CI is needed."
	  },
	  {
	    "source_id": "JD005",
	    "description": "Backend engineer needed for a modern legacy migration. Must be experts in c-sharp and the dotnet ecosystem. Strong TS frontend skills are a major bonus."
	  }
	]
	
	Output:
	[
	  {"source_id": "JD001", "tech_stack": "Java, Spring Boot, SAP ERP, SAP BW, GraphQL, Oracle, PostgreSQL, Kafka"},
	  {"source_id": "JD002", "tech_stack": "ABAP, SAP S/4HANA, SAP Fiori, SQL, Python"},
	  {"source_id": "JD003", "tech_stack": "JavaScript, React, Node.js, MongoDB, Redis, AWS"},
	  {"source_id": "JD004", "tech_stack": "Vue.js, Angular, Next.js, Go, scikit-learn, GitHub Actions, GitLab CI"},
	  {"source_id": "JD005", "tech_stack": "C#, .NET, TypeScript"}
	]
	
	---
	
	Now analyze the following job descriptions and return the JSON array:
	"""

	return prompt + json.dumps(batch, indent=2)


def run_batch(rows: list[dict]) -> list[dict]:
	batch = [{"source_id": row[0], "description": row[1]} for row in rows]
	prompt = build_batch_prompt(batch)

	for attempt in range(MAX_RETRIES):
		try:
			response = prompt_model("gemini-3.1-flash-lite", prompt)
			return json.loads(response)
		except json.JSONDecodeError:
			prompt = f"""
				Fix the output into valid JSON array only: {response}
			"""
			backoff_sleep(attempt)
		except Exception as e:
			print(f"Attempt {attempt} failed: {e}")
			backoff_sleep(attempt)
	
	print(f"Failed to process batch after {MAX_RETRIES} attempts")
	sys.exit(1)

def tag_data(db_url: str):
	conn = sqlite3.connect(db_url)
	cursor = conn.cursor()

	while True:
		rows = cursor.execute("""
			SELECT source_id, description FROM job WHERE tech_stack IS NULL LIMIT ?
		""", (BATCH_SIZE,)).fetchall()
		if not rows:
			print("No data to tag")
			break
		data = run_batch(rows)
		cursor.executemany("UPDATE job SET tech_stack = :tech_stack WHERE source_id = :source_id", data)
		conn.commit()

		for d in data:
			print(f"Analyzed Job {d['source_id']}: {d['tech_stack']}")

	conn.close()


if __name__ == "__main__":
	load_dotenv()
	tag_data(DB_URL)
