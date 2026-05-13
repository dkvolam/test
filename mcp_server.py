#!/usr/bin/env python3
"""
MCP Server for file organization and temp file cleanup
Provides tools to:
- Find temp files (.tmp, .temp, etc.)
- Delete temp files
- Organize files by type
- Get storage statistics
"""

import os
import sys
import json
import shutil
import webbrowser
from pathlib import Path
from typing import Any

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials as OAuth2Credentials
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

# MCP SDK - simplified implementation
class MCPServer:
    def __init__(self):
        self.tools = {}
        self.gmail_service = None
        self.register_tools()

    def register_tools(self):
        """Register available tools"""
        self.tools = {
            "find_temp_files": self.find_temp_files,
            "delete_temp_files": self.delete_temp_files,
            "organize_files": self.organize_files,
            "get_storage_stats": self.get_storage_stats,
            "cleanup_directory": self.cleanup_directory,
            "open_gmail": self.open_gmail,
            "search_gmail": self.search_gmail,
        }

    def find_temp_files(self, directory: str = None, patterns: list = None) -> dict:
        """Find temporary files matching patterns"""
        if directory is None:
            directory = os.path.expanduser("~")
        if patterns is None:
            patterns = [".tmp", ".temp", "~"]

        directory = os.path.expanduser(directory)
        if not os.path.exists(directory):
            return {"error": f"Directory not found: {directory}"}

        temp_files = []
        total_size = 0

        try:
            for root, dirs, files in os.walk(directory):
                # Skip hidden/system folders to avoid permissions issues
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    for pattern in patterns:
                        if file.endswith(pattern) or file.startswith(pattern):
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                total_size += size
                                temp_files.append({
                                    "path": file_path,
                                    "size": size,
                                    "pattern": pattern
                                })
                            except OSError:
                                pass
                            break
        except PermissionError as e:
            return {"error": f"Permission denied: {e}", "files": temp_files, "total_size": total_size}

        return {
            "count": len(temp_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": temp_files,
            "directory": directory
        }

    def delete_temp_files(self, directory: str = None, patterns: list = None, dry_run: bool = True) -> dict:
        """Delete temporary files"""
        if directory is None:
            directory = os.path.expanduser("~")
        if patterns is None:
            patterns = [".tmp", ".temp"]

        find_result = self.find_temp_files(directory, patterns)
        if "error" in find_result:
            return find_result

        deleted = []
        failed = []

        for file_info in find_result.get("files", []):
            file_path = file_info["path"]
            try:
                if not dry_run:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                deleted.append({
                    "path": file_path,
                    "size": file_info["size"],
                    "status": "deleted" if not dry_run else "would_delete"
                })
            except Exception as e:
                failed.append({"path": file_path, "error": str(e)})

        return {
            "dry_run": dry_run,
            "deleted_count": len(deleted),
            "failed_count": len(failed),
            "total_freed_mb": round(sum(f["size"] for f in deleted) / (1024 * 1024), 2),
            "deleted": deleted,
            "failed": failed
        }

    def open_gmail(self, url: str = "https://mail.google.com/") -> dict:
        """Open Gmail in the default browser."""
        try:
            webbrowser.open(url, new=2)
            return {"status": "ok", "url": url, "message": "Opened Gmail in browser"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def authenticate_gmail(self) -> dict:
        """Authenticate with Gmail API using OAuth 2.0."""
        if not GMAIL_API_AVAILABLE:
            return {"error": "Gmail API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"}
        
        try:
            credentials_file = "credentials.json"
            token_file = "token.json"
            
            # Load existing token if available
            if os.path.exists(token_file):
                creds = OAuth2Credentials.from_authorized_user_file(token_file)
                self.gmail_service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
                return {"status": "ok", "message": "Authenticated using saved token"}
            
            # Create new OAuth flow
            if not os.path.exists(credentials_file):
                return {"error": f"credentials.json not found. Download OAuth credentials from Google Cloud Console and save as {credentials_file}"}
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save token for future use
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
            return {"status": "ok", "message": "Successfully authenticated with Gmail API"}
        
        except Exception as e:
            return {"error": str(e)}

    def search_gmail(self, query: str = "", max_results: int = 10) -> dict:
        """Search Gmail for messages matching the query."""
        if not GMAIL_API_AVAILABLE:
            return {"error": "Gmail API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"}
        
        try:
            # Authenticate if not already done
            if self.gmail_service is None:
                auth_result = self.authenticate_gmail()
                if "error" in auth_result:
                    return auth_result
            
            # Execute search
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=min(max_results, 100)
            ).execute()
            
            messages = results.get('messages', [])
            total = results.get('resultSizeEstimate', 0)
            
            email_details = []
            for msg in messages:
                try:
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
                except Exception as e:
                    email_details.append({"id": msg['id'], "error": str(e)})
            
            return {
                "status": "ok",
                "query": query,
                "total_results": total,
                "returned": len(email_details),
                "emails": email_details
            }
        
        except Exception as e:
            return {"error": str(e)}

    def organize_files(self, directory: str, group_by: str = "extension") -> dict:
        """Organize files by extension or type"""
        directory = os.path.expanduser(directory)
        if not os.path.exists(directory):
            return {"error": f"Directory not found: {directory}"}

        organized = {}

        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if group_by == "extension":
                        key = os.path.splitext(file)[1] or "no_extension"
                    else:
                        key = "files"

                    if key not in organized:
                        organized[key] = []
                    
                    try:
                        size = os.path.getsize(file_path)
                        organized[key].append({
                            "path": file_path,
                            "name": file,
                            "size": size
                        })
                    except OSError:
                        pass
        except PermissionError as e:
            return {"error": f"Permission denied: {e}", "organized": organized}

        return {
            "directory": directory,
            "group_by": group_by,
            "groups": len(organized),
            "organized": organized
        }

    def get_storage_stats(self, directory: str = None) -> dict:
        """Get storage statistics for a directory"""
        if directory is None:
            directory = os.path.expanduser("~")
        
        directory = os.path.expanduser(directory)
        if not os.path.exists(directory):
            return {"error": f"Directory not found: {directory}"}

        total_size = 0
        file_count = 0
        dir_count = 0

        try:
            for root, dirs, files in os.walk(directory):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                dir_count += len(dirs)
                file_count += len(files)
                
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except OSError:
                        pass
        except PermissionError as e:
            return {"error": f"Permission denied: {e}"}

        return {
            "directory": directory,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "file_count": file_count,
            "dir_count": dir_count
        }

    def cleanup_directory(self, directory: str) -> dict:
        """Complete cleanup: organize + remove temps + stats"""
        directory = os.path.expanduser(directory)
        
        stats_before = self.get_storage_stats(directory)
        temp_cleanup = self.delete_temp_files(directory, dry_run=False)
        organized = self.organize_files(directory)
        stats_after = self.get_storage_stats(directory)

        return {
            "directory": directory,
            "stats_before": stats_before,
            "stats_after": stats_after,
            "space_freed_mb": round((stats_before.get("total_size_bytes", 0) - stats_after.get("total_size_bytes", 0)) / (1024 * 1024), 2),
            "temp_cleanup": temp_cleanup,
            "organized": organized
        }

    def process_request(self, request: dict) -> dict:
        """Process incoming request"""
        tool_name = request.get("tool")
        args = request.get("args", {})

        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = self.tools[tool_name](**args)
            return result
        except Exception as e:
            return {"error": str(e)}

    def list_tools(self) -> dict:
        """List available tools"""
        return {
            "tools": list(self.tools.keys()),
            "descriptions": {
                "find_temp_files": "Find temporary files by pattern",
                "delete_temp_files": "Delete temporary files (with dry-run option)",
                "organize_files": "Organize files by extension",
                "get_storage_stats": "Get directory storage statistics",
                "cleanup_directory": "Complete cleanup operation",
                "open_gmail": "Open Gmail in default browser",
                "search_gmail": "Search Gmail messages by query (requires OAuth setup)"
            }
        }


def main():
    """Main server loop"""
    server = MCPServer()
    
    print("File Organization MCP Server started", file=sys.stderr)
    print(json.dumps({"status": "ready", "tools": list(server.tools.keys())}))
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line)
                
                if request.get("method") == "list_tools":
                    response = server.list_tools()
                else:
                    response = server.process_request(request)
                
                print(json.dumps(response))
            except json.JSONDecodeError as e:
                print(json.dumps({"error": f"Invalid JSON: {e}"}))
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
