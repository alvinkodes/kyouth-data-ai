import sqlite3
import json


counts = {
    "Total": 0,
    "Inserted": 0
}

def create_db(output_dir):
    conn = sqlite3.connect(output_dir / 'jobs.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT UNIQUE NOT NULL,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            description TEXT NOT NULL,
            tech_stack TEXT)''')
    
    conn.commit()
    conn.close()


def load_all_jsons(input_dir, output_dir):
    print("Gold:...")
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist.")
        return
    if not output_dir.exists():
        output_dir.mkdir()

    create_db(output_dir)

    conn = sqlite3.connect(output_dir / 'jobs.db')
    cursor = conn.cursor()

    for infile in input_dir.iterdir():
        counts["Total"] += 1
        with open(infile, 'r') as f:
            data = json.load(f)
        f.close()

        cursor.execute(
            """
                INSERT OR IGNORE INTO job (source_id, job_title, company, description)
                VALUES (?, ?, ?, ?)
            """,
                (data["source_id"], data["job_title"], data["company"], data["description"]))
        if cursor.rowcount == 0:
            print(f"Skipped (duplicate): {infile.name}")
            continue
        print(f"Inserted: {infile.name}")
        counts["Inserted"] += 1

    conn.commit()
    conn.close()

    print()
    print("Gold Summary:")
    print(f"Total: {counts['Total']} | Inserted: {counts['Inserted']} | Skipped: {counts['Total'] - counts['Inserted']}")
