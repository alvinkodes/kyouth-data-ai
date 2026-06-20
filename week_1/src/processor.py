from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError


class JobListing(BaseModel):
    source_id: str = Field(min_length=1)
    job_title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    description: str = Field(min_length=1)

counts = {
    "Total": 0,
    "Processed": 0
}

def process_html(infile, outfile):
    counts["Total"] += 1    
    with open(infile, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    f.close()

    try:
        source_id = soup.select_one('[property="og:url"]')
        source_id = source_id.get("content").rsplit('/', 1)[-1] if source_id else None
        job_title = soup.select_one('[data-automation="job-detail-title"]')
        job_title = job_title.get_text(separator=" ", strip=True) if job_title else None
        company = soup.select_one('[data-automation="advertiser-name"]')
        company = company.get_text(separator=" ", strip=True) if company else None
        description = soup.select_one('[data-automation="jobAdDetails"]')
        description = description.get_text(separator=" ", strip=True) if description else None

        job_listing = JobListing(
            source_id=source_id,
            job_title=job_title,
            company=company,
            description=description
        )

        with open(outfile, "w") as f:
            f.write(job_listing.model_dump_json(indent=2))

        print(f"Processed: {infile.name}")

        counts["Processed"] += 1
        f.close()

    except ValidationError as e:
        column_name = e.errors()[0]['loc'][0]
        print(f"Missing {column_name} in: {infile.name}")

def process_all_html(input_dir, output_dir):
    print("Silver:...")
    if not input_dir.exists():
        print(f"Input directory {input_dir} does not exist.")
        return
    if not output_dir.exists():
        output_dir.mkdir()
    for infile in input_dir.iterdir():
        outfile = output_dir / (infile.stem + ".json")
        process_html(infile, outfile)

    print()
    print("Silver Summary:")
    print(f"Total: {counts['Total']} | Processed: {counts['Processed']} | Skipped: {counts['Total'] - counts['Processed']}")