# Gmail API Setup Guide

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter project name: `Gmail MCP Server`
5. Click "CREATE"

## Step 2: Enable Gmail API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on **Gmail API**
4. Click the **ENABLE** button

## Step 3: Create OAuth Consent Screen and OAuth 2.0 Credentials

1. In the Google Cloud Console, go to **APIs & Services** > **OAuth consent screen**.
2. Select the user type:
   - **Internal** if only your organization will use it
   - **External** if you or others outside your organization will use it
3. Fill in the required fields:
   - **App name**
   - **User support email**
   - **Developer contact email**
4. Save and continue through the consent screen wizard. You can leave optional branding fields blank for a simple setup.
5. After the consent screen is configured, go to **APIs & Services** > **Credentials**.
6. Click **+ CREATE CREDENTIALS** > **OAuth client ID**.
7. Choose **Desktop application**.
8. Click **CREATE**.
9. In the dialog that appears, click **DOWNLOAD JSON** to save the OAuth client credentials file.
10. Rename the downloaded file to `credentials.json` and place it in your project directory.

## Step 4: Configure Your MCP Server

Place the `credentials.json` file in the same directory as `mcp_server.py`:

```
c:\Users\dilip\Desktop\github_test2\test\
├── mcp_server.py
├── credentials.json (download from Google Cloud)
└── token.json (auto-generated on first auth)
```

## Step 5: Install Required Packages

```powershell
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## Step 6: Usage

### First Time Authentication

When you call a Gmail search function for the first time, a browser window will open asking you to authorize the app. Click "Allow" to grant permissions.

### Search Examples

Search for "ultimatix ppt":
```json
{
  "tool": "search_gmail",
  "args": {
    "query": "ultimatix ppt"
  }
}
```

Search for spam emails:
```json
{
  "tool": "search_gmail",
  "args": {
    "query": "label:spam"
  }
}
```

Search for unread emails:
```json
{
  "tool": "search_gmail",
  "args": {
    "query": "is:unread"
  }
}
```

## Gmail Search Syntax

- `label:spam` - Search in spam folder
- `is:unread` - Search for unread emails
- `is:starred` - Search for starred emails
- `from:sender@example.com` - Search by sender
- `subject:keyword` - Search in subject
- `before:2024-01-01` - Search before a date
- `after:2024-01-01` - Search after a date

## Troubleshooting

**"credentials.json not found"**
- Download the OAuth credentials JSON file from Google Cloud Console
- Save it as `credentials.json` in the same directory as `mcp_server.py`

**"ModuleNotFoundError: No module named 'google'"**
- Run: `pip install google-api-python-client google-auth-oauthlib google-auth-httplib2`

**"Invalid client" error**
- Make sure you downloaded the correct credentials.json
- Try deleting `token.json` and re-authenticating
