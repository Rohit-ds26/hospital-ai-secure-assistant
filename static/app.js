const demoAccounts = [
  ["admin", "Admin@123", "SUPER_ADMIN"],
  ["supervisor1", "Supervisor@123", "HOSPITAL_SUPERVISOR"],
  ["doctor1", "Doctor@123", "DOCTOR"],
  ["nurse1", "Nurse@123", "NURSE"],
  ["labtech1", "LabTech@123", "LAB_TECH"],
  ["receptionist1", "Reception@123", "RECEPTIONIST"],
  ["billing1", "Billing@123", "BILLING_INSURANCE"],
  ["patient1", "Patient@123", "PATIENT"],
];

const chatbotProfiles = {
  patient: {
    label: "Patient Assistant",
    eyebrow: "Patient information and care",
    summary: "General hospital help before login, personal services after patient sign-in.",
    help: "Ask general questions without login, or sign in as a patient for your own records and services.",
    placeholder: "Ask general questions, or sign in for personal patient details...",
    allowedRoles: ["PATIENT"],
    requiresAuth: false,
    supportsLogin: true,
    defaultAccount: ["patient1", "Patient@123"],
    guestPrompts: [
      "What services does the hospital provide?",
      "How can I book an appointment?",
      "How do I request medical records?",
      "What should I do in an emergency?",
      "What lab services are available?",
      "How does billing support work?",
    ],
    patientPrompts: [
      "Show my profile",
      "Show my appointments",
      "Show my lab reports",
      "Show my billing details",
      "Show my prescriptions",
      "Show my insurance claims",
      "Show my medical history",
    ],
  },
  staff: {
    label: "Hospital Staff Assistant",
    eyebrow: "Internal staff operations",
    summary: "A workflow assistant for doctors, nurses, lab, reception, and billing teams.",
    help: "Use normal staff workflows. Each staff role only sees its own allowed tools.",
    placeholder: "Ask the staff assistant...",
    allowedRoles: ["DOCTOR", "NURSE", "LAB_TECH", "RECEPTIONIST", "BILLING_INSURANCE"],
    requiresAuth: true,
    supportsLogin: true,
    defaultAccount: ["doctor1", "Doctor@123"],
    prompts: [
      "Show medical records for patient 1",
      "Show lab reports for patient 1",
      "Book an appointment for patient 1 with doctor 1",
      "Show billing details for patient 1",
      "Show audit logs",
    ],
  },
  management: {
    label: "Management Assistant",
    eyebrow: "Senior governance",
    summary: "A restricted assistant for supervisors and administrators.",
    help: "Review analytics, audit logs, and governance data for senior hospital operations.",
    placeholder: "Ask the management assistant...",
    allowedRoles: ["SUPER_ADMIN", "HOSPITAL_SUPERVISOR"],
    requiresAuth: true,
    supportsLogin: true,
    defaultAccount: ["admin", "Admin@123"],
    adminPrompts: [
      "Show hospital analytics",
      "Show audit logs",
      "Show pending document requests",
      "Approve document request 1",
      "Reject document request 1",
      "Show clinical safety rules",
    ],
    supervisorPrompts: [
      "Show hospital analytics",
      "Show audit logs",
      "Create full patient records document for patient 1",
      "Create all hospital billing records document",
      "Create lab reports document for patient 1",
      "Create insurance details document for patient 1",
      "Create a secure document for last month patient records",
      "Show my document requests",
      "Show approved document 1",
      "Show clinical safety rules",
      "Search hospital documents for emergency",
    ],
  },
};

let authToken = "";
let currentUser = null;
let selectedChatbot = document.body.dataset.chatbot || "patient";
let fixedChatbot = Boolean(document.body.dataset.chatbot);
let conversationId = `hospital-${Math.random().toString(36).slice(2)}`;
let allowedTools = [];

const botSelector = document.getElementById("botSelector");
const botAccessNote = document.getElementById("botAccessNote");
const botEyebrow = document.getElementById("botEyebrow");
const botTitle = document.getElementById("botTitle");
const botSummary = document.getElementById("botSummary");
const chatSurfaceHelp = document.getElementById("chatSurfaceHelp");
const quickActions = document.getElementById("quickActions");
const loginForm = document.getElementById("loginForm");
const loginBtn = document.getElementById("loginBtn");
const loginUser = document.getElementById("loginUser");
const loginPass = document.getElementById("loginPass");
const loginError = document.getElementById("loginError");
const accountGrid = document.getElementById("accountGrid");
const sessionName = document.getElementById("sessionName");
const sessionRole = document.getElementById("sessionRole");
const statusDot = document.querySelector(".status-dot");
const toolsList = document.getElementById("toolsList");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const toolSelect = document.getElementById("toolSelect");
const toolArgs = document.getElementById("toolArgs");
const invokeBtn = document.getElementById("invokeBtn");
const toolOutput = document.getElementById("toolOutput");
const surfaceLinks = document.getElementById("surfaceLinks");

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function activeProfile() {
  return chatbotProfiles[selectedChatbot];
}

function sessionStorageKey() {
  return `hospitalChatSession:${selectedChatbot}`;
}

function historyStorageKey(username = currentUser?.username, role = currentUser?.role) {
  const identity = username && role ? `${username}:${role}` : "guest";
  return `hospitalChatHistory:${selectedChatbot}:${identity}`;
}

function saveSession() {
  if (!currentUser || !authToken) {
    return;
  }
  localStorage.setItem(sessionStorageKey(), JSON.stringify({
    authToken,
    currentUser,
    conversationId,
  }));
}

function saveChatMessage(role, text) {
  const key = historyStorageKey();
  const history = JSON.parse(localStorage.getItem(key) || "[]");
  history.push({ role, text });
  localStorage.setItem(key, JSON.stringify(history.slice(-40)));
}

function loadChatHistory(username = currentUser?.username, role = currentUser?.role) {
  return JSON.parse(localStorage.getItem(historyStorageKey(username, role)) || "[]");
}

function renderChatHistory(history) {
  chatMessages.innerHTML = "";
  if (!history.length) {
    addMessage("assistant", `Signed in as ${currentUser.role} on ${activeProfile().label}. Your previous chat will appear here as you continue.`, false);
    return;
  }
  history.forEach((message) => addMessage(message.role, message.text, false));
}

function humanizeKey(key) {
  return String(key)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function humanizeValue(value) {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return `${value.length} item${value.length === 1 ? "" : "s"}`;
  }
  if (typeof value === "object") {
    return "";
  }
  return String(value);
}

function titleFromToolName(toolName) {
  const titles = {
    list_pending_report_requests: "Pending Document Requests",
    get_my_report_requests: "My Document Requests",
    get_approved_management_report: "Approved Document",
    approve_report_request: "Document Approval",
    reject_report_request: "Document Rejection",
    create_secure_document_request: "Secure Document Request",
    generate_patient_records_report: "Secure Document Request",
  };
  return titles[toolName] || humanizeKey(String(toolName || "Result").replace(/^get_/, "").replace(/^patient_/, "patient_"));
}

function parseToolResultText(text) {
  if (typeof text !== "string") {
    return null;
  }

  const marker = text.match(/^Here is the result from ([\w_]+):\s*/);
  if (!marker) {
    return null;
  }

  const jsonText = text.slice(marker[0].length).trim();
  try {
    return {
      title: titleFromToolName(marker[1]),
      data: JSON.parse(jsonText),
    };
  } catch (err) {
    return null;
  }
}

function renderObjectRows(container, record) {
  Object.entries(record).forEach(([key, value]) => {
    if (value && typeof value === "object") {
      return;
    }

    const row = document.createElement("div");
    row.className = "result-row";

    const label = document.createElement("span");
    label.className = "result-label";
    label.textContent = humanizeKey(key);

    const text = document.createElement("span");
    text.className = "result-value";
    if (key.toLowerCase().includes("url") && value) {
      const link = document.createElement("a");
      link.className = "result-link";
      link.href = String(value);
      link.textContent = "Open Secure Document Vault";
      text.appendChild(link);
    } else {
      text.textContent = humanizeValue(value);
    }

    row.append(label, text);
    container.appendChild(row);
  });
}

function renderRecordSection(wrapper, record, title) {
  const section = document.createElement("div");
  section.className = "result-section";

  if (title) {
    const sectionTitle = document.createElement("span");
    sectionTitle.className = "result-section-title";
    sectionTitle.textContent = title;
    section.appendChild(sectionTitle);
  }

  if (record && typeof record === "object" && !Array.isArray(record)) {
    renderObjectRows(section, record);
  } else {
    const value = document.createElement("p");
    value.textContent = humanizeValue(record);
    section.appendChild(value);
  }

  wrapper.appendChild(section);
}

function renderNestedResultGroups(wrapper, data) {
  let renderedGroup = false;

  Object.entries(data).forEach(([key, value]) => {
    if (!Array.isArray(value)) {
      return;
    }

    renderedGroup = true;
    const groupTitle = document.createElement("span");
    groupTitle.className = "result-group-title";
    groupTitle.textContent = humanizeKey(key);
    wrapper.appendChild(groupTitle);

    if (!value.length) {
      const empty = document.createElement("p");
      empty.className = "muted result-empty";
      empty.textContent = "No records found.";
      wrapper.appendChild(empty);
      return;
    }

    value.forEach((record, index) => {
      renderRecordSection(wrapper, record, `${humanizeKey(key.replace(/s$/, ""))} ${index + 1}`);
    });
  });

  return renderedGroup;
}

function renderStructuredResult(container, title, data) {
  const wrapper = document.createElement("div");
  wrapper.className = "result-card";

  const heading = document.createElement("strong");
  heading.className = "result-title";
  heading.textContent = title;
  wrapper.appendChild(heading);

  if (data && typeof data === "object" && !Array.isArray(data)) {
    const scalarData = Object.fromEntries(
      Object.entries(data).filter(([, value]) => !Array.isArray(value) && !(value && typeof value === "object"))
    );
    if (Object.keys(scalarData).length) {
      renderRecordSection(wrapper, scalarData);
    }

    if (renderNestedResultGroups(wrapper, data)) {
      container.appendChild(wrapper);
      return;
    }

    if (Object.keys(scalarData).length) {
      container.appendChild(wrapper);
      return;
    }
  }

  const records = Array.isArray(data) ? data : [data];

  if (!records.length) {
    const empty = document.createElement("p");
    empty.className = "muted result-empty";
    empty.textContent = "No records found.";
    wrapper.appendChild(empty);
  }

  records.forEach((record, index) => {
    renderRecordSection(wrapper, record, records.length > 1 ? `Record ${index + 1}` : "");
  });

  container.appendChild(wrapper);
}

function setMessageContent(item, text) {
  item.innerHTML = "";

  const parsedToolResult = parseToolResultText(text);
  if (parsedToolResult) {
    renderStructuredResult(item, parsedToolResult.title, parsedToolResult.data);
    return;
  }

  const plain = document.createElement("span");
  plain.textContent = text;
  item.appendChild(plain);
}

function addMessage(role, text, persist = true) {
  const item = document.createElement("div");
  item.className = `message ${role}`;
  setMessageContent(item, text);
  chatMessages.appendChild(item);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  if (persist) {
    saveChatMessage(role, text);
  }
  return item;
}

function setSignedIn(username, role, options = {}) {
  currentUser = { username, role };
  conversationId = options.conversationId || `hospital-${selectedChatbot}-${role.toLowerCase()}-${Math.random().toString(36).slice(2)}`;
  sessionName.textContent = username;
  sessionRole.textContent = role;
  statusDot.classList.add("active");
  chatInput.disabled = false;
  sendBtn.disabled = false;
  saveSession();
  renderChatHistory(loadChatHistory(username, role));
  renderQuickActions();
}

function renderAccounts() {
  accountGrid.innerHTML = "";
  if (!activeProfile().supportsLogin) {
    accountGrid.innerHTML = "<span>No account login for this chat</span>";
    return;
  }
  const eligibleRoles = new Set(activeProfile().allowedRoles);
  demoAccounts.filter(([, , role]) => eligibleRoles.has(role)).forEach(([username, password, role]) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = `${username} - ${role}`;
    btn.addEventListener("click", () => {
      loginUser.value = username;
      loginPass.value = password;
    });
    accountGrid.appendChild(btn);
  });
}

function resetSession() {
  authToken = "";
  currentUser = null;
  allowedTools = [];
  localStorage.removeItem(sessionStorageKey());
  sessionName.textContent = "Not signed in";
  sessionRole.textContent = "No active role";
  statusDot.classList.remove("active");
  chatInput.disabled = true;
  sendBtn.disabled = true;
  toolSelect.disabled = true;
  toolArgs.disabled = true;
  invokeBtn.disabled = true;
  toolsList.innerHTML = "<span>Sign in to view tools</span>";
  toolSelect.innerHTML = "";
  toolOutput.textContent = "No tool result yet.";
}

function renderQuickActions() {
  quickActions.innerHTML = "";
  const profile = activeProfile();
  let prompts = profile.prompts || [];
  if (selectedChatbot === "patient") {
    prompts = authToken ? profile.patientPrompts : profile.guestPrompts;
  }
  if (selectedChatbot === "management" && currentUser) {
    prompts = currentUser.role === "SUPER_ADMIN" ? profile.adminPrompts : profile.supervisorPrompts;
  }

  const select = document.createElement("select");
  select.className = "prompt-select";

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Choose an example question...";
  select.appendChild(placeholder);

  prompts.forEach((prompt) => {
    const option = document.createElement("option");
    option.value = prompt;
    option.textContent = prompt;
    select.appendChild(option);
  });

  select.addEventListener("change", () => {
    if (!select.value) return;
    chatInput.value = select.value;
    chatInput.focus();
    select.value = "";
  });

  quickActions.appendChild(select);
}

function renderChatbotSurface() {
  const profile = activeProfile();
  document.querySelectorAll("[data-bot]").forEach((button) => {
    button.classList.toggle("active", button.dataset.bot === selectedChatbot);
  });
  botEyebrow.textContent = profile.eyebrow;
  botTitle.textContent = profile.label;
  botSummary.textContent = profile.summary;
  chatSurfaceHelp.textContent = profile.help;
  chatInput.placeholder = profile.placeholder;
  botAccessNote.textContent = profile.requiresAuth
    ? `Allowed roles: ${profile.allowedRoles.join(", ")}`
    : profile.supportsLogin
      ? "No login needed for general questions. Sign in as PATIENT for personal details."
      : "No login required. Public information only.";
  loginUser.value = profile.defaultAccount[0];
  loginPass.value = profile.defaultAccount[1];
  chatMessages.innerHTML = "";
  loginForm.hidden = !profile.supportsLogin;
  chatInput.disabled = profile.requiresAuth;
  sendBtn.disabled = profile.requiresAuth;
  if (profile.requiresAuth) {
    addMessage("assistant", `Selected ${profile.label}. Sign in with an eligible role to begin.`, false);
  } else {
    sessionName.textContent = profile.supportsLogin ? "Guest patient" : "Public visitor";
    sessionRole.textContent = profile.supportsLogin ? "Public mode" : "No authentication";
    statusDot.classList.remove("active");
    toolsList.innerHTML = profile.supportsLogin
      ? "<span>Sign in to view patient tools</span>"
      : "<span>No tools available for public chat</span>";
    addMessage("assistant", profile.supportsLogin
      ? "Patient chat is ready in public mode. Sign in to access your own patient details."
      : "Public chat is ready. I can answer general hospital questions, but not patient-specific data.", false);
  }
  renderQuickActions();
  renderAccounts();
}

function renderTools() {
  toolsList.innerHTML = "";
  toolSelect.innerHTML = "";

  if (!allowedTools.length) {
    toolsList.innerHTML = "<span>No tools available</span>";
    return;
  }

  allowedTools.forEach((tool) => {
    const pill = document.createElement("span");
    pill.textContent = tool;
    toolsList.appendChild(pill);

    const opt = document.createElement("option");
    opt.value = tool;
    opt.textContent = tool;
    toolSelect.appendChild(opt);
  });

  toolSelect.disabled = false;
  toolArgs.disabled = false;
  invokeBtn.disabled = false;
}

async function loadTools() {
  const response = await fetch("/mcp/tools", {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  const data = await response.json();
  allowedTools = data.tools || [];
  renderTools();
}

async function login(event) {
  event.preventDefault();
  loginBtn.disabled = true;
  loginBtn.textContent = "Signing in...";
  loginError.hidden = true;

  try {
    const response = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: loginUser.value.trim(),
        password: loginPass.value,
      }),
    });

    if (!response.ok) {
      throw new Error("Login failed");
    }

    const data = await response.json();
    if (!activeProfile().allowedRoles.includes(data.role)) {
      throw new Error(`${activeProfile().label} does not allow ${data.role}`);
    }
    authToken = data.access_token;
    setSignedIn(loginUser.value.trim(), data.role);
    await loadTools();
    addMessage("assistant", "Your visible tools are now loaded.", false);
  } catch (err) {
    loginError.hidden = false;
  } finally {
    loginBtn.disabled = false;
    loginBtn.textContent = "Sign in";
  }
}

async function sendChat(event) {
  event.preventDefault();
  const prompt = chatInput.value.trim();
  const profile = activeProfile();
  if (!prompt || (profile.requiresAuth && !authToken)) return;

  addMessage("user", prompt);
  chatInput.value = "";
  const pending = addMessage("assistant", authToken ? "Working through authorized hospital tools..." : "Checking public hospital guidance...", false);

  try {
    const response = await fetch(`/chat/${selectedChatbot}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
      body: JSON.stringify({
        user_prompt: prompt,
        conversation_id: conversationId,
      }),
    });
    const raw = await response.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch (err) {
      data = { detail: raw };
    }
    const detail = typeof data.detail === "string" ? data.detail : data.detail ? pretty(data.detail) : "";
    const answer = data.answer || data.error || detail || `No response returned. HTTP ${response.status}`;
    setMessageContent(pending, answer);
    saveChatMessage("assistant", answer);
  } catch (err) {
    const answer = "Unable to reach the Hospital AI backend.";
    setMessageContent(pending, answer);
    saveChatMessage("assistant", answer);
  }
}

async function restoreSavedSession() {
  const saved = JSON.parse(localStorage.getItem(sessionStorageKey()) || "null");
  if (!saved?.authToken || !saved?.currentUser) {
    return;
  }

  const profile = activeProfile();
  if (!profile.allowedRoles?.includes(saved.currentUser.role)) {
    localStorage.removeItem(sessionStorageKey());
    return;
  }

  authToken = saved.authToken;
  currentUser = saved.currentUser;
  setSignedIn(currentUser.username, currentUser.role, {
    conversationId: saved.conversationId,
  });
  await loadTools();
}

async function invokeTool() {
  if (!authToken) return;

  let args = {};
  try {
    args = JSON.parse(toolArgs.value || "{}");
  } catch (err) {
    toolOutput.textContent = "Arguments must be valid JSON.";
    return;
  }

  invokeBtn.disabled = true;
  toolOutput.textContent = "Invoking...";

  try {
    const response = await fetch("/mcp/invoke", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({
        tool_name: toolSelect.value,
        arguments: args,
      }),
    });
    const data = await response.json();
    toolOutput.textContent = pretty(data);
  } catch (err) {
    toolOutput.textContent = "Tool invocation failed.";
  } finally {
    invokeBtn.disabled = false;
  }
}

if (botSelector) {
  if (fixedChatbot) {
    botSelector.hidden = true;
  }

  botSelector.addEventListener("click", (event) => {
    if (fixedChatbot) return;
    const button = event.target.closest("[data-bot]");
    if (!button) return;
    selectedChatbot = button.dataset.bot;
    resetSession();
    renderChatbotSurface();
  });
}

if (surfaceLinks) {
  surfaceLinks.querySelectorAll("[data-surface-link]").forEach((link) => {
    link.classList.toggle("active", link.dataset.surfaceLink === selectedChatbot);
  });
}

loginForm.addEventListener("submit", login);
chatForm.addEventListener("submit", sendChat);
invokeBtn.addEventListener("click", invokeTool);

renderChatbotSurface();
restoreSavedSession();
