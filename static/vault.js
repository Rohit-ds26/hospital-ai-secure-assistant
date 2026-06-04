let vaultToken = "";

const vaultLoginForm = document.getElementById("vaultLoginForm");
const vaultLoginBtn = document.getElementById("vaultLoginBtn");
const vaultLoginError = document.getElementById("vaultLoginError");
const vaultUser = document.getElementById("vaultUser");
const vaultPass = document.getElementById("vaultPass");
const vaultStatusDot = document.getElementById("vaultStatusDot");
const vaultSessionName = document.getElementById("vaultSessionName");
const vaultSessionRole = document.getElementById("vaultSessionRole");
const vaultDocs = document.getElementById("vaultDocs");
const refreshVaultBtn = document.getElementById("refreshVaultBtn");
const vaultDocTitle = document.getElementById("vaultDocTitle");
const vaultDocMeta = document.getElementById("vaultDocMeta");
const vaultDocContent = document.getElementById("vaultDocContent");
const vaultAccountButtons = document.querySelectorAll("[data-vault-user]");

function prettyLabel(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function setVaultSession(username, role) {
  vaultSessionName.textContent = username;
  vaultSessionRole.textContent = role;
  vaultStatusDot.classList.add("active");
  refreshVaultBtn.disabled = false;
  localStorage.setItem("hospitalVaultSession", JSON.stringify({
    vaultToken,
    username,
    role,
  }));
}

async function loadVaultDocs() {
  vaultDocs.innerHTML = "<span class=\"muted\">Loading approved documents...</span>";

  const response = await fetch("/vault/docs", {
    headers: { Authorization: `Bearer ${vaultToken}` },
  });
  const data = await response.json();

  if (!response.ok) {
    vaultDocs.innerHTML = `<span class="error">${data.detail || "Unable to load vault documents."}</span>`;
    return;
  }

  const docs = data.documents || [];
  vaultDocs.innerHTML = "";

  if (!docs.length) {
    vaultDocs.innerHTML = "<span class=\"muted\">No approved documents available.</span>";
    return;
  }

  docs.forEach((doc) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "vault-doc-item";
    item.innerHTML = `
      <strong>${doc.title}</strong>
      <span>${prettyLabel(doc.document_type)} - Request ${doc.request_id}</span>
      <small>Approved by ${doc.approved_by || "admin"}${doc.approved_at ? ` on ${doc.approved_at}` : ""}</small>
    `;
    item.addEventListener("click", () => loadVaultDoc(doc.request_id));
    vaultDocs.appendChild(item);
  });
}

async function loadVaultDoc(requestId) {
  vaultDocTitle.textContent = "Loading document...";
  vaultDocMeta.textContent = `Request ${requestId}`;
  vaultDocContent.textContent = "Opening secure document...";

  const response = await fetch(`/vault/docs/${requestId}`, {
    headers: { Authorization: `Bearer ${vaultToken}` },
  });
  const data = await response.json();

  if (!response.ok) {
    vaultDocTitle.textContent = "Document Viewer";
    vaultDocMeta.textContent = `Request ${requestId}`;
    vaultDocContent.textContent = data.detail || "Unable to open this document.";
    return;
  }

  vaultDocTitle.textContent = data.title;
  vaultDocMeta.textContent = `${prettyLabel(data.document_type)} - Approved by ${data.approved_by || "admin"}`;
  vaultDocContent.textContent = data.content || "Document is empty.";
}

async function loginToVault(event) {
  event.preventDefault();
  vaultLoginBtn.disabled = true;
  vaultLoginBtn.textContent = "Signing in...";
  vaultLoginError.hidden = true;

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: vaultUser.value.trim(),
        password: vaultPass.value,
      }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Invalid credentials");
    }
    if (!["SUPER_ADMIN", "HOSPITAL_SUPERVISOR"].includes(data.role)) {
      throw new Error(`${data.role} is not allowed to access the vault`);
    }

    vaultToken = data.access_token;
    setVaultSession(vaultUser.value.trim(), data.role);
    await loadVaultDocs();
  } catch (err) {
    vaultLoginError.textContent = err.message || "Vault login failed or role not allowed.";
    vaultLoginError.hidden = false;
  } finally {
    vaultLoginBtn.disabled = false;
    vaultLoginBtn.textContent = "Sign in to vault";
  }
}

async function restoreVaultSession() {
  const saved = JSON.parse(localStorage.getItem("hospitalVaultSession") || "null");
  if (!saved?.vaultToken || !saved?.username || !saved?.role) {
    return;
  }
  vaultToken = saved.vaultToken;
  setVaultSession(saved.username, saved.role);
  await loadVaultDocs();
}

vaultAccountButtons.forEach((button) => {
  button.addEventListener("click", () => {
    vaultUser.value = button.dataset.vaultUser;
    vaultPass.value = button.dataset.vaultPass;
    vaultUser.focus();
  });
});

vaultLoginForm.addEventListener("submit", loginToVault);
refreshVaultBtn.addEventListener("click", loadVaultDocs);
restoreVaultSession();
