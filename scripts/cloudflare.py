#!/usr/bin/env python3
"""
Cloudflare API CLI - Manage zones, DNS records, and Pages custom domains.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Load environment variables from .env file
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    # Handle export statements
                    if line.startswith("export "):
                        line = line[7:]
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()

load_env()

# Configuration
ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
API_KEY = os.environ.get("CLOUDFLARE_API_KEY", "")
EMAIL = os.environ.get("CLOUDFLARE_EMAIL", "")
BASE_URL = os.environ.get("CLOUDFLARE_BASE_URL", "https://api.cloudflare.com/client/v4")

def get_headers():
    """Get authorization headers."""
    if API_TOKEN:
        return {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
    elif API_KEY and EMAIL:
        return {
            "X-Auth-Key": API_KEY,
            "X-Auth-Email": EMAIL,
            "Content-Type": "application/json"
        }
    else:
        raise ValueError("No API credentials configured")

def api_request(method, endpoint, data=None):
    """Make an API request to Cloudflare."""
    url = f"{BASE_URL}{endpoint}"
    headers = get_headers()

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            return json.loads(error_body)
        except:
            return {"success": False, "errors": [{"message": error_body}]}

def print_json(data):
    """Pretty print JSON."""
    print(json.dumps(data, indent=2))

# Permission requirements by feature
PERMISSION_HINTS = {
    "email/routing/rules": {
        "name": "Email Routing Rules",
        "permission": "Zone > Email Routing Rules > Edit",
        "scope": "zone"
    },
    "email/routing/addresses": {
        "name": "Email Routing Addresses",
        "permission": "Account > Email Routing Addresses > Edit",
        "scope": "account"
    },
    "email/routing/enable": {
        "name": "Email Routing Settings",
        "permission": "Zone > Email Routing Rules > Edit",
        "scope": "zone"
    },
    "email/routing": {
        "name": "Email Routing",
        "permission": "Zone > Email Routing Rules > Read",
        "scope": "zone"
    },
    "dns_records": {
        "name": "DNS Records",
        "permission": "Zone > DNS > Edit",
        "scope": "zone"
    },
    "pages/projects": {
        "name": "Cloudflare Pages",
        "permission": "Account > Cloudflare Pages > Edit",
        "scope": "account"
    },
    "workers/scripts": {
        "name": "Workers",
        "permission": "Account > Worker Scripts > Edit",
        "scope": "account"
    },
    "r2/buckets": {
        "name": "R2 Storage",
        "permission": "Account > R2 Storage > Edit",
        "scope": "account"
    },
    "zones": {
        "name": "Zones",
        "permission": "Zone > Zone > Read (or Zone > Zone Settings > Edit)",
        "scope": "zone"
    },
    "storage/kv": {
        "name": "Workers KV Storage",
        "permission": "Account > Workers KV Storage > Edit",
        "scope": "account"
    }
}

def get_permission_hint(endpoint):
    """Get permission hint based on endpoint."""
    for pattern, hint in PERMISSION_HINTS.items():
        if pattern in endpoint:
            return hint
    return None

def handle_api_error(result, endpoint=""):
    """Check for auth errors and print helpful guidance."""
    if not result.get("success", True):
        errors = result.get("errors", [])
        for error in errors:
            code = error.get("code")
            message = error.get("message", "")

            # Authentication/authorization errors
            if code == 10000 or "authentication" in message.lower() or "authorization" in message.lower():
                hint = get_permission_hint(endpoint)

                print(f"\n{'='*60}")
                print(f"  ❌ API Token Permission Error")
                print(f"{'='*60}\n")

                if hint:
                    print(f"  Feature: {hint['name']}")
                    print(f"  Required: {hint['permission']}")
                    print()

                print(f"  Fix: Update your API token at:")
                print(f"  https://dash.cloudflare.com/profile/api-tokens")
                print()
                print(f"  1. Click 'Edit' on your token")
                print(f"  2. Under 'Permissions', add the required permission")
                print(f"  3. Save and update ~/.claude/skills/cloudflare-skill/.env")
                print()
                return True

            # Token not found
            elif code == 10001 or "token" in message.lower():
                print(f"\n{'='*60}")
                print(f"  ❌ API Token Not Found or Invalid")
                print(f"{'='*60}\n")
                print(f"  Check ~/.claude/skills/cloudflare-skill/.env")
                print(f"  Ensure CLOUDFLARE_API_TOKEN is set correctly.")
                print()
                print(f"  Get a token at: https://dash.cloudflare.com/profile/api-tokens")
                print()
                return True

            # Resource not found (wrong zone/account)
            elif code == 10002:
                print(f"\n{'='*60}")
                print(f"  ❌ Resource Not Found")
                print(f"{'='*60}\n")
                print(f"  The zone or resource doesn't exist, or your token")
                print(f"  doesn't have access to it.")
                print()
                return True

            # Duplicate resource
            elif code == 2014:
                print(f"\n  ⚠️  Rule already exists (duplicate)")
                return True

    return False

# ============== ZONES ==============

def zones_list():
    """List all zones in the account."""
    result = api_request("GET", "/zones")
    print_json(result)

def zones_get(zone_id):
    """Get details for a specific zone."""
    result = api_request("GET", f"/zones/{zone_id}")
    print_json(result)

def zones_create(domain, zone_type="full"):
    """Create a new zone."""
    data = {
        "account": {"id": ACCOUNT_ID},
        "name": domain,
        "type": zone_type
    }
    result = api_request("POST", "/zones", data)
    print_json(result)

def zones_delete(zone_id):
    """Delete a zone."""
    result = api_request("DELETE", f"/zones/{zone_id}")
    print_json(result)

# ============== DNS RECORDS ==============

def dns_list(zone_id):
    """List all DNS records for a zone."""
    result = api_request("GET", f"/zones/{zone_id}/dns_records")
    print_json(result)

def dns_create(zone_id, record_type, name, content, ttl=1, proxied=False, priority=None):
    """Create a DNS record."""
    data = {
        "type": record_type,
        "name": name,
        "content": content,
        "ttl": int(ttl),
        "proxied": proxied
    }
    if priority is not None:
        data["priority"] = int(priority)
    result = api_request("POST", f"/zones/{zone_id}/dns_records", data)
    print_json(result)

def dns_update(zone_id, record_id, record_type, name, content, ttl=1, proxied=False, priority=None):
    """Update a DNS record."""
    data = {
        "type": record_type,
        "name": name,
        "content": content,
        "ttl": int(ttl),
        "proxied": proxied
    }
    if priority is not None:
        data["priority"] = int(priority)
    result = api_request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", data)
    print_json(result)

def dns_delete(zone_id, record_id):
    """Delete a DNS record."""
    result = api_request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")
    print_json(result)

# ============== PAGES PROJECTS ==============

def pages_list():
    """List all Pages projects."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects")
    print_json(result)

def pages_get(project_name):
    """Get details for a Pages project."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}")
    print_json(result)

def pages_create(project_name, production_branch="main"):
    """Create a new Pages project."""
    data = {
        "name": project_name,
        "production_branch": production_branch
    }
    result = api_request("POST", f"/accounts/{ACCOUNT_ID}/pages/projects", data)
    print_json(result)

def pages_connect_git(project_name, owner, repo_name, production_branch="main"):
    """Connect a GitHub repo to a Pages project."""
    data = {
        "source": {
            "type": "github",
            "config": {
                "owner": owner,
                "repo_name": repo_name,
                "production_branch": production_branch,
                "pr_comments_enabled": True,
                "deployments_enabled": True
            }
        },
        "build_config": {
            "build_command": "pnpm build",
            "destination_dir": "dist",
            "root_dir": ""
        }
    }
    result = api_request("PATCH", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}", data)
    print_json(result)

def pages_update_build(project_name, build_command, destination_dir, root_dir=""):
    """Update build configuration for a Pages project."""
    data = {
        "build_config": {
            "build_command": build_command,
            "destination_dir": destination_dir,
            "root_dir": root_dir
        }
    }
    result = api_request("PATCH", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}", data)
    print_json(result)

# ============== PAGES CUSTOM DOMAINS ==============

def pages_domains_list(project_name):
    """List custom domains for a Pages project."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}/domains")
    print_json(result)

def pages_domains_add(project_name, domain):
    """Add a custom domain to a Pages project."""
    data = {"name": domain}
    result = api_request("POST", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}/domains", data)
    print_json(result)

def pages_domains_delete(project_name, domain):
    """Remove a custom domain from a Pages project."""
    result = api_request("DELETE", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}/domains/{domain}")
    print_json(result)

# ============== PAGES ENVIRONMENT VARIABLES ==============

def pages_env_list(project_name, environment="production"):
    """List environment variables for a Pages project."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}")
    if result.get("success") and result.get("result"):
        project = result["result"]
        deployment_configs = project.get("deployment_configs", {})
        env_config = deployment_configs.get(environment, {})
        env_vars = env_config.get("env_vars") or {}

        print(f"\n{'='*60}")
        print(f"  Environment Variables: {project_name} ({environment})")
        print(f"{'='*60}\n")

        if not env_vars:
            print("  No environment variables configured.\n")
            return

        for name, config in env_vars.items():
            if isinstance(config, dict):
                value = config.get("value", "(secret)")
                var_type = config.get("type", "plain_text")
                if var_type == "secret_text":
                    print(f"  {name} = (secret)")
                else:
                    print(f"  {name} = {value}")
            else:
                print(f"  {name} = {config}")
        print()
    else:
        print_json(result)

def pages_env_set(project_name, var_name, var_value, environment="production", secret=False):
    """Set an environment variable for a Pages project."""
    # First get existing env vars
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}")
    if not result.get("success"):
        print_json(result)
        return

    project = result["result"]
    deployment_configs = project.get("deployment_configs", {})
    env_config = deployment_configs.get(environment, {})
    existing_vars = env_config.get("env_vars") or {}

    # Add/update the variable
    if secret:
        existing_vars[var_name] = {"type": "secret_text", "value": var_value}
    else:
        existing_vars[var_name] = {"type": "plain_text", "value": var_value}

    # Update the project
    data = {
        "deployment_configs": {
            environment: {
                "env_vars": existing_vars
            }
        }
    }

    result = api_request("PATCH", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}", data)
    if result.get("success"):
        var_type = "secret" if secret else "plain"
        print(f"\n  Set {var_name} ({var_type}) for {project_name} ({environment})\n")
    else:
        print_json(result)

def pages_env_delete(project_name, var_name, environment="production"):
    """Delete an environment variable from a Pages project."""
    # First get existing env vars
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}")
    if not result.get("success"):
        print_json(result)
        return

    project = result["result"]
    deployment_configs = project.get("deployment_configs", {})
    env_config = deployment_configs.get(environment, {})
    existing_vars = env_config.get("env_vars") or {}

    if var_name not in existing_vars:
        print(f"\n  Variable {var_name} not found.\n")
        return

    # Remove the variable
    del existing_vars[var_name]

    # Update the project
    data = {
        "deployment_configs": {
            environment: {
                "env_vars": existing_vars
            }
        }
    }

    result = api_request("PATCH", f"/accounts/{ACCOUNT_ID}/pages/projects/{project_name}", data)
    if result.get("success"):
        print(f"\n  Deleted {var_name} from {project_name} ({environment})\n")
    else:
        print_json(result)

# ============== WORKERS ==============

def workers_list():
    """List all Workers scripts."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/workers/scripts")
    if result.get("success") and result.get("result"):
        print(f"\n{'='*60}")
        print(f"  Workers Scripts")
        print(f"{'='*60}\n")
        for w in result["result"]:
            print(f"  {w['id']}")
            if w.get('modified_on'):
                print(f"    Modified: {w['modified_on']}")
        print()
    else:
        print_json(result)

def workers_get(name):
    """Get Worker script details."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/workers/scripts/{name}")
    print_json(result)

def workers_subdomain(new_subdomain=None):
    """Get or set account's workers.dev subdomain."""
    if new_subdomain:
        # Change subdomain
        result = api_request("PUT", f"/accounts/{ACCOUNT_ID}/workers/subdomain", {"subdomain": new_subdomain})
        if result.get("success"):
            print(f"\nSubdomain changed to: {new_subdomain}.workers.dev\n")
            return new_subdomain
        else:
            print_json(result)
            return None
    else:
        # Get current subdomain
        result = api_request("GET", f"/accounts/{ACCOUNT_ID}/workers/subdomain")
        if result.get("success") and result.get("result"):
            subdomain = result["result"].get("subdomain", "")
            print(f"\nYour workers.dev subdomain: {subdomain}.workers.dev\n")
            return subdomain
        else:
            print_json(result)
            return None

def workers_deploy(name, script_content, r2_bindings=None):
    """Deploy a Worker script with optional R2 bindings."""
    import urllib.request
    import json

    url = f"{BASE_URL}/accounts/{ACCOUNT_ID}/workers/scripts/{name}"
    headers = get_headers()

    # Build metadata
    metadata = {
        "main_module": "worker.js",
        "compatibility_date": "2024-01-01"
    }

    if r2_bindings:
        metadata["bindings"] = [
            {"type": "r2_bucket", "name": b["name"], "bucket_name": b["bucket_name"]}
            for b in r2_bindings
        ]

    # Create multipart form data
    boundary = "----CloudflareWorkerBoundary"

    body_parts = []

    # Metadata part
    body_parts.append(f'--{boundary}')
    body_parts.append('Content-Disposition: form-data; name="metadata"; filename="metadata.json"')
    body_parts.append('Content-Type: application/json')
    body_parts.append('')
    body_parts.append(json.dumps(metadata))

    # Script part
    body_parts.append(f'--{boundary}')
    body_parts.append('Content-Disposition: form-data; name="worker.js"; filename="worker.js"')
    body_parts.append('Content-Type: application/javascript+module')
    body_parts.append('')
    body_parts.append(script_content)

    body_parts.append(f'--{boundary}--')

    body = '\r\n'.join(body_parts).encode('utf-8')

    headers_copy = dict(headers)
    headers_copy['Content-Type'] = f'multipart/form-data; boundary={boundary}'

    req = urllib.request.Request(url, data=body, headers=headers_copy, method="PUT")

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("success"):
                subdomain = workers_subdomain()
                if subdomain:
                    print(f"Worker deployed: https://{name}.{subdomain}.workers.dev")
            else:
                print_json(result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error: {error_body}")

def workers_delete(name):
    """Delete a Worker script."""
    result = api_request("DELETE", f"/accounts/{ACCOUNT_ID}/workers/scripts/{name}")
    print_json(result)

def workers_deploy_media(name, bucket_name, api_key=None):
    """Deploy a media server worker with R2 binding and optional API key auth."""
    script = '''export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const key = url.pathname.slice(1);

    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, PUT, POST, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
        },
      });
    }

    const corsHeaders = { 'Access-Control-Allow-Origin': '*' };

    // Auth check for write operations
    if (request.method !== 'GET') {
      const authHeader = request.headers.get('Authorization') || '';
      const apiKeyHeader = request.headers.get('X-API-Key') || '';
      const validKey = env.API_KEY;

      if (validKey) {
        const providedKey = authHeader.replace('Bearer ', '') || apiKeyHeader;
        if (providedKey !== validKey) {
          return new Response(JSON.stringify({ error: 'Unauthorized' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
      }
    }

    if (request.method === 'GET') {
      if (!key) return new Response('media service', { headers: corsHeaders });
      const object = await env.BUCKET.get(key);
      if (!object) return new Response('Not found', { status: 404, headers: corsHeaders });
      const headers = new Headers(corsHeaders);
      object.writeHttpMetadata(headers);
      headers.set('etag', object.httpEtag);
      headers.set('Cache-Control', 'public, max-age=31536000');
      return new Response(object.body, { headers });
    }

    if (request.method === 'PUT' || request.method === 'POST') {
      if (!key) return new Response('Missing filename', { status: 400, headers: corsHeaders });
      const contentType = request.headers.get('Content-Type') || 'video/mp4';
      await env.BUCKET.put(key, request.body, { httpMetadata: { contentType } });
      return new Response(JSON.stringify({ success: true, key, url: `${url.origin}/${key}` }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    if (request.method === 'DELETE') {
      if (!key) return new Response('Missing filename', { status: 400, headers: corsHeaders });
      await env.BUCKET.delete(key);
      return new Response(JSON.stringify({ success: true }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders },
      });
    }

    return new Response('Method not allowed', { status: 405, headers: corsHeaders });
  },
};'''

    # Generate API key if not provided
    import secrets
    if not api_key:
        api_key = secrets.token_urlsafe(32)

    # Build multipart form
    boundary = "----WorkerBoundary"
    metadata = {
        "main_module": "worker.js",
        "compatibility_date": "2024-01-01",
        "bindings": [
            {"type": "r2_bucket", "name": "BUCKET", "bucket_name": bucket_name},
            {"type": "secret_text", "name": "API_KEY", "text": api_key}
        ]
    }

    body = f'''--{boundary}\r
Content-Disposition: form-data; name="metadata"; filename="metadata.json"\r
Content-Type: application/json\r
\r
{json.dumps(metadata)}\r
--{boundary}\r
Content-Disposition: form-data; name="worker.js"; filename="worker.js"\r
Content-Type: application/javascript+module\r
\r
{script}\r
--{boundary}--'''

    url = f"{BASE_URL}/accounts/{ACCOUNT_ID}/workers/scripts/{name}"
    headers = get_headers()
    headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

    req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers, method="PUT")

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("success"):
                # Get subdomain
                sub_result = api_request("GET", f"/accounts/{ACCOUNT_ID}/workers/subdomain")
                subdomain = sub_result.get("result", {}).get("subdomain", "")
                worker_url = f"https://{name}.{subdomain}.workers.dev"
                print(f"\nWorker deployed successfully!")
                print(f"URL: {worker_url}")
                print(f"\nAPI Key (save this!): {api_key}")
                print(f"\nUpload: curl -X PUT '{worker_url}/filename.mp4' -H 'X-API-Key: {api_key}' --data-binary @file.mp4")
                print(f"Access: {worker_url}/filename.mp4\n")
            else:
                print_json(result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            print_json(json.loads(error_body))
        except:
            print(f"Error: {error_body}")

def workers_domains_list():
    """List all Workers custom domains."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/workers/domains")
    print_json(result)

def workers_domains_add(hostname, zone_id, service, environment="production"):
    """Add a custom domain to a Worker."""
    data = {
        "hostname": hostname,
        "zone_id": zone_id,
        "service": service,
        "environment": environment
    }
    result = api_request("PUT", f"/accounts/{ACCOUNT_ID}/workers/domains", data)
    print_json(result)

# ============== R2 STORAGE ==============

def r2_list_buckets():
    """List all R2 buckets."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/r2/buckets")
    buckets = None
    if result.get("success"):
        # Handle nested format: result.result.buckets
        if result.get("result") and isinstance(result["result"], dict):
            buckets = result["result"].get("buckets", [])
        # Handle flat format: result.buckets
        elif result.get("buckets"):
            buckets = result["buckets"]

    if buckets:
        print(f"\n{'='*60}")
        print(f"  R2 Buckets")
        print(f"{'='*60}\n")
        for b in buckets:
            print(f"  {b['name']}")
            if b.get('creation_date'):
                print(f"    Created: {b['creation_date']}")
            if b.get('location'):
                print(f"    Location: {b['location']}")
        print()
    elif result.get("success"):
        print(f"\n  No R2 buckets found.\n")
    else:
        print_json(result)

def r2_create_bucket(name, location="wnam"):
    """Create an R2 bucket."""
    data = {"name": name}
    if location:
        data["locationHint"] = location
    result = api_request("POST", f"/accounts/{ACCOUNT_ID}/r2/buckets", data)
    if result.get("success"):
        print(f"\nR2 bucket created: {name}\n")
    else:
        print_json(result)

def r2_delete_bucket(name):
    """Delete an R2 bucket."""
    result = api_request("DELETE", f"/accounts/{ACCOUNT_ID}/r2/buckets/{name}")
    if result.get("success"):
        print(f"\nR2 bucket deleted: {name}\n")
    else:
        print_json(result)

def r2_get_bucket(name):
    """Get R2 bucket details."""
    result = api_request("GET", f"/accounts/{ACCOUNT_ID}/r2/buckets/{name}")
    print_json(result)

def r2_list_objects(bucket_name, prefix="", cursor="", limit=100):
    """List objects in an R2 bucket."""
    endpoint = f"/accounts/{ACCOUNT_ID}/r2/buckets/{bucket_name}/objects"
    params = []
    if prefix:
        params.append(f"prefix={prefix}")
    if cursor:
        params.append(f"cursor={cursor}")
    if limit:
        params.append(f"limit={limit}")
    if params:
        endpoint += "?" + "&".join(params)

    result = api_request("GET", endpoint)

    if result.get("success"):
        objects = result.get("result", [])
        if isinstance(objects, dict):
            objects = objects.get("objects", [])

        print(f"\n{'='*70}")
        print(f"  R2 Objects: {bucket_name}")
        if prefix:
            print(f"  Prefix: {prefix}")
        print(f"{'='*70}\n")

        if not objects:
            print("  (no objects found)\n")
            return

        def fmt_bytes(b):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if b < 1024:
                    return f"{b:.1f}{unit}"
                b /= 1024
            return f"{b:.1f}TB"

        print(f"  {'Size':>10}  {'Last Modified':<20}  Key")
        print(f"  {'-'*10}  {'-'*20}  {'-'*35}")

        for obj in objects:
            key = obj.get("key", "")
            size = fmt_bytes(obj.get("size", 0))
            last_mod = obj.get("last_modified", "")[:19] if obj.get("last_modified") else ""
            print(f"  {size:>10}  {last_mod:<20}  {key}")

        print(f"\n  Total: {len(objects)} objects")
        print()
    else:
        print_json(result)

# ============== KV STORAGE ==============

def kv_get_headers():
    """Get headers for KV API (prefers API Key over Token for broader permissions)."""
    if API_KEY and EMAIL:
        return {
            "X-Auth-Key": API_KEY,
            "X-Auth-Email": EMAIL,
            "Content-Type": "application/json"
        }
    elif API_TOKEN:
        return {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
    else:
        raise ValueError("No API credentials configured")

def kv_request(method, endpoint, data=None, raw_response=False):
    """Make KV API request using API Key (has broader permissions than token)."""
    url = f"{BASE_URL}{endpoint}"
    headers = kv_get_headers()

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            if raw_response:
                return response.read().decode()
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            result = json.loads(error_body)
            if not handle_api_error(result, endpoint):
                return result
            return result
        except:
            return {"success": False, "errors": [{"message": error_body}]}

def kv_namespaces_list():
    """List all KV namespaces."""
    result = kv_request("GET", f"/accounts/{ACCOUNT_ID}/storage/kv/namespaces")
    if result.get("success") and result.get("result"):
        print(f"\n{'='*60}")
        print(f"  KV Namespaces")
        print(f"{'='*60}\n")
        for ns in result["result"]:
            print(f"  {ns['title']}")
            print(f"    ID: {ns['id']}")
        print()
    else:
        print_json(result)

def kv_keys_list(namespace_id, prefix=""):
    """List keys in a KV namespace."""
    endpoint = f"/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{namespace_id}/keys"
    if prefix:
        endpoint += f"?prefix={prefix}"
    result = kv_request("GET", endpoint)
    if result.get("success") and "result" in result:
        keys = result["result"]
        print(f"\n{'='*60}")
        print(f"  KV Keys ({len(keys)} found)")
        print(f"{'='*60}\n")
        if not keys:
            print("  (empty)")
        for key in keys:
            exp = f" [expires: {key['expiration']}]" if key.get('expiration') else ""
            print(f"  {key['name']}{exp}")
        print()
    else:
        print_json(result)

def kv_get(namespace_id, key):
    """Get a value from KV."""
    endpoint = f"/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{namespace_id}/values/{key}"
    value = kv_request("GET", endpoint, raw_response=True)
    print(f"\n  Key: {key}")
    print(f"  Value: {value}\n")

def kv_put(namespace_id, key, value, expiration_ttl=None):
    """Put a value in KV."""
    endpoint = f"/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{namespace_id}/values/{key}"
    if expiration_ttl:
        endpoint += f"?expiration_ttl={expiration_ttl}"

    url = f"{BASE_URL}{endpoint}"
    headers = kv_get_headers()
    headers["Content-Type"] = "text/plain"

    req = urllib.request.Request(url, data=value.encode(), headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            if result.get("success"):
                print(f"\n  Stored: {key} = {value}\n")
            else:
                print_json(result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error: {error_body}")

def kv_delete(namespace_id, key):
    """Delete a key from KV."""
    endpoint = f"/accounts/{ACCOUNT_ID}/storage/kv/namespaces/{namespace_id}/values/{key}"
    result = kv_request("DELETE", endpoint)
    if result.get("success"):
        print(f"\n  Deleted: {key}\n")
    else:
        print_json(result)

# ============== ANALYTICS ==============

def graphql_request(query, variables=None):
    """Make a GraphQL request to Cloudflare Analytics."""
    url = "https://api.cloudflare.com/client/v4/graphql"
    headers = get_headers()

    data = {"query": query}
    if variables:
        data["variables"] = variables

    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            return json.loads(error_body)
        except:
            return {"errors": [{"message": error_body}]}

def get_zone_id(domain):
    """Get zone ID from domain name."""
    result = api_request("GET", f"/zones?name={domain}")
    if result.get("success") and result.get("result"):
        return result["result"][0]["id"]
    return None

def analytics_traffic(domain, days=7):
    """Get traffic overview for a domain."""
    from datetime import datetime, timedelta, timezone

    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    query = """
    query GetZoneAnalytics($zoneTag: String!, $since: String!, $until: String!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequests1dGroups(
            limit: 100
            filter: {date_geq: $since, date_leq: $until}
            orderBy: [date_ASC]
          ) {
            dimensions {
              date
            }
            sum {
              requests
              pageViews
              bytes
              cachedBytes
              threats
            }
            uniq {
              uniques
            }
          }
        }
      }
    }
    """

    variables = {
        "zoneTag": zone_id,
        "since": start.strftime("%Y-%m-%d"),
        "until": end.strftime("%Y-%m-%d")
    }

    result = graphql_request(query, variables)

    if result.get("errors"):
        print_json(result)
        return

    zones = result.get("data", {}).get("viewer", {}).get("zones", [])
    if not zones or not zones[0].get("httpRequests1dGroups"):
        print(f"No analytics data for {domain}")
        return

    groups = zones[0]["httpRequests1dGroups"]

    # Calculate totals
    total_requests = sum(g["sum"]["requests"] for g in groups)
    total_visitors = sum(g["uniq"]["uniques"] for g in groups)
    total_pageviews = sum(g["sum"]["pageViews"] for g in groups)
    total_bytes = sum(g["sum"]["bytes"] for g in groups)
    cached_bytes = sum(g["sum"]["cachedBytes"] for g in groups)
    total_threats = sum(g["sum"]["threats"] for g in groups)

    # Format bytes
    def fmt_bytes(b):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024:
                return f"{b:.2f} {unit}"
            b /= 1024
        return f"{b:.2f} PB"

    cache_rate = (cached_bytes / total_bytes * 100) if total_bytes > 0 else 0

    print(f"\n{'='*50}")
    print(f"  Traffic Summary: {domain}")
    print(f"  Last {days} days")
    print(f"{'='*50}\n")
    print(f"  Requests:      {total_requests:,}")
    print(f"  Unique visitors: {total_visitors:,}")
    print(f"  Page views:    {total_pageviews:,}")
    print(f"  Bandwidth:     {fmt_bytes(total_bytes)}")
    print(f"  Cached:        {fmt_bytes(cached_bytes)} ({cache_rate:.1f}%)")
    print(f"  Threats blocked: {total_threats:,}")
    print()

    # Daily breakdown
    print(f"  {'Date':<12} {'Requests':>10} {'Visitors':>10} {'Bandwidth':>12}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*12}")
    for g in groups:
        date = g["dimensions"]["date"]
        reqs = g["sum"]["requests"]
        uniq = g["uniq"]["uniques"]
        bw = fmt_bytes(g["sum"]["bytes"])
        print(f"  {date:<12} {reqs:>10,} {uniq:>10,} {bw:>12}")
    print()

def analytics_top_paths(domain, days=1, limit=20):
    """Get top requested paths for a domain using HTTP adaptive groups (max 24h)."""
    from datetime import datetime, timedelta, timezone

    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    # Adaptive groups API only supports 24h max
    if days > 1:
        print(f"  Note: Path analytics limited to 24 hours (API restriction)")
        days = 1

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    # Use httpRequestsAdaptiveGroups which supports path dimensions
    query = """
    query GetTopPaths($zoneTag: String!, $since: DateTime!, $until: DateTime!, $limit: Int!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequestsAdaptiveGroups(
            limit: $limit
            filter: {datetime_geq: $since, datetime_leq: $until}
            orderBy: [count_DESC]
          ) {
            dimensions {
              clientRequestPath
            }
            count
            sum {
              edgeResponseBytes
            }
          }
        }
      }
    }
    """

    variables = {
        "zoneTag": zone_id,
        "since": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "until": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": limit
    }

    result = graphql_request(query, variables)

    if result.get("errors"):
        print_json(result)
        return

    zones = result.get("data", {}).get("viewer", {}).get("zones", [])
    if not zones or not zones[0].get("httpRequestsAdaptiveGroups"):
        print(f"No path data for {domain}")
        return

    groups = zones[0]["httpRequestsAdaptiveGroups"]

    def fmt_bytes(b):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"

    print(f"\n{'='*70}")
    print(f"  Top Paths: {domain} (last {days} days)")
    print(f"{'='*70}\n")
    print(f"  {'Requests':>10}  {'Bandwidth':>10}  Path")
    print(f"  {'-'*10}  {'-'*10}  {'-'*45}")

    for g in groups:
        path = g["dimensions"].get("clientRequestPath", "/")
        reqs = g.get("count", 0)
        bw = fmt_bytes(g["sum"].get("edgeResponseBytes", 0))
        display_path = path[:50] + "..." if len(path) > 53 else path
        print(f"  {reqs:>10,}  {bw:>10}  {display_path}")
    print()

def analytics_countries(domain, days=7, limit=15):
    """Get traffic by country for a domain."""
    from datetime import datetime, timedelta, timezone

    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    query = """
    query GetCountries($zoneTag: String!, $since: String!, $until: String!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequests1dGroups(
            limit: 100
            filter: {date_geq: $since, date_leq: $until}
          ) {
            sum {
              countryMap {
                clientCountryName
                requests
                bytes
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "zoneTag": zone_id,
        "since": start.strftime("%Y-%m-%d"),
        "until": end.strftime("%Y-%m-%d")
    }

    result = graphql_request(query, variables)

    if result.get("errors"):
        print_json(result)
        return

    zones = result.get("data", {}).get("viewer", {}).get("zones", [])
    if not zones or not zones[0].get("httpRequests1dGroups"):
        print(f"No country data for {domain}")
        return

    groups = zones[0]["httpRequests1dGroups"]

    # Aggregate by country from countryMap
    country_stats = {}
    for g in groups:
        for country_entry in g["sum"].get("countryMap", []):
            country = country_entry.get("clientCountryName", "Unknown")
            if country not in country_stats:
                country_stats[country] = {"requests": 0, "bytes": 0}
            country_stats[country]["requests"] += country_entry.get("requests", 0)
            country_stats[country]["bytes"] += country_entry.get("bytes", 0)

    # Sort by requests
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1]["requests"], reverse=True)[:limit]
    total_requests = sum(c[1]["requests"] for c in sorted_countries)

    def fmt_bytes(b):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"

    print(f"\n{'='*60}")
    print(f"  Traffic by Country: {domain} (last {days} days)")
    print(f"{'='*60}\n")
    print(f"  {'Country':<25} {'Requests':>10} {'%':>7} {'Bandwidth':>10}")
    print(f"  {'-'*25} {'-'*10} {'-'*7} {'-'*10}")

    for country, stats in sorted_countries:
        reqs = stats["requests"]
        pct = (reqs / total_requests * 100) if total_requests > 0 else 0
        bw = fmt_bytes(stats["bytes"])
        display_country = country[:24] if len(country) > 24 else country
        print(f"  {display_country:<25} {reqs:>10,} {pct:>6.1f}% {bw:>10}")
    print()

def analytics_status_codes(domain, days=7):
    """Get HTTP status code breakdown for a domain."""
    from datetime import datetime, timedelta, timezone

    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    query = """
    query GetStatusCodes($zoneTag: String!, $since: String!, $until: String!) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          httpRequests1dGroups(
            limit: 100
            filter: {date_geq: $since, date_leq: $until}
          ) {
            sum {
              responseStatusMap {
                edgeResponseStatus
                requests
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "zoneTag": zone_id,
        "since": start.strftime("%Y-%m-%d"),
        "until": end.strftime("%Y-%m-%d")
    }

    result = graphql_request(query, variables)

    if result.get("errors"):
        print_json(result)
        return

    zones = result.get("data", {}).get("viewer", {}).get("zones", [])
    if not zones or not zones[0].get("httpRequests1dGroups"):
        print(f"No status code data for {domain}")
        return

    groups = zones[0]["httpRequests1dGroups"]

    # Aggregate status codes
    status_counts = {}
    for g in groups:
        for status_entry in g["sum"].get("responseStatusMap", []):
            code = status_entry["edgeResponseStatus"]
            reqs = status_entry["requests"]
            status_counts[code] = status_counts.get(code, 0) + reqs

    # Sort by status code
    sorted_codes = sorted(status_counts.items(), key=lambda x: x[0])
    total = sum(status_counts.values())

    # Group by category
    categories = {
        "2xx Success": {},
        "3xx Redirect": {},
        "4xx Client Error": {},
        "5xx Server Error": {},
        "Other": {}
    }

    for code, count in sorted_codes:
        if 200 <= code < 300:
            categories["2xx Success"][code] = count
        elif 300 <= code < 400:
            categories["3xx Redirect"][code] = count
        elif 400 <= code < 500:
            categories["4xx Client Error"][code] = count
        elif 500 <= code < 600:
            categories["5xx Server Error"][code] = count
        else:
            categories["Other"][code] = count

    print(f"\n{'='*50}")
    print(f"  Status Codes: {domain} (last {days} days)")
    print(f"{'='*50}\n")

    for category, codes in categories.items():
        if codes:
            cat_total = sum(codes.values())
            cat_pct = (cat_total / total * 100) if total > 0 else 0
            print(f"  {category}: {cat_total:,} ({cat_pct:.1f}%)")
            for code, count in sorted(codes.items()):
                pct = (count / total * 100) if total > 0 else 0
                print(f"    {code}: {count:,} ({pct:.1f}%)")
            print()

def analytics_summary(domain, days=7):
    """Get full analytics summary for a domain (traffic + countries + status)."""
    analytics_traffic(domain, days)
    analytics_countries(domain, days, 10)
    analytics_status_codes(domain, days)

# ============== EMAIL ROUTING ==============

def email_settings(domain):
    """Get email routing settings for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return None

    result = api_request("GET", f"/zones/{zone_id}/email/routing")
    if result.get("success") and result.get("result"):
        settings = result["result"]
        print(f"\n{'='*50}")
        print(f"  Email Routing: {domain}")
        print(f"{'='*50}\n")
        print(f"  Enabled: {settings.get('enabled', False)}")
        print(f"  Status: {settings.get('status', 'unknown')}")
        if settings.get('name'):
            print(f"  Name: {settings['name']}")
        print()
        return settings
    else:
        print_json(result)
        return None

def email_enable(domain):
    """Enable email routing for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    endpoint = f"/zones/{zone_id}/email/routing/enable"
    result = api_request("POST", endpoint)
    if result.get("success"):
        print(f"\nEmail routing enabled for {domain}")
        print("MX and SPF records have been added and locked.\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_disable(domain):
    """Disable email routing for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    endpoint = f"/zones/{zone_id}/email/routing/disable"
    result = api_request("POST", endpoint)
    if result.get("success"):
        print(f"\nEmail routing disabled for {domain}\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_addresses_list():
    """List destination addresses for the account."""
    endpoint = f"/accounts/{ACCOUNT_ID}/email/routing/addresses"
    result = api_request("GET", endpoint)
    if result.get("success") and "result" in result:
        addresses = result["result"]
        print(f"\n{'='*60}")
        print(f"  Destination Addresses")
        print(f"{'='*60}\n")
        if not addresses:
            print("  No destination addresses configured.\n")
            return
        for addr in addresses:
            status = "✓ verified" if addr.get("verified") else "⏳ pending"
            print(f"  {addr['email']} [{status}]")
            print(f"    ID: {addr['id']}")
            if addr.get('created'):
                print(f"    Created: {addr['created']}")
        print()
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_address_add(email):
    """Add a destination address (requires verification)."""
    data = {"email": email}
    endpoint = f"/accounts/{ACCOUNT_ID}/email/routing/addresses"
    result = api_request("POST", endpoint, data)
    if result.get("success"):
        print(f"\nDestination address created: {email}")
        print("A verification email has been sent. Click the link to verify.\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_address_delete(address_id):
    """Delete a destination address."""
    endpoint = f"/accounts/{ACCOUNT_ID}/email/routing/addresses/{address_id}"
    result = api_request("DELETE", endpoint)
    if result.get("success"):
        print(f"\nDestination address deleted.\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_rules_list(domain):
    """List email routing rules for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    endpoint = f"/zones/{zone_id}/email/routing/rules"
    result = api_request("GET", endpoint)
    if result.get("success") and result.get("result"):
        rules = result["result"]
        print(f"\n{'='*70}")
        print(f"  Email Routing Rules: {domain}")
        print(f"{'='*70}\n")
        if not rules:
            print("  No routing rules configured.\n")
            return
        for rule in rules:
            enabled = "✓" if rule.get("enabled") else "✗"
            name = rule.get("name", "Unnamed")
            print(f"  [{enabled}] {name}")
            print(f"      ID: {rule['id']}")
            for matcher in rule.get("matchers", []):
                if matcher.get("type") == "literal":
                    print(f"      From: {matcher.get('value', '?')}")
            for action in rule.get("actions", []):
                if action.get("type") == "forward":
                    destinations = action.get("value", [])
                    print(f"      To: {', '.join(destinations)}")
                elif action.get("type") == "drop":
                    print(f"      Action: drop")
                elif action.get("type") == "worker":
                    print(f"      Worker: {action.get('value', ['?'])[0]}")
        print()
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_rule_add(domain, from_address, to_address, name=None):
    """Create an email routing rule."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    local_part = from_address.split("@")[0] if "@" in from_address else from_address
    full_from = f"{local_part}@{domain}"

    if not name:
        name = f"Forward {local_part} to {to_address}"

    data = {
        "actions": [{"type": "forward", "value": [to_address]}],
        "matchers": [{"type": "literal", "field": "to", "value": full_from}],
        "enabled": True,
        "name": name
    }

    endpoint = f"/zones/{zone_id}/email/routing/rules"
    result = api_request("POST", endpoint, data)
    if result.get("success"):
        print(f"\nRouting rule created:")
        print(f"  {full_from} → {to_address}\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_rule_delete(domain, rule_id):
    """Delete an email routing rule."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    endpoint = f"/zones/{zone_id}/email/routing/rules/{rule_id}"
    result = api_request("DELETE", endpoint)
    if result.get("success"):
        print(f"\nRouting rule deleted.\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_catchall_get(domain):
    """Get catch-all rule for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    endpoint = f"/zones/{zone_id}/email/routing/rules/catch_all"
    result = api_request("GET", endpoint)
    if result.get("success") and result.get("result"):
        rule = result["result"]
        enabled = "✓ enabled" if rule.get("enabled") else "✗ disabled"
        print(f"\n{'='*50}")
        print(f"  Catch-All Rule: {domain}")
        print(f"{'='*50}\n")
        print(f"  Status: {enabled}")
        for action in rule.get("actions", []):
            if action.get("type") == "forward":
                destinations = action.get("value", [])
                print(f"  Forward to: {', '.join(destinations)}")
            elif action.get("type") == "drop":
                print(f"  Action: drop (reject all)")
        print()
    elif not handle_api_error(result, endpoint):
        print_json(result)

def email_catchall_set(domain, to_address=None, enabled=True):
    """Set catch-all rule for a domain."""
    zone_id = get_zone_id(domain)
    if not zone_id:
        print(f"Zone not found: {domain}")
        return

    if to_address:
        data = {
            "actions": [{"type": "forward", "value": [to_address]}],
            "matchers": [{"type": "all"}],
            "enabled": enabled,
            "name": f"Catch-all forward to {to_address}"
        }
    else:
        data = {
            "actions": [{"type": "drop"}],
            "matchers": [{"type": "all"}],
            "enabled": enabled,
            "name": "Catch-all drop"
        }

    endpoint = f"/zones/{zone_id}/email/routing/rules/catch_all"
    result = api_request("PUT", endpoint, data)
    if result.get("success"):
        if to_address:
            print(f"\nCatch-all rule set: *@{domain} → {to_address}\n")
        else:
            print(f"\nCatch-all rule set to drop all unmatched emails.\n")
    elif not handle_api_error(result, endpoint):
        print_json(result)

# ============== REDIRECT RULES ==============

def redirects_list(zone_id):
    """List page rules for a zone."""
    result = api_request("GET", f"/zones/{zone_id}/pagerules")
    print_json(result)

def redirects_create_www(zone_id, domain):
    """Create a redirect rule from www to non-www using Page Rules."""
    data = {
        "targets": [
            {
                "target": "url",
                "constraint": {
                    "operator": "matches",
                    "value": f"www.{domain}/*"
                }
            }
        ],
        "actions": [
            {
                "id": "forwarding_url",
                "value": {
                    "url": f"https://{domain}/$1",
                    "status_code": 301
                }
            }
        ],
        "priority": 1,
        "status": "active"
    }
    result = api_request("POST", f"/zones/{zone_id}/pagerules", data)
    if result.get("success"):
        print(f"\nPage Rule created: www.{domain}/* -> {domain}/$1 (301)")
    print_json(result)

def redirects_delete(zone_id, pagerule_id):
    """Delete a page rule."""
    result = api_request("DELETE", f"/zones/{zone_id}/pagerules/{pagerule_id}")
    print_json(result)

# ============== HELPER COMMANDS ==============

def find_zone(domain):
    """Find zone ID by domain name."""
    result = api_request("GET", f"/zones?name={domain}")
    if result.get("success") and result.get("result"):
        zone = result["result"][0]
        print(f"Zone ID: {zone['id']}")
        print(f"Name: {zone['name']}")
        print(f"Status: {zone['status']}")
        print(f"Nameservers: {', '.join(zone.get('name_servers', []))}")
    else:
        print_json(result)

def verify():
    """Verify API token is valid."""
    result = api_request("GET", "/user/tokens/verify")
    print_json(result)

def show_help():
    """Show help message."""
    help_text = """
Cloudflare CLI - Manage zones, DNS records, Pages, Email Routing, and analytics.

USAGE:
    python3 cloudflare.py <command> [args...]

COMMANDS:
    verify                              Verify API token

    ZONES:
    zones list                          List all zones
    zones get <zone_id>                 Get zone details
    zones create <domain> [type]        Create zone (type: full/partial)
    zones delete <zone_id>              Delete zone
    zones find <domain>                 Find zone by domain name

    DNS RECORDS:
    dns list <zone_id>                  List DNS records
    dns create <zone_id> <type> <name> <content> [ttl] [proxied] [priority]
    dns update <zone_id> <record_id> <type> <name> <content> [ttl] [proxied] [priority]
    dns delete <zone_id> <record_id>    Delete DNS record

    EMAIL ROUTING:
    email <domain>                      Get email routing settings
    email enable <domain>               Enable email routing (adds MX records)
    email disable <domain>              Disable email routing
    email addresses                     List destination addresses (account-wide)
    email address add <email>           Add destination address (requires verification)
    email address delete <id>           Delete destination address
    email rules <domain>                List routing rules
    email rule add <domain> <from> <to> Create routing rule (from = local part or full)
    email rule delete <domain> <id>     Delete routing rule
    email catchall <domain>             Get catch-all rule
    email catchall <domain> <to>        Set catch-all to forward to address
    email catchall <domain> drop        Set catch-all to drop/reject

    PAGES:
    pages list                          List Pages projects
    pages get <project_name>            Get project details
    pages domains <project_name>        List custom domains
    pages domain add <project> <domain> Add custom domain
    pages domain delete <project> <domain> Remove custom domain
    pages env list <project> [env]      List environment variables
    pages env set <project> <name> <value> [env] [--secret]  Set env var
    pages env delete <project> <name> [env]  Delete env var

    R2 STORAGE:
    r2 list                             List all R2 buckets
    r2 create <name> [location]         Create bucket (location: wnam, enam, weur, eeur, apac)
    r2 delete <name>                    Delete bucket
    r2 get <name>                       Get bucket details
    r2 objects <bucket> [prefix]        List objects in bucket

    WORKERS:
    workers domains                     List Workers custom domains

    ANALYTICS:
    analytics <domain> [days]           Full traffic summary (default: 7 days)
    analytics traffic <domain> [days]   Requests, visitors, bandwidth
    analytics paths <domain> [days]     Top requested paths
    analytics countries <domain> [days] Traffic by country
    analytics status <domain> [days]    HTTP status code breakdown

EXAMPLES:
    python3 cloudflare.py zones create clippa.net
    python3 cloudflare.py zones find clippa.net
    python3 cloudflare.py dns list abc123
    python3 cloudflare.py email enable skills.ceo
    python3 cloudflare.py email rule add skills.ceo dave justindmo94@gmail.com
    python3 cloudflare.py email catchall skills.ceo justindmo94@gmail.com
    python3 cloudflare.py pages domain add my-project clippa.net
    python3 cloudflare.py analytics clippa.net
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    try:
        if cmd == "help":
            show_help()
        elif cmd == "verify":
            verify()

        # Zones
        elif cmd == "zones":
            if not args or args[0] == "list":
                zones_list()
            elif args[0] == "get" and len(args) > 1:
                zones_get(args[1])
            elif args[0] == "create" and len(args) > 1:
                zone_type = args[2] if len(args) > 2 else "full"
                zones_create(args[1], zone_type)
            elif args[0] == "delete" and len(args) > 1:
                zones_delete(args[1])
            elif args[0] == "find" and len(args) > 1:
                find_zone(args[1])
            else:
                print("Usage: zones [list|get|create|delete|find] ...")

        # DNS
        elif cmd == "dns":
            if not args:
                print("Usage: dns [list|create|update|delete] ...")
            elif args[0] == "list" and len(args) > 1:
                dns_list(args[1])
            elif args[0] == "create" and len(args) >= 4:
                zone_id, rtype, name, content = args[1:5]
                ttl = int(args[5]) if len(args) > 5 else 1
                proxied = args[6].lower() == "true" if len(args) > 6 else False
                priority = int(args[7]) if len(args) > 7 else None
                dns_create(zone_id, rtype, name, content, ttl, proxied, priority)
            elif args[0] == "update" and len(args) >= 5:
                zone_id, record_id, rtype, name, content = args[1:6]
                ttl = int(args[6]) if len(args) > 6 else 1
                proxied = args[7].lower() == "true" if len(args) > 7 else False
                priority = int(args[8]) if len(args) > 8 else None
                dns_update(zone_id, record_id, rtype, name, content, ttl, proxied, priority)
            elif args[0] == "delete" and len(args) > 2:
                dns_delete(args[1], args[2])
            else:
                print("Usage: dns [list|create|update|delete] ...")

        # Pages
        elif cmd == "pages":
            if not args or args[0] == "list":
                pages_list()
            elif args[0] == "get" and len(args) > 1:
                pages_get(args[1])
            elif args[0] == "create" and len(args) > 1:
                branch = args[2] if len(args) > 2 else "main"
                pages_create(args[1], branch)
            elif args[0] == "connect" and len(args) >= 4:
                # pages connect <project> <owner> <repo> [branch]
                project, owner, repo = args[1:4]
                branch = args[4] if len(args) > 4 else "main"
                pages_connect_git(project, owner, repo, branch)
            elif args[0] == "build" and len(args) >= 4:
                # pages build <project> <build_cmd> <dest_dir> [root_dir]
                project, build_cmd, dest_dir = args[1:4]
                root_dir = args[4] if len(args) > 4 else ""
                pages_update_build(project, build_cmd, dest_dir, root_dir)
            elif args[0] == "domains" and len(args) > 1:
                pages_domains_list(args[1])
            elif args[0] == "domain":
                if len(args) >= 3 and args[1] == "add":
                    pages_domains_add(args[2], args[3])
                elif len(args) >= 3 and args[1] == "delete":
                    pages_domains_delete(args[2], args[3])
                else:
                    print("Usage: pages domain [add|delete] <project> <domain>")
            elif args[0] == "env":
                if len(args) >= 2 and args[1] == "list":
                    # pages env list <project> [environment]
                    project = args[2] if len(args) > 2 else None
                    if not project:
                        print("Usage: pages env list <project> [production|preview]")
                    else:
                        env = args[3] if len(args) > 3 else "production"
                        pages_env_list(project, env)
                elif len(args) >= 4 and args[1] == "set":
                    # pages env set <project> <name> <value> [environment] [--secret]
                    project, var_name, var_value = args[2:5]
                    env = "production"
                    secret = False
                    for arg in args[5:]:
                        if arg == "--secret":
                            secret = True
                        elif arg in ["production", "preview"]:
                            env = arg
                    pages_env_set(project, var_name, var_value, env, secret)
                elif len(args) >= 4 and args[1] == "delete":
                    # pages env delete <project> <name> [environment]
                    project, var_name = args[2:4]
                    env = args[4] if len(args) > 4 else "production"
                    pages_env_delete(project, var_name, env)
                else:
                    print("Usage: pages env list <project> [production|preview]")
                    print("       pages env set <project> <name> <value> [production|preview] [--secret]")
                    print("       pages env delete <project> <name> [production|preview]")
            else:
                print("Usage: pages [list|get|create|connect|build|domains|domain|env] ...")

        # Workers
        elif cmd == "workers":
            if not args or args[0] == "list":
                workers_list()
            elif args[0] == "subdomain":
                if len(args) > 1:
                    workers_subdomain(args[1])  # Set new subdomain
                else:
                    workers_subdomain()  # Get current
            elif args[0] == "get" and len(args) > 1:
                workers_get(args[1])
            elif args[0] == "delete" and len(args) > 1:
                workers_delete(args[1])
            elif args[0] == "domains":
                workers_domains_list()
            elif args[0] == "media" and len(args) >= 3:
                # workers media <worker-name> <bucket-name>
                workers_deploy_media(args[1], args[2])
            else:
                print("Usage: workers [list|subdomain|get|delete|domains|media] ...")
                print("       workers media <name> <r2-bucket>  - Deploy media server")

        # R2 Storage
        elif cmd == "r2":
            if not args or args[0] == "list":
                r2_list_buckets()
            elif args[0] == "create" and len(args) > 1:
                location = args[2] if len(args) > 2 else "wnam"
                r2_create_bucket(args[1], location)
            elif args[0] == "delete" and len(args) > 1:
                r2_delete_bucket(args[1])
            elif args[0] == "get" and len(args) > 1:
                r2_get_bucket(args[1])
            elif args[0] == "objects" and len(args) > 1:
                bucket = args[1]
                prefix = args[2] if len(args) > 2 else ""
                r2_list_objects(bucket, prefix)
            else:
                print("Usage: r2 [list|create|delete|get|objects] ...")
                print("       r2 objects <bucket> [prefix]  - List objects in bucket")

        # KV Storage
        elif cmd == "kv":
            if not args or args[0] == "namespaces":
                kv_namespaces_list()
            elif args[0] == "keys" and len(args) > 1:
                prefix = args[2] if len(args) > 2 else ""
                kv_keys_list(args[1], prefix)
            elif args[0] == "get" and len(args) > 2:
                kv_get(args[1], args[2])
            elif args[0] == "put" and len(args) > 3:
                ttl = int(args[4]) if len(args) > 4 else None
                kv_put(args[1], args[2], args[3], ttl)
            elif args[0] == "delete" and len(args) > 2:
                kv_delete(args[1], args[2])
            else:
                print("Usage: kv namespaces | kv keys <ns_id> | kv get <ns_id> <key> | kv put <ns_id> <key> <value> | kv delete <ns_id> <key>")

        # Email Routing
        elif cmd == "email":
            if not args:
                print("Usage: email <domain> | email [enable|disable|addresses|rules|catchall] ...")
            elif args[0] == "enable" and len(args) > 1:
                email_enable(args[1])
            elif args[0] == "disable" and len(args) > 1:
                email_disable(args[1])
            elif args[0] == "addresses":
                email_addresses_list()
            elif args[0] == "address":
                if len(args) >= 3 and args[1] == "add":
                    email_address_add(args[2])
                elif len(args) >= 3 and args[1] == "delete":
                    email_address_delete(args[2])
                else:
                    print("Usage: email address [add|delete] <email|id>")
            elif args[0] == "rules" and len(args) > 1:
                email_rules_list(args[1])
            elif args[0] == "rule":
                if len(args) >= 4 and args[1] == "add":
                    # email rule add <domain> <from> <to>
                    email_rule_add(args[2], args[3], args[4])
                elif len(args) >= 4 and args[1] == "delete":
                    # email rule delete <domain> <id>
                    email_rule_delete(args[2], args[3])
                else:
                    print("Usage: email rule [add|delete] <domain> <from> <to>|<id>")
            elif args[0] == "catchall" and len(args) > 1:
                if len(args) == 2:
                    email_catchall_get(args[1])
                elif args[2].lower() == "drop":
                    email_catchall_set(args[1], None, True)
                else:
                    email_catchall_set(args[1], args[2], True)
            else:
                # email <domain> - get settings
                email_settings(args[0])

        # Redirects
        elif cmd == "redirects":
            if not args:
                print("Usage: redirects [list|www|delete] ...")
            elif args[0] == "list" and len(args) > 1:
                redirects_list(args[1])
            elif args[0] == "www" and len(args) > 2:
                # redirects www <zone_id> <domain>
                redirects_create_www(args[1], args[2])
            elif args[0] == "delete" and len(args) > 2:
                redirects_delete(args[1], args[2])
            else:
                print("Usage: redirects [list|www|delete] <zone_id> ...")

        # Analytics
        elif cmd == "analytics":
            if not args:
                print("Usage: analytics [traffic|paths|countries|status] <domain> [days]")
            elif args[0] == "traffic" and len(args) > 1:
                domain = args[1]
                days = int(args[2]) if len(args) > 2 else 7
                analytics_traffic(domain, days)
            elif args[0] == "paths" and len(args) > 1:
                domain = args[1]
                days = int(args[2]) if len(args) > 2 else 7
                analytics_top_paths(domain, days)
            elif args[0] == "countries" and len(args) > 1:
                domain = args[1]
                days = int(args[2]) if len(args) > 2 else 7
                analytics_countries(domain, days)
            elif args[0] == "status" and len(args) > 1:
                domain = args[1]
                days = int(args[2]) if len(args) > 2 else 7
                analytics_status_codes(domain, days)
            elif args[0] not in ["traffic", "paths", "countries", "status"]:
                # Direct domain name - show full summary
                domain = args[0]
                days = int(args[1]) if len(args) > 1 else 7
                analytics_summary(domain, days)
            else:
                print("Usage: analytics [traffic|paths|countries|status] <domain> [days]")

        else:
            print(f"Unknown command: {cmd}")
            show_help()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
