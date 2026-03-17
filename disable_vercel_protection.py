"""
Script to disable Vercel deployment protection using the Vercel REST API.
"""
import os
import glob
import json
import requests

# Find auth token from Vercel CLI config
search_paths = [
    os.path.expandvars(r'%APPDATA%\com.vercel.cli\auth.json'),
    os.path.expandvars(r'%LOCALAPPDATA%\com.vercel.cli\auth.json'),
    os.path.expanduser(r'~\.config\vercel\auth.json'),
    os.path.expanduser(r'~\AppData\Roaming\vercel\auth.json'),
]

token = None
for path in search_paths:
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
            token = data.get('token') or data.get('_')
            print(f"Found token at: {path}")
            break

# Also try searching broadly
if not token:
    for pattern in [r'C:\Users\Admin\**\auth.json']:
        for path in glob.glob(pattern, recursive=True):
            if 'vercel' in path.lower():
                try:
                    with open(path) as f:
                        data = json.load(f)
                        if 'token' in data:
                            token = data['token']
                            print(f"Found token at: {path}")
                            break
                except:
                    pass

if not token:
    print("ERROR: Could not find Vercel auth token automatically.")
    print("Please go to https://vercel.com/account/tokens, create a token,")
    print("and set it as VERCEL_TOKEN environment variable.")
    token = os.environ.get('VERCEL_TOKEN')

if token:
    print(f"Using token: {token[:10]}...")
    project_id = "prj_dtJHwXQM5uEPz6vJasYYuaMFmHcl"
    team_id = "team_QEZsqzph79sCGm3UA3wNbA1H"
    
    # First, get current project info to see fields
    get_url = f"https://api.vercel.com/v9/projects/{project_id}?teamId={team_id}"
    headers = {"Authorization": f"Bearer {token}"}
    get_resp = requests.get(get_url, headers=headers)
    project_data = get_resp.json()
    print("Project Data Keys:", list(project_data.keys()))
    
    # Try to find protection related fields
    protection_fields = {k: v for k, v in project_data.items() if 'protect' in k.lower() or 'auth' in k.lower()}
    print("Protection Fields Found:", protection_fields)

    # Update with suspected correct fields
    patch_url = f"https://api.vercel.com/v9/projects/{project_id}?teamId={team_id}"
    patch_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Standard fields to try and disable
    payload = {}
    if 'passwordProtection' in project_data:
        payload['passwordProtection'] = None
    if 'ssoProtection' in project_data:
        payload['ssoProtection'] = None
    
    # If no obvious fields, let's try setting things to null/false
    if not payload:
        payload = {
            "passwordProtection": None,
            "ssoProtection": None
        }

    print(f"Sending PATCH with payload: {payload}")
    resp = requests.patch(patch_url, json=payload, headers=patch_headers)
    print(f"API Response ({resp.status_code}): {resp.text[:500]}")
    
    if resp.status_code == 200:
        print("SUCCESS: Project settings updated potentially disabling protection.")
    else:
        print("ERROR: Failed to update project settings.")
else:
    print("No token found. Cannot proceed.")
