const form = document.getElementById("translate-form");
const input = document.getElementById("sentence-input");
const errorEl = document.getElementById("form-error");
const resultsContainer = document.getElementById("results");

function renderResults(data) {
  resultsContainer.classList.remove("results--placeholder");
  resultsContainer.innerHTML = "";

  data.results.forEach((result) => {
    const block = document.createElement("article");
    block.className = "result";

    const sentence = document.createElement("h3");
    sentence.className = "result__sentence";
    sentence.textContent = result.originalSentence;

    const gloss = document.createElement("p");
    gloss.className = "result__gloss";
    gloss.textContent = result.glossTokens.join(" ");

    const linkList = document.createElement("ul");
    linkList.className = "result__links";

    result.links.forEach((link, index) => {
      const item = document.createElement("li");
      const anchor = document.createElement("a");
      anchor.href = link;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.textContent = result.glossTokens[index] || link;
      item.appendChild(anchor);
      linkList.appendChild(item);
    });

    block.appendChild(sentence);
    block.appendChild(gloss);
    block.appendChild(linkList);
    resultsContainer.appendChild(block);
  });
}

function renderError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

async function handleSubmit(event) {
  event.preventDefault();
  const sentence = input.value.trim();

  if (!sentence) {
    renderError("Please enter a sentence to translate.");
    return;
  }

  errorEl.hidden = true;
  resultsContainer.innerHTML = '<p class="loading">Translating…</p>';

  try {
    const response = await fetch("/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sentences: [sentence] }),
    });

    const data = await response.json();

    if (!response.ok) {
      const message = data.error || "Translation failed. Please try again.";
      renderError(message);
      resultsContainer.innerHTML = "";
      return;
    }

    renderResults(data);
  } catch (error) {
    renderError("Network error. Please check your connection and try again.");
    resultsContainer.innerHTML = "";
  }
}

form.addEventListener("submit", handleSubmit);
