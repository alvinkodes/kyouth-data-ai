import email

counts = {
	"Total": 0,
	"Extracted": 0
}

def ingest_mhtml(in_file, out_file, counts):
	counts["Total"] += 1
	with open(in_file, 'br') as input_file:
		msg = email.message_from_binary_file(input_file)

	input_file.close()


	for part in msg.walk():
		if part.get_content_type() == "text/html":
			payload = part.get_payload(decode=True)
			break

	if payload is None:
		print(f"No HTML content found in {in_file}")
		return

	with open(out_file, 'wb') as output_file:
		output_file.write(payload)

	print(f"Extracted: {in_file.name}")
	counts["Extracted"] += 1
	output_file.close()


def ingest_all_mhtml(input_dir, output_dir):
	print("Bronze:...")
	if not input_dir.exists():
		print(f"Input directory {input_dir} does not exist.")
		return
	if not output_dir.exists():
		output_dir.mkdir()
	for in_file in input_dir.iterdir():
		out_file = output_dir / (in_file.stem + ".html")
		ingest_mhtml(in_file, out_file, counts)
	
	print()
	print("Bronze Summary:")
	print(f"Total: {counts['Total']} | Extracted: {counts['Extracted']} | Failed: {counts['Total'] - counts['Extracted']}")
