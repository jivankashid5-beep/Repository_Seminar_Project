// Add, remove, number, and total the bill rows on the entry form.
const billRows = document.querySelector("#bill-rows");
const addRowButton = document.querySelector("#add-row");
const totalDisplay = document.querySelector("#total-display");
const amountInWordsDisplay = document.querySelector("#amount-in-words");

// Words for numbers below one hundred.
const smallNumberWords = [
	"Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
	"Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
	"Seventeen", "Eighteen", "Nineteen"
];
const tensWords = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"];

function underOneThousandWords(number) {
	const words = [];
	if (number >= 100) {
		words.push(`${smallNumberWords[Math.floor(number / 100)]} Hundred`);
		number %= 100;
	}
	if (number >= 20) {
		const tens = tensWords[Math.floor(number / 10)];
		const ones = number % 10;
		words.push(ones ? `${tens} ${smallNumberWords[ones]}` : tens);
	} else if (number > 0) {
		words.push(smallNumberWords[number]);
	}
	return words.join(" ");
}

function integerInWords(number) {
	if (number === 0) return "Zero";

	const groups = [
		[10000000, "Crore"],
		[100000, "Lakh"],
		[1000, "Thousand"]
	];
	const words = [];

	groups.forEach(([size, label]) => {
		if (number >= size) {
			const groupValue = Math.floor(number / size);
			words.push(`${underOneThousandWords(groupValue)} ${label}`);
			number %= size;
		}
	});

	if (number > 0) words.push(underOneThousandWords(number));
	return words.join(" ");
}

function amountInWords(amount) {
	const fixedAmount = Math.abs(amount).toFixed(2);
	const [wholePart, decimalPart] = fixedAmount.split(".");
	let words = integerInWords(Number(wholePart));

	// Match num2words' spoken decimal style, e.g. "point five".
	const spokenDecimals = decimalPart.replace(/0+$/, "");
	if (spokenDecimals) {
		const digitWords = [...spokenDecimals].map((digit) => smallNumberWords[Number(digit)]);
		words += ` Point ${digitWords.join(" ")}`;
	}

	if (amount < 0) words = `Minus ${words}`;
	return `${words} Only`;
}

function updateRowNumbers() {
	billRows.querySelectorAll(".row-number").forEach((cell, index) => {
		cell.textContent = index + 1;
	});
}

function updateTotals() {
	const total = [...billRows.querySelectorAll(".row-amount")].reduce((sum, input) => {
		const amount = Number.parseFloat(input.value);
		return sum + (Number.isFinite(amount) ? amount : 0);
	}, 0);

	totalDisplay.textContent = total.toLocaleString("en-IN", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	amountInWordsDisplay.textContent = amountInWords(total);
	updateRowNumbers();
}

function addRow() {
	const row = document.createElement("tr");
	row.className = "bill-row";
	const rowNumber = billRows.querySelectorAll("tr").length + 1;
	row.innerHTML = `
		<td class="row-number"></td>
		<td><span class="voice-input"><input id="row-description-${rowNumber}" class="row-description" type="text" name="descriptions[]" placeholder="Description"><button class="field-mic" type="button" data-voice-target="row-description" aria-label="Speak description" title="Speak description">🎙</button></span></td>
		<td><span class="voice-input"><input id="row-amount-${rowNumber}" class="row-amount" type="number" name="amounts[]" min="0" step="0.01" placeholder="0.00"><button class="field-mic" type="button" data-voice-target="row-amount" aria-label="Speak amount" title="Speak amount">🎙</button></span></td>
		<td><button class="remove-row" type="button" aria-label="Remove this row">Remove row</button></td>
	`;
	billRows.appendChild(row);
	row.querySelector(".row-amount").addEventListener("input", updateTotals);
	updateTotals();
}

if (billRows && addRowButton) {
	billRows.querySelectorAll(".row-amount").forEach((input) => {
		input.addEventListener("input", updateTotals);
	});

	billRows.addEventListener("click", (event) => {
		const removeButton = event.target.closest(".remove-row");
		if (removeButton) {
			removeButton.closest("tr").remove();
			updateTotals();
		}
	});

	addRowButton.addEventListener("click", addRow);
	updateTotals();
}

// Browser speech recognition is available in Chrome and some other browsers.
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const mainMicButton = document.querySelector("#main-mic");
const languageSelect = document.querySelector("#voice-language");
const transcriptInput = document.querySelector("#voice-transcript");
const applyTranscriptButton = document.querySelector("#apply-transcript");
const voiceStatus = document.querySelector("#voice-status");
let activeRecognition = null;

function setVoiceStatus(message, isError = false) {
	if (!voiceStatus) return;
	voiceStatus.textContent = message;
	voiceStatus.classList.toggle("is-error", isError);
}

function startVoiceRecognition(target, button) {
	if (!SpeechRecognition) {
		setVoiceStatus("Voice input is not supported in this browser. Try the latest Google Chrome.", true);
		return;
	}
	if (activeRecognition) {
		setVoiceStatus("Finish the current voice input before starting another.", true);
		return;
	}

	const recognition = new SpeechRecognition();
	activeRecognition = recognition;
	recognition.lang = languageSelect.value;
	recognition.continuous = false;
	recognition.interimResults = false;
	recognition.maxAlternatives = 1;
	if (button) button.classList.add("is-listening");
	setVoiceStatus(`Listening in ${recognition.lang}… Speak now.`);

	recognition.onresult = (event) => {
		const recognizedText = event.results[0][0].transcript.trim();
		if (!recognizedText) {
			setVoiceStatus("No speech was recognized. Check your microphone and try again.", true);
			return;
		}
		transcriptInput.value = recognizedText;
		transcriptInput.dataset.target = target || "";

		if (target) {
			applyVoiceTextToField(target, recognizedText)
				.then(() => setVoiceStatus(`Recognized: “${recognizedText}”`))
				.catch((error) => setVoiceStatus(error.message, true));
		} else {
			applyBillLine(recognizedText)
				.then(() => setVoiceStatus(`Filled the bill fields from: “${recognizedText}”. You can edit the transcript and apply it again.`))
				.catch((error) => setVoiceStatus(error.message, true));
		}
	};

	recognition.onerror = (event) => {
		const messages = {
			"no-speech": "No speech was recognized. Speak clearly and try again.",
			"not-allowed": "Microphone access is blocked. Allow it in Chrome site settings.",
			"service-not-allowed": "Speech recognition is blocked by the browser or network.",
			"audio-capture": "No microphone was found. Connect or enable a microphone.",
			"network": "Speech recognition needs a working internet connection in Chrome.",
			"aborted": "Voice input was cancelled. Try again when ready."
		};
		setVoiceStatus(messages[event.error] || `Voice recognition failed: ${event.error}.`, true);
	};

	recognition.onend = () => {
		if (button) button.classList.remove("is-listening");
		activeRecognition = null;
	};

	try {
		recognition.start();
	} catch (error) {
		activeRecognition = null;
		if (button) button.classList.remove("is-listening");
		setVoiceStatus(`Could not start the microphone: ${error.message}`, true);
	}
}

async function convertSpokenNumber(text) {
	const response = await fetch("/api/words-to-number", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ text })
	});
	const result = await response.json();
	if (!response.ok) throw new Error(result.error || "Could not understand that number.");
	return result.number;
}

function findTargetInput(target, button = null) {
	const inputById = document.getElementById(target);
	if (inputById) return inputById;
	if (target === "row-description" || target === "row-amount") {
		const row = button?.closest("tr");
		return row?.querySelector(target === "row-description" ? ".row-description" : ".row-amount") || null;
	}
	return document.getElementById(target);
}

function setInputValue(input, value) {
	if (!input) throw new Error("The field for this voice input could not be found.");
	input.value = value;
	input.dispatchEvent(new Event("input", { bubbles: true }));
	input.dispatchEvent(new Event("change", { bubbles: true }));
}

async function normalizeSpokenDate(text) {
	let parsed = new Date(text);
	if (Number.isNaN(parsed.getTime())) {
		const monthNames = [
			["january", "जनवरी"], ["february", "फ़रवरी", "फरवरी"], ["march", "मार्च"],
			["april", "अप्रैल"], ["may", "मई"], ["june", "जून"], ["july", "जुलाई"],
			["august", "अगस्त"], ["september", "सितंबर", "सितम्बर"],
			["october", "अक्टूबर"], ["november", "नवंबर", "नवम्बर"],
			["december", "दिसंबर", "दिसम्बर"]
		];
		const lowerText = text.toLocaleLowerCase();
		let foundMonth = null;
		let monthPosition = -1;
		monthNames.some((names, index) => {
			const name = names.find((candidate) => lowerText.includes(candidate.toLocaleLowerCase()));
			if (!name) return false;
			foundMonth = index + 1;
			monthPosition = lowerText.indexOf(name.toLocaleLowerCase());
			return true;
		});

		if (foundMonth) {
			const monthName = monthNames[foundMonth - 1].find((name) =>
				lowerText.includes(name.toLocaleLowerCase())
			);
			const dayText = text.slice(0, monthPosition).replace(/\b(of|the)\b/gi, " ").trim();
			const yearText = text.slice(monthPosition + monthName.length).replace(/\b(of|the)\b/gi, " ").trim();
			try {
				const day = await convertSpokenNumber(dayText);
				const year = await convertSpokenNumber(yearText);
				parsed = new Date(year, foundMonth - 1, day);
				if (parsed.getFullYear() !== year || parsed.getMonth() !== foundMonth - 1 || parsed.getDate() !== day) {
					throw new Error("That date is not valid.");
				}
			} catch (error) {
				throw new Error("I heard the date, but could not format it. Say a date like ‘October 5 2026’ or ‘पांच अक्टूबर दो हजार छब्बीस’.");
			}
		} else {
			throw new Error("I heard the date, but could not format it. Say a date like ‘October 5 2026’ or ‘पांच अक्टूबर दो हजार छब्बीस’.");
		}
	}
	const localYear = parsed.getFullYear();
	const localMonth = String(parsed.getMonth() + 1).padStart(2, "0");
	const localDay = String(parsed.getDate()).padStart(2, "0");
	return `${localYear}-${localMonth}-${localDay}`;
}

async function applyVoiceTextToField(target, text, button = null) {
	const input = findTargetInput(target, button);
	if (!input) throw new Error("The field for this voice input could not be found.");

	if (input.type === "number") {
		const number = await convertSpokenNumber(text);
		setInputValue(input, number);
		if (input.classList.contains("row-amount")) updateTotals();
		return;
	}
	if (input.type === "date") {
		setInputValue(input, await normalizeSpokenDate(text));
		return;
	}
	setInputValue(input, text);
}

async function applyBillLine(text) {
	const parts = text.split(",").map((part) => part.trim()).filter(Boolean);
	if (parts.length < 3) {
		throw new Error("Please say the customer, description, and amount separated by commas, for example: Dhoot Transmission, Yazaki to Dhoot, 2200.");
	}

	const [customer, description, ...amountParts] = parts;
	// Join any grouping commas in a spoken amount, e.g. "2,200".
	const amountText = amountParts.join("");
	const amount = await convertSpokenNumber(amountText);
	const customerInput = document.querySelector("#customer-name");
	let descriptionInput = [...document.querySelectorAll(".row-description")].find((input) => !input.value.trim());
	let amountInput = descriptionInput?.closest("tr")?.querySelector(".row-amount");
	if (!descriptionInput) {
		addRow();
		descriptionInput = billRows.querySelector("tr:last-child .row-description");
		amountInput = billRows.querySelector("tr:last-child .row-amount");
	}
	setInputValue(customerInput, customer);
	setInputValue(descriptionInput, description);
	setInputValue(amountInput, amount);
	updateTotals();
}

if (mainMicButton && languageSelect && transcriptInput && applyTranscriptButton && voiceStatus) {
	if (!SpeechRecognition) {
		setVoiceStatus("Voice input is not supported here. Use the latest Google Chrome and allow microphone access.", true);
		mainMicButton.disabled = true;
		document.querySelectorAll(".field-mic").forEach((button) => { button.disabled = true; });
	}

	mainMicButton.addEventListener("click", () => startVoiceRecognition(null, mainMicButton));
	document.addEventListener("click", (event) => {
		const micButton = event.target.closest(".field-mic");
		if (!micButton) return;
		const target = micButton.closest(".voice-input")?.querySelector("input")?.id || micButton.dataset.voiceTarget;
		startVoiceRecognition(target, micButton);
	});

	applyTranscriptButton.addEventListener("click", () => {
		const text = transcriptInput.value.trim();
		if (!text) {
			setVoiceStatus("There is no recognized text to apply yet.", true);
			return;
		}
		const target = transcriptInput.dataset.target;
		const operation = target
			? applyVoiceTextToField(target, text)
			: applyBillLine(text);
		operation
			.then(() => setVoiceStatus(target ? `Applied to the selected field: “${text}”.` : `Applied the edited line: “${text}”.`))
			.catch((error) => setVoiceStatus(error.message, true));
	});
}

// Switch the preview between its designed page and values-only positions.
const printModeSelect = document.querySelector("#print-mode");
const billPrintSheet = document.querySelector("#bill-print-sheet");
const preprintedValues = document.querySelector(".preprinted-values");

if (printModeSelect && billPrintSheet && preprintedValues) {
	printModeSelect.addEventListener("change", () => {
		const selectedMode = printModeSelect.value;
		document.body.classList.toggle("print-mode-full", selectedMode === "full");
		document.body.classList.toggle("print-mode-values", selectedMode === "values");
		billPrintSheet.dataset.printMode = selectedMode;
		preprintedValues.setAttribute("aria-hidden", String(selectedMode !== "values"));
	});
}
