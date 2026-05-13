# Gmail MCP Server Integration - Complete Flow Guide

## Overview
This document explains how the Gmail read functionality works in your MCP server setup, from initial setup through searching emails.

---

## Architecture Components

### 1. Files Involved

#### `requirements.txt`
- Lists all Python dependencies needed
- Contains:
  - `google-api-python-client` - Google API library
  - `google-auth-oauthlib` - OAuth authentication library
  - `google-auth-httplib2` - HTTP library for Google Auth

#### `mcp_server.py`
- Main MCP server file
- Contains the `MCPServer` class with Gmail tools
- Implements `search_gmail()` and `authenticate_gmail()` methods
- Fixed import: uses `google_auth_oauthlib` (not `google.auth.oauthlib`)

#### `credentials.json`
- Downloaded from Google Cloud Console
- Contains OAuth 2.0 client credentials
- Stores: client ID, client secret, redirect URIs
- **Must be in the same folder as `mcp_server.py`**

#### `token.json`
- Auto-generated after first successful OAuth login
- Stores: access token, refresh token, expiration info
- Created automatically by `authenticate_gmail()` method
- Reused for subsequent API calls (no re-login needed)

#### `.mcp.json`
- Configuration file for running the MCP server
- Defines how to start `mcp_server.py`

#### `GMAIL_API_SETUP.md`
- Step-by-step setup guide (for manual reference)

---

## Setup Steps (Sequence)

### Step 1: Create Google Cloud Project
```
Google Cloud Console → Create new project
Project name: "Gmail MCP Server"
```

### Step 2: Enable Gmail API
```
Google Cloud Console → APIs & Services → Library
Search: "Gmail API" → Enable
```

### Step 3: Create OAuth Consent Screen
```
Google Cloud Console → APIs & Services → OAuth consent screen
- Select user type: External (for development)
- Fill in app name, support email, developer email
- Add yourself as a test user (your Gmail address)
- Save
```

### Step 4: Create OAuth 2.0 Credentials
```
Google Cloud Console → APIs & Services → Credentials
- Click "Create Credentials" → "OAuth client ID"
- Choose: "Desktop application"
- Download JSON → Save as "credentials.json"
- Place in: c:\Users\dilip\Desktop\github_test2\test\
```

### Step 5: Install Dependencies
```powershell
cd c:\Users\dilip\Desktop\github_test2\test
pip install -r requirements.txt
```

This installs:
- google-api-python-client
- google-auth-oauthlib
- google-auth-httplib2

---

## How Gmail Search Works (Complete Flow)

### Phase 1: Import & Initialization

When you import `mcp_server.py`:

```python
# mcp_server.py lines 19-30
try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow  # OAuth flow
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build  # Gmail API service
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False
```

**What happens:**
- Python checks if Gmail libraries are installed
- If all imports succeed → `GMAIL_API_AVAILABLE = True`
- If any fails → `GMAIL_API_AVAILABLE = False`

### Phase 2: Create MCPServer Instance

```python
srv = MCPServer()
```

**What happens:**
- MCPServer class initializes
- Sets `self.gmail_service = None` (not authenticated yet)
- Registers available tools (search_gmail, authenticate_gmail, etc.)

### Phase 3: Call search_gmail()

```python
result = srv.search_gmail(query='from:equitable', max_results=5)
```

**Execution sequence:**

#### Step 3a: Check if Gmail libraries available
```python
if not GMAIL_API_AVAILABLE:
    return {"error": "Gmail API libraries not installed..."}
```

#### Step 3b: Authenticate if not already done
```python
if self.gmail_service is None:
    auth_result = self.authenticate_gmail()
    if "error" in auth_result:
        return auth_result
```

This calls `authenticate_gmail()`:

#### Step 3c: authenticate_gmail() Flow

**Sub-step 1: Check for existing token.json**
```python
if os.path.exists('token.json'):
    creds = OAuth2Credentials.from_authorized_user_file('token.json')
    self.gmail_service = build('gmail', 'v1', credentials=creds, ...)
    return {"status": "ok", "message": "Authenticated using saved token"}
```

**Result:** If `token.json` exists, use it (fast path - no browser needed)

**Sub-step 2: If no token.json, start OAuth flow**
```python
if not os.path.exists('credentials.json'):
    return {"error": "credentials.json not found..."}

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
flow = InstalledAppFlow.from_client_secrets_file(credentials.json, SCOPES)
creds = flow.run_local_server(port=0)
```

**What happens:**
- Reads `credentials.json` (OAuth client credentials)
- Creates an OAuth flow with Gmail read-only scope
- Opens browser at Google OAuth URL
- User logs in and grants permission

**Browser shows:**
```
Authorization URL:
https://accounts.google.com/o/oauth2/auth?
  response_type=code&
  client_id=20639107758-jb7ukf9j3o9ql8q771m3pi17ve8eb6oo.apps.googleusercontent.com&
  redirect_uri=http://localhost:54194/&
  scope=https://www.googleapis.com/auth/gmail.readonly&
  ...
```

**Sub-step 3: Save token.json for future use**
```python
with open('token.json', 'w') as token:
    token.write(creds.to_json())
```

**Result:** Token saved, next searches won't need browser login

**Sub-step 4: Build Gmail service**
```python
self.gmail_service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
return {"status": "ok", "message": "Successfully authenticated..."}
```

---

#### Step 3d: Execute Gmail Search

Once authenticated, the `search_gmail()` method executes:

```python
results = self.gmail_service.users().messages().list(
    userId='me',
    q=query,           # e.g., 'from:equitable'
    maxResults=5
).execute()

messages = results.get('messages', [])
total = results.get('resultSizeEstimate', 0)
```

**What happens:**
- Calls Gmail API with search query
- Returns message IDs and total count

#### Step 3e: Fetch Email Details

For each message found:

```python
for msg in messages:
    msg_data = self.gmail_service.users().messages().get(
        userId='me',
        id=msg['id'],
        format='metadata',
        metadataHeaders=['From', 'Subject', 'Date']
    ).execute()
    
    headers = {h['name']: h['value'] for h in msg_data['payload'].get('headers', [])}
    email_details.append({
        "id": msg['id'],
        "from": headers.get('From', 'Unknown'),
        "subject": headers.get('Subject', '(No subject)'),
        "date": headers.get('Date', 'Unknown')
    })
```

**What happens:**
- Retrieves metadata for each email
- Extracts From, Subject, Date headers
- Builds list of email details

#### Step 3f: Return Results

```python
return {
    "status": "ok",
    "query": query,
    "total_results": total,
    "returned": len(email_details),
    "emails": email_details
}
```

---

## Example: Search Flow in Action

### Command
```powershell
cd c:\Users\dilip\Desktop\github_test2\test
python -c "from mcp_server import MCPServer; srv=MCPServer(); print(srv.search_gmail('from:equitable', max_results=5))"
```

### Timeline

1. **T+0s:** Python imports `mcp_server.py`
   - Gmail libraries checked
   - GMAIL_API_AVAILABLE = True

2. **T+1s:** MCPServer instance created
   - Tools registered
   - gmail_service = None

3. **T+2s:** search_gmail() called
   - Checks GMAIL_API_AVAILABLE (ok)
   - Calls authenticate_gmail()

4. **T+3s:** authenticate_gmail() checks for token.json
   - First time: not found
   - Starts OAuth flow

5. **T+4s:** Browser opens with OAuth URL
   - Shows Google login screen
   - User logs in
   - User grants permission

6. **T+10s:** OAuth completes
   - Access token received
   - token.json saved
   - gmail_service initialized

7. **T+11s:** Gmail search executed
   - Query: 'from:equitable'
   - Returns: 201 total results

8. **T+12s:** Email details fetched
   - 5 emails retrieved
   - From, Subject, Date extracted

9. **T+13s:** Results returned to user

```json
{
  "status": "ok",
  "query": "from:equitable",
  "total_results": 201,
  "returned": 5,
  "emails": [
    {
      "id": "19e1e419eee14015",
      "from": "Equitable <no_reply@equitable.ca>",
      "subject": "Your Equitable application is ready...",
      "date": "Tue, 12 May 2026 22:14:37 +0000"
    },
    ...
  ]
}
```

---

## Directory Structure

```
c:\Users\dilip\Desktop\github_test2\test\
├── mcp_server.py              # Main server with Gmail tools
├── credentials.json           # OAuth client credentials (from Google Cloud)
├── token.json                 # Generated after first OAuth login
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── GMAIL_API_SETUP.md         # Setup instructions
├── HOW_IT_WORKS.md            # This file
├── .mcp.json                  # MCP server configuration
└── .git/                      # Version control
```

---

## Key Concepts Explained

### OAuth 2.0 Flow
- **Credentials.json:** Contains app's client ID and secret
- **Token.json:** Contains user's access token
- **Browser login:** User authorizes app to access their Gmail
- **Scope:** `gmail.readonly` means read-only access (can't delete/send)

### Gmail API Calls
1. **List messages:** Search Gmail by query, get message IDs
2. **Get message:** Retrieve metadata/content for specific message
3. **Headers:** From, Subject, Date are metadata fields

### Caching
- First search: Requires OAuth browser login
- Subsequent searches: Uses `token.json` (instant, no browser)
- Token auto-refreshes if expired

---

## Gmail Search Query Examples

| Query | Result |
|-------|--------|
| `from:equitable` | Emails from Equitable |
| `after:2026-05-12` | Emails after May 12, 2026 |
| `label:spam` | Emails in Spam folder |
| `is:unread` | Unread emails |
| `subject:important` | Subject contains "important" |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `credentials.json not found` | Download from Google Cloud Console Credentials page |
| `ModuleNotFoundError: No module named 'google'` | Run: `pip install -r requirements.txt` |
| `Access blocked: www.gmail.com not verified` | Add yourself as test user in OAuth consent screen |
| Browser won't open | Check firewall, try opening URL manually |
| No `token.json` after login | Check Google Cloud project matches your Gmail account |

---

## Summary

**The complete flow:**

1. **Setup phase:** Create Google Cloud project, enable Gmail API, create OAuth credentials
2. **Installation phase:** Install Python dependencies
3. **Configuration phase:** Place credentials.json in project folder
4. **Runtime phase:**
   - First search: OAuth login → save token.json → search
   - Subsequent searches: Use token.json → instant search
5. **Result phase:** Email list returned with From, Subject, Date

Each search call returns matching emails with metadata. The token.json file makes subsequent searches instant.

