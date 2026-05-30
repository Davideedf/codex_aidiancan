const statusEl = document.querySelector("#status");
const documentsEl = document.querySelector("#documents");
const messagesEl = document.querySelector("#messages");
const uploadForm = document.querySelector("#upload-form");
const fileInput = document.querySelector("#file-input");
const askForm = document.querySelector("#ask-form");
const questionEl = document.querySelector("#question");
const clearButton = document.querySelector("#clear-button");

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch {
      // Keep the original HTTP status text.
    }
    throw new Error(detail);
  }
  return response.json();
}

async function refreshHealth() {
  try {
    const data = await api("/api/health");
    statusEl.textContent = data.llm_enabled ? "LLM 已启用" : "本地检索模式";
  } catch (error) {
    statusEl.textContent = "服务不可用";
    statusEl.classList.add("error");
  }
}

async function refreshDocuments() {
  const data = await api("/api/documents");
  documentsEl.innerHTML = "";
  if (!data.documents.length) {
    documentsEl.append(el("div", "empty", "暂无文档"));
    return;
  }

  for (const doc of data.documents) {
    const item = el("div", "document-item");
    item.append(el("div", "document-title", doc.title));
    item.append(el("div", "document-meta", `${doc.chunks} 个知识片段`));
    documentsEl.append(item);
  }
}

function appendMessage(role, text, sources = []) {
  const message = el("div", `message ${role}`, text);
  if (sources.length) {
    const sourceList = el("div", "sources");
    for (const source of sources) {
      const row = el("div", "source");
      row.innerHTML = `<strong>${escapeHtml(source.title)}</strong> · 相关度 ${source.score}<br>${escapeHtml(source.snippet)}`;
      sourceList.append(row);
    }
    message.append(sourceList);
  }
  messagesEl.append(message);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) return;

  const submitButton = uploadForm.querySelector("button");
  submitButton.disabled = true;
  try {
    const body = new FormData();
    for (const file of fileInput.files) body.append("files", file);
    await api("/api/documents", { method: "POST", body });
    fileInput.value = "";
    await refreshDocuments();
  } catch (error) {
    appendMessage("agent", `上传失败：${error.message}`);
  } finally {
    submitButton.disabled = false;
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionEl.value.trim();
  if (!question) return;

  appendMessage("user", question);
  questionEl.value = "";
  const submitButton = askForm.querySelector("button");
  submitButton.disabled = true;

  try {
    const data = await api("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: 5 }),
    });
    appendMessage("agent", data.answer, data.sources);
  } catch (error) {
    appendMessage("agent", `回答失败：${error.message}`);
  } finally {
    submitButton.disabled = false;
    questionEl.focus();
  }
});

questionEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    askForm.requestSubmit();
  }
});

clearButton.addEventListener("click", async () => {
  clearButton.disabled = true;
  try {
    await api("/api/documents", { method: "DELETE" });
    await refreshDocuments();
    appendMessage("agent", "索引已清空。");
  } catch (error) {
    appendMessage("agent", `清空失败：${error.message}`);
  } finally {
    clearButton.disabled = false;
  }
});

appendMessage("agent", "上传企业资料后开始提问。支持 txt、md、csv、json、log。");
refreshHealth();
refreshDocuments();
