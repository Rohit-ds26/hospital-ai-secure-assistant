# Hospital AI System

A simulated enterprise healthcare backend and UI for testing role-based AI assistants, hospital workflows, secure document approvals, prompt-injection defenses, and MCP-style tool access.

The project includes:

- FastAPI backend
- SQLite demo database
- Role-based JWT authentication
- Patient, staff, and management chat surfaces
- Public patient FAQ mode before login
- Secure Document Vault for approved confidential supervisor documents
- MCP-style tool listing and invocation endpoints
- Mock AI mode for local demos without external AI keys

## 1. Quick Setup

Run this from the project root on Windows PowerShell:

```powershell
.\setup.ps1
```

The script will:

- create `.venv` if it does not exist
- install Python dependencies
- create `.env` if missing
- generate `hospital.db` if missing
- create `secure_vault/` if missing

To recreate demo data from scratch:

```powershell
.\setup.ps1 -ResetDb
```

To setup and start the server immediately:

```powershell
.\setup.ps1 -StartServer
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then rerun:

```powershell
.\setup.ps1
```

## 2. Manual Setup

If you do not want to use the setup script:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python generate_hospital_data.py
```

Create `.env`:

```env
HOSPITAL_AI_PROVIDER=mock
JWT_SECRET=hospital-dev-secret
REPORT_GENERATION_DELAY_SECONDS=0
```

## 3. Run Locally

Start the app:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open:

- Main dashboard: `http://127.0.0.1:8000/`
- Patient chat: `http://127.0.0.1:8000/patient`
- Staff chat: `http://127.0.0.1:8000/staff`
- Management chat: `http://127.0.0.1:8000/management`
- Secure Document Vault: `http://127.0.0.1:8000/vault`
- Swagger API docs: `http://127.0.0.1:8000/docs`
- Health/status: `http://127.0.0.1:8000/api/status`

## 4. Run With Ngrok

Install ngrok, then start your local server first:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
ngrok http 8000
```

Ngrok will print a public URL like:

```text
https://example-name.ngrok-free.dev
```

Share these with testers:

- `https://example-name.ngrok-free.dev/patient`
- `https://example-name.ngrok-free.dev/staff`
- `https://example-name.ngrok-free.dev/management`
- `https://example-name.ngrok-free.dev/vault`
- `https://example-name.ngrok-free.dev/docs`

If you use a fixed ngrok domain, point it to the same local port your FastAPI app is running on.

To inspect active ngrok tunnels locally:

```powershell
Invoke-RestMethod http://127.0.0.1:4040/api/tunnels
```

## 5. Demo Accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `Admin@123` | `SUPER_ADMIN` |
| `supervisor1` | `Supervisor@123` | `HOSPITAL_SUPERVISOR` |
| `doctor1` | `Doctor@123` | `DOCTOR` |
| `doctor2` | `Doctor@123` | `DOCTOR` |
| `doctor3` | `Doctor@123` | `DOCTOR` |
| `nurse1` | `Nurse@123` | `NURSE` |
| `labtech1` | `LabTech@123` | `LAB_TECH` |
| `receptionist1` | `Reception@123` | `RECEPTIONIST` |
| `billing1` | `Billing@123` | `BILLING_INSURANCE` |
| `patient1` | `Patient@123` | `PATIENT` |
| `patient2` | `Patient@123` | `PATIENT` |

## 6. Chat Surfaces

### Patient Chat

URL:

```text
/patient
```

API:

```text
POST /chat/patient
```

Behavior:

- Without login: public hospital FAQ mode
- With `PATIENT` login: private patient mode

Public mode can answer general questions about:

- services
- appointment process
- lab services
- billing support
- emergency guidance
- medical-record request process

Public mode cannot reveal:

- patient profile
- medical records
- lab reports
- billing records
- prescriptions
- insurance claims
- appointment status

### Staff Chat

URL:

```text
/staff
```

API:

```text
POST /chat/staff
```

Requires one of:

- `DOCTOR`
- `NURSE`
- `LAB_TECH`
- `RECEPTIONIST`
- `BILLING_INSURANCE`

Each staff role only sees tools allowed for that role.

### Management Chat

URL:

```text
/management
```

API:

```text
POST /chat/management
```

Requires:

- `SUPER_ADMIN`
- `HOSPITAL_SUPERVISOR`

Management role split:

- Supervisor creates secure document requests and checks own request status.
- Admin approves/rejects document requests and views pending queue.
- Admin does not create supervisor document requests.
- Supervisor does not approve requests.

## 7. Secure Document Vault

URL:

```text
/vault
```

APIs:

```text
GET /vault/docs
GET /vault/docs/{request_id}
```

Allowed roles:

- `SUPER_ADMIN`
- `HOSPITAL_SUPERVISOR`

Denied roles:

- `PATIENT`
- `DOCTOR`
- `NURSE`
- `LAB_TECH`
- `RECEPTIONIST`
- `BILLING_INSURANCE`

Vault behavior:

- Supervisor creates confidential document requests from management chat.
- The generated document content is stored in `secure_vault/`.
- Chat never displays confidential document content.
- Request stays `PENDING_ADMIN_APPROVAL`.
- Admin approves/rejects.
- After approval, supervisor signs into `/vault` again to view their own approved docs.
- Admin signs into `/vault` to view all approved docs.

## 8. Supervisor Document Types

Supervisor can create these secure document requests:

| Document Type | Description | Requires Patient ID |
|---|---|---|
| `patient_full_records` | Full patient document: profile, appointments, medical records, prescriptions, lab reports, billing, insurance | Yes |
| `hospital_billing_records` | All hospital billing records and billing summary | No |
| `patient_lab_reports` | All lab reports for one patient | Yes |
| `patient_insurance_details` | Insurance details and claims for one patient | Yes |
| `patient_records_summary` | Monthly patient activity summary document | No |

Example supervisor chat prompts:

```text
Create full patient records document for patient 1
Create all hospital billing records document
Create lab reports document for patient 1
Create insurance details document for patient 1
Create a secure document for last month patient records
Show my document requests
Show approved document 1
```

Example admin chat prompts:

```text
Show pending document requests
Approve document request 1
Reject document request 1
Show hospital analytics
Show audit logs
```

## 9. API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Main UI |
| `GET` | `/patient` | No | Patient UI |
| `GET` | `/staff` | No page auth, chat requires JWT | Staff UI |
| `GET` | `/management` | No page auth, chat requires JWT | Management UI |
| `GET` | `/vault` | No page auth, vault APIs require JWT | Secure Document Vault UI |
| `GET` | `/docs` | No | Swagger/OpenAPI docs |
| `GET` | `/api/status` | No | Service status |
| `POST` | `/auth/login` | No | Login and receive JWT |
| `POST` | `/chat/patient` | Optional | Public patient FAQ or signed-in patient chat |
| `POST` | `/chat/staff` | Yes | Staff chat |
| `POST` | `/chat/management` | Yes | Management chat |
| `GET` | `/mcp/health` | No | MCP health |
| `GET` | `/mcp/tools` | Yes | List tools available to signed-in role |
| `POST` | `/mcp/invoke` | Yes | Invoke a tool directly |
| `GET` | `/mcp/sse` | Yes/token query | MCP SSE stream |
| `POST` | `/mcp/sse/message` | Yes/token query | MCP SSE message endpoint |
| `GET` | `/vault/docs` | Yes | List approved vault docs |
| `GET` | `/vault/docs/{request_id}` | Yes | Read approved vault doc |

## 10. API Testing Examples

### Login

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"Admin@123"}'

$token = $login.access_token
```

### List Tools For Role

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/mcp/tools `
  -Headers @{ Authorization = "Bearer $token" }
```

### Public Patient Chat

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/chat/patient `
  -ContentType "application/json" `
  -Body '{"user_prompt":"What lab services are available?"}'
```

### Signed-In Patient Chat

```powershell
$patient = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"patient1","password":"Patient@123"}'

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/chat/patient `
  -Headers @{ Authorization = "Bearer $($patient.access_token)" } `
  -ContentType "application/json" `
  -Body '{"user_prompt":"Show my profile"}'
```

### Supervisor Creates Secure Document Request

```powershell
$sup = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"supervisor1","password":"Supervisor@123"}'

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/mcp/invoke `
  -Headers @{ Authorization = "Bearer $($sup.access_token)" } `
  -ContentType "application/json" `
  -Body '{"tool_name":"create_secure_document_request","arguments":{"document_type":"patient_lab_reports","patient_id":1}}'
```

### Admin Approves Request

```powershell
$admin = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"Admin@123"}'

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/mcp/invoke `
  -Headers @{ Authorization = "Bearer $($admin.access_token)" } `
  -ContentType "application/json" `
  -Body '{"tool_name":"approve_report_request","arguments":{"request_id":1}}'
```

### View Vault Docs

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/vault/docs `
  -Headers @{ Authorization = "Bearer $($admin.access_token)" }
```

## 11. AI Provider Configuration

Default local/demo mode:

```env
HOSPITAL_AI_PROVIDER=mock
```

OpenAI:

```env
HOSPITAL_AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4.1-mini
```

Gemini:

```env
HOSPITAL_AI_PROVIDER=gemini
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.0-flash
```

Vertex AI:

```env
HOSPITAL_AI_PROVIDER=vertex
VERTEX_PROJECT_ID=your_project
VERTEX_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=service_account.json
```

## 12. Database

Main SQLite database:

```text
hospital.db
```

Generated by:

```powershell
python generate_hospital_data.py
```

Important tables include:

- `users`
- `hospital_staff`
- `doctors`
- `patients`
- `appointments`
- `medical_records`
- `prescriptions`
- `lab_reports`
- `billing`
- `insurance`
- `hospital_documents`
- `audit_logs`
- `management_report_requests`

`management_report_requests` stores metadata for secure document requests. The confidential document body is stored in `secure_vault/`.

## 13. Security Model

- JWT authentication
- Role-based access control
- Patient self-access isolation
- Staff tools limited by role
- Supervisor creates confidential document requests
- Admin approves/rejects confidential document requests
- Vault requires separate sign-in
- Vault content is not served from `/static`
- Chat does not display confidential vault document bodies
- Prompt filtering blocks obvious prompt-injection attempts
- Audit logs record tool execution attempts

## 14. Recommended Demo Flow

1. Open `/patient`.
2. Ask public question without login:

   ```text
   What services does the hospital provide?
   ```

3. Sign in as `patient1`.
4. Ask:

   ```text
   Show my lab reports
   ```

5. Open `/management`.
6. Sign in as `supervisor1`.
7. Ask:

   ```text
   Create lab reports document for patient 1
   ```

8. Sign out/refresh or login as `admin`.
9. Ask:

   ```text
   Show pending document requests
   Approve document request 1
   ```

10. Open `/vault`.
11. Sign in as `supervisor1` to see own approved docs.
12. Sign in as `admin` to see all approved docs.

## 15. Development Notes

Useful checks:

```powershell
.\.venv\Scripts\python.exe -m py_compile app.py api\chat_api.py api\vault_api.py services\tool_router.py tools\admin_tools.py
```

Run with reload during development:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

If browser UI looks stale, hard refresh:

```text
Ctrl + F5
```

## 16. Cleanup Candidates

These files/folders are development artifacts and are safe candidates for deletion before sharing the project, but do not delete them if you want to keep local test history:

- `test_quick.py`
- `test_phase1.py`
- `test_advanced.py`
- `test_out.txt`
- `test_out_new.txt`
- all `__pycache__/` folders
- `.venv/`
- `.venv312/`
- `hospital.db`
- `secure_vault/`

If you delete `hospital.db`, run:

```powershell
.\setup.ps1 -ResetDb
```

If you delete `secure_vault/`, it will be recreated by setup or when a new vault document is generated.
