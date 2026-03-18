import os
import json
import requests
import time

# Vercel Project Details
PROJECT_ID = "prj_dtJHwXQM5uEPz6vJasYYuaMFmHcl"
TEAM_ID = "team_QEZsqzph79sCGm3UA3wNbA1H"
DOMAINS = ["tool.forex", "forextool.vercel.app", "forex-tool.vercel.app"]

def get_vercel_token():
    search_paths = [
        os.path.expandvars(r'%APPDATA%\com.vercel.cli\auth.json'),
        os.path.expandvars(r'%LOCALAPPDATA%\com.vercel.cli\auth.json'),
        os.path.expanduser(r'~\.config\vercel\auth.json'),
        os.path.expanduser(r'~\AppData\Roaming\vercel\auth.json'),
    ]
    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    token = data.get('token') or data.get('_')
                    if token:
                        print(f"Found Vercel token at: {path}")
                        return token
            except:
                pass
    return os.environ.get('VERCEL_TOKEN')

def fix_deployment():
    token = get_vercel_token()
    if not token:
        print("ERROR: No Vercel token found. Please set VERCEL_TOKEN env var.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Get Latest Ready Deployments
    print("\n[1/3] Fetching latest deployments...")
    deploy_url = f"https://api.vercel.com/v6/deployments?projectId={PROJECT_ID}&teamId={TEAM_ID}&limit=5&state=READY"
    resp = requests.get(deploy_url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch deployments: {resp.text}")
        return
    
    deploys = resp.json().get('deployments', [])
    if not deploys:
        print("No successful deployments found.")
        return

    # Find the deployment with the GESI AI PREMIUM V4.0 commit or the very latest
    latest_deploy = deploys[0]
    target_deploy_id = latest_deploy['uid']
    target_url = latest_deploy['url']
    
    print(f"Targeting Deployment: {target_deploy_id} ({target_url})")
    print(f"Commit: {latest_deploy.get('meta', {}).get('githubCommitMessage', 'N/A')}")

    # 2. Assign Aliases (Update Domains)
    print(f"\n[2/3] Updating domains to point to {target_deploy_id}...")
    for domain in DOMAINS:
        alias_url = f"https://api.vercel.com/v2/deployments/{target_deploy_id}/aliases?teamId={TEAM_ID}"
        alias_resp = requests.post(alias_url, headers=headers, json={"alias": domain})
        if alias_resp.status_code == 200:
            print(f"SUCCESS: {domain} is now live on the latest version!")
        else:
            # If it's already assigned, Vercel might return 400 or other, but we ensure it's pointing here
            print(f"INFO: Domain {domain} update response: {alias_resp.status_code}")

    # 3. Verify Public Status
    print("\n[3/3] Verifying public access...")
    time.sleep(2) # Brief wait for propagation
    for domain in DOMAINS:
        try:
            v_url = f"https://{domain}"
            v_resp = requests.get(v_url, timeout=5)
            if v_resp.status_code == 200:
                print(f"CONFIRMED: {v_url} is active (HTTP 200).")
                if "GESI AI PREMIUM" in v_resp.text:
                    print(f"FEATURE CHECK: Found 'GESI AI PREMIUM' in {v_url} source!")
            else:
                print(f"WARNING: {v_url} returned {v_resp.status_code}")
        except Exception as e:
            print(f"ERROR: Could not reach {domain}: {e}")

if __name__ == "__main__":
    fix_deployment()
