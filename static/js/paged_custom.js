this.ready = new Promise(function ($) {
	document.addEventListener("DOMContentLoaded", $, { once: true });
});


class MM_Handler extends Paged.Handler {
	t0 = 0; t1 = 0;
	constructor(chunker, polisher, caller) {
		super(chunker, polisher, caller);
		this.chunker = chunker;
		this.polisher = polisher;
		this.caller = caller;
	}

	afterPreview(pages) {
		this.t0 = performance.now();
	}
}


class EasyReading extends Paged.Handler {
	constructor(chunker, polisher, caller) {
		super(chunker, polisher, caller);
		this.chunker = chunker;
		this.polisher = polisher;
		this.caller = caller;
	}

	beforeParsed(content) {
		// modified from: https://stackoverflow.com/questions/49403285/splitting-word-into-syllables-in-javascript
		const syllableRegex = /[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?/gi;

		function syllabify(word) {
			const result = word.match(syllableRegex);
			return result ? result : [word];
		}

		function splitWords(text) {
			// Split text into words while ignoring HTML tags
			const regex = /(<[^>]+>)|\s+/g;
			return text.split(regex).filter(word => word !== undefined && word !== "");
		}

		function processParagraph(paragraph) {
			// Get text content of paragraph
			const text = paragraph.innerHTML;
			// Split text into words while ignoring HTML tags
			const words = splitWords(text);
			// Process words and replace paragraph content
			const processedWords = words.map(speedRead);
			paragraph.innerHTML = processedWords.join(" ");
		}

		const output = content.querySelector(".mw-parser-output");
		output.querySelectorAll("p").forEach(processParagraph);

		function speedRead(word) {
			// if the word starts with "<" it's an HTML tag. skip it.
			if (word.startsWith("<")) return word;

			let syllables = syllabify(word);
			// console.log(syllables);
			if (syllables.length > 1) {
				const firstSyllable = syllables[0];
				const restOfWord = syllables.slice(1).join("");
				return `<b>${firstSyllable}</b>${restOfWord}`;
			} else {
				const syllable = syllables[0];
				const halfIndex = Math.floor(syllable.length / 2);
				const firstHalf = syllable.slice(0, halfIndex);
				const secondHalf = syllable.slice(halfIndex);
				return `<b>${firstHalf}</b>${secondHalf}`;
			}
		}
	}
}

ready.then(async function () {

	let flowText = document.querySelector("#source");

	let t0 = performance.now();

	Paged.registerHandlers(MM_Handler);
	Paged.registerHandlers(EasyReading);

	let paged = new Paged.Previewer();

	paged.preview(flowText.content).then((flow) => {
		let t1 = performance.now();
		console.log("Rendering Pagedjs " + flow.total + " pages took " + (t1 - t0) + " milliseconds.");
	});


	let resizer = () => {
		let pages = document.querySelector(".pagedjs_pages");

		if (pages) {
			let scale = (window.innerWidth * 0.9) / pages.offsetWidth;
			if (scale < 1) {
				pages.style.transform = `scale(${scale}) translate(${window.innerWidth / 2 - (pages.offsetWidth * scale) / 2
					}px, 0)`;
			} else {
				pages.style.transform = "none";
			}
		}
	};
	resizer();

	window.addEventListener("resize", resizer, false);

	paged.on("rendering", () => {
		resizer();
	});
});