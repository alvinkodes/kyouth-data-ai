import sqlite3


def run_data_profile(db_path):
	if not db_path.exists():
		print(f"Database not found at {db_path}")
		return
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()

	query = """
		SELECT COUNT(*) AS total_records,
			SUM(CASE WHEN job_title IS NULL THEN 1 ELSE 0 END) AS null_titles,
			SUM(CASE WHEN company IS NULL THEN 1 ELSE 0 END) AS null_companies,
			SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END) AS null_descriptions,
			CAST(AVG(LENGTH(description)) AS INTEGER) AS avg_desc
		FROM job;
	"""
	cursor.execute(query)
	res = cursor.fetchone()

	min_query = """
		SELECT source_id, job_title, LENGTH(description) AS desc_length
		FROM job
		ORDER BY desc_length ASC
		LIMIT 1;
	"""
	cursor.execute(min_query)
	min_res = cursor.fetchone()

	max_query = """
		SELECT source_id, job_title, LENGTH(description) AS desc_length
		FROM job
		ORDER BY desc_length DESC
		LIMIT 1;
	"""
	cursor.execute(max_query)
	max_res = cursor.fetchone()

	print("--- DATA QUALITY REPORT ---")
	print(f"Total Records: {res['total_records']}")
	print(f"Missing Values -> job_title: {res['null_titles']}, company: {res['null_companies']}, description: {res['null_descriptions']}")
	print(f"Avg Description Length: {res['avg_desc']} chars")
	print(f"Shortest Description: {min_res['desc_length']} chars\n  source_id: {min_res['source_id']} | job_title: {min_res['job_title']}")
	print(f"Longest Description: {max_res['desc_length']} chars\n  source_id: {max_res['source_id']} | job_title: {max_res['job_title']}")

	conn.close()