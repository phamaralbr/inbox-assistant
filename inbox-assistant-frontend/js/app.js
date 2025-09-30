const fileInput = document.getElementById("file");
const filePill = document.getElementById("filePill");
const fileNameSpan = document.getElementById("fileName");
const removeFileBtn = document.getElementById("removeFile");
const textarea = document.getElementById("text");
const form = document.getElementById("emailForm");
const resultContainer = document.getElementById("resultContainer");
const infoMessage = document.getElementById("infoMessage");

// Auto-grow textarea
textarea.addEventListener("input", () => {
  textarea.style.height = "auto";
  textarea.style.height = textarea.scrollHeight + "px";
});

// Enter submits, Shift+Enter new line
textarea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

// Show file pill when a file is selected
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    const file = fileInput.files[0];
    fileNameSpan.textContent = file.name;
    filePill.classList.remove("hidden");
    textarea.classList.add("hidden");
  }
});

// Remove file pill
removeFileBtn.addEventListener("click", () => {
  fileInput.value = "";
  filePill.classList.add("hidden");
  textarea.classList.remove("hidden");
});

// Function to add chat messages
function addMessage(content, type = "user") {
  const div = document.createElement("div");

  content = content.replace(/\n/g, "<br>");

  if (type === "user") {
    // Bubble aligned to right, text stays left
    div.className = "flex justify-end";
    div.innerHTML = `
      <div class="inline-block bg-gray-700/50 text-white px-4 py-2 rounded-2xl max-w-[80%] text-left">
        ${content}
      </div>`;
  } else {
    // Bubble aligned left (default)
    div.className = "flex justify-start";
    div.innerHTML = `
      <div class="inline-block bg-gray-900 text-white px-4 py-2 rounded-2xl max-w-[80%] text-left">
        ${content}
      </div>`;
  }

  resultContainer.appendChild(div);
  resultContainer.scrollTop = resultContainer.scrollHeight;
}

// Handle form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Read values before clearing
  const textValue = textarea.value.trim();
  const file = fileInput.files[0];

  // If no text and no file, do nothing
  if (!textValue && !file) return;

  // Hide info message
  if (infoMessage) infoMessage.style.display = "none";

  // CLEAR INPUTS
  textarea.value = "";
  textarea.style.height = "auto"; // reset height
  fileInput.value = "";
  filePill.classList.add("hidden");
  textarea.classList.remove("hidden");

  if (textValue) addMessage(textValue, "user");
  if (file) addMessage(file.name, "user");

  addMessage("Processando...", "bot");

  try {
    const formData = new FormData();
    if (textValue) formData.append("text", textValue);
    if (file) formData.append("file", file);

    // Decide API base URL depending on environment
    const API_URL = window.location.hostname.includes("github.io")
      ? "https://inbox-assistant-mkt3.onrender.com" // deployed backend
      : "http://127.0.0.1:8000"; // local backend

    const response = await fetch(API_URL + "/classify", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    // Remove "Processando..."
    resultContainer.lastChild.remove();

    let content = `<strong>Categoria:</strong> <span class="${
      data.category === "Produtivo" ? "text-green-400" : "text-red-400"
    }">${data.category}</span><br><br>`;
    content += `<strong>Resposta sugerida:</strong><br><br> ${data.suggested_response}`;

    addMessage(content, "bot");
  } catch (err) {
    console.error(err);
    resultContainer.lastChild.remove();
    addMessage("Erro ao conectar com o servidor.", "bot");
  }
});
