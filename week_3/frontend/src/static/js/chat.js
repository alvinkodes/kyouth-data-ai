import * as pdfjsLib from 'https://mozilla.github.io/pdf.js/build/pdf.mjs';
pdfjsLib.GlobalWorkerOptions.workerSrc ='https://mozilla.github.io/pdf.js/build/pdf.worker.mjs';

let extractedPdfText = "";

async function extractText(typedArray) {
	try {
		const pdf = await pdfjsLib.getDocument({ data: typedArray }).promise;
		const pagePromises = [];
		for (let i = 1; i <= pdf.numPages; i++) {
			const page = await pdf.getPage(i);
			const textContent = await page.getTextContent();
			const text = textContent.items.map(s => s.str).join('');
			pagePromises.push(text);
		}
		return pagePromises.join(' ');
	} catch (error) {
		console.error("Error parsing PDF: " + error);
		throw error;
	}
}


const fileInput = document.getElementById('fileInput')

fileInput.addEventListener('change', async (e) => {
	const file = e.target.files[0];
	if (!file) return;

	if (file.type !== 'application/pdf') {
		alert('Only PDF files are supported');
		return;
	}

	const reader = new FileReader();
	reader.onload = async function() {
		const typedArray = new Uint8Array(this.result);
		try {
			extractedPdfText = await extractText(typedArray);
			console.log('parse ' + extractedPdfText);
		} catch (error) {
			console.error(error);
		}
	};
	reader.readAsArrayBuffer(file);
})


const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
const chatBody = document.getElementById('chatBody');

async function sendMessage() {
	const messageText = msgInput.value.trim();
	if (!messageText && !extractedPdfText) return;

	appendMessageToUI("User", messageText);
	msgInput.value = "";

	const payload = {
		message: messageText,
		pdf_text: extractedPdfText || null
	};

	try {
		const response = await fetch(BACKEND_URL, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});
		const data = await response.json();

		appendMessageToUI("Bot", data.response);
	} catch (error) {
		console.error("Error sending message:", error);
		appendMessageToUI("Server Error", "An error occurred while sending your message. Please try again later.")
	}
}


function appendMessageToUI(sender, message) {
	const msgDiv = document.createElement('div');
	msgDiv.className = sender === "User"
		? "bg-primary text-white p-2 rounded shadow-sm align-self-end"
		: "bg-white p-2 rounded shadow-sm align-self-start";
	msgDiv.textContent = `${sender}: ${message}`;
	chatBody.appendChild(msgDiv);
	chatBody.scrollTop = chatBody.scrollHeight;
}


sendBtn.addEventListener('click', sendMessage);
msgInput.addEventListener('keypress', (e) => {
	if (e.key === 'Enter') sendMessage();
});