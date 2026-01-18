---
name: cloudflare
description: |
  Manage Cloudflare zones, DNS records, Pages custom domains, and analytics via API. Use when user asks to:
  - Create, list, or manage zones (domains)
  - Create/edit/delete DNS records
  - Get nameservers assigned to a zone
  - Add/remove custom domains from Cloudflare Pages projects
  - View traffic analytics, visitors, bandwidth, top paths, countries
  - Configure email routing and forwarding rules
  - Verify API connection
  Triggers: "cloudflare", "zone", "pages domain", "custom domain", "nameserver", "cloudflare dns", "traffic", "analytics", "visitors", "email routing", "email forwarding"
---

# Cloudflare Manager

Manage Cloudflare zones, DNS records, Pages custom domains, KV storage, email routing, and analytics via the `cloudflare.py` script.

## First-Time Setup

### 1. Get Your Credentials

Go to: **https://dash.cloudflare.com/profile/api-tokens**

You need **ONE** of these (Global API Key recommended for full access):

| Method | What to Get | Permissions |
|--------|-------------|-------------|
| **Global API Key** (recommended) | API Key + Email | Full access to everything |
| API Token | Create custom token | Only what you configure |

### 2. Create .env File

```bash
cp ~/.claude/skills/cloudflare/.env.example ~/.claude/skills/cloudflare/.env
```

Edit with your credentials:

```bash
# REQUIRED: Your Account ID (from any Cloudflare dashboard URL)
export CLOUDFLARE_ACCOUNT_ID=your_account_id

# OPTION A: Global API Key (RECOMMENDED - full permissions)
export CLOUDFLARE_API_KEY=your_global_api_key
export CLOUDFLARE_EMAIL=your@email.com

# OPTION B: API Token (scoped permissions - may lack KV, Workers, etc.)
export CLOUDFLARE_API_TOKEN=your_api_token
```

### 3. Verify Setup

```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py verify
```

---

## API Authentication: Token vs Global Key

**Before troubleshooting auth errors, understand this:**

| | API Token | Global API Key |
|--|-----------|----------------|
| **Permissions** | Only what you add | Everything |
| **Security** | More secure (scoped) | Less secure (full access) |
| **Setup** | Must configure each permission | Works immediately |
| **KV Storage** | Requires explicit permission | ✅ Works |
| **Workers** | Requires explicit permission | ✅ Works |
| **R2** | Requires explicit permission | ✅ Works |

**Recommendation**: Use Global API Key for personal use. Use scoped API Token for production/shared environments.

If a command fails with auth errors, either:
1. Add the missing permission to your token at https://dash.cloudflare.com/profile/api-tokens
2. Or add Global API Key to your .env (script will use it as fallback)

---

## Anti-Patterns

❌ **Token-only setup for KV/Workers**: API Tokens don't include KV permissions by default. You'll get auth errors. Add Global API Key as fallback or explicitly add KV permission to your token.

❌ **Forgetting Account ID**: Many commands fail silently without `CLOUDFLARE_ACCOUNT_ID`. Always set it.

❌ **Using wrong zone ID**: Zone IDs look like random strings. Use `zones find example.com` to get the right one.

❌ **Proxying MX/TXT records**: Email and verification records must have `proxied: false`. The script handles this but manual edits can break email.

---

## Script Location

```
~/.claude/skills/cloudflare/scripts/cloudflare.py
```

Credentials load automatically from `~/.claude/skills/cloudflare/.env`

## Quick Reference

### Verify API Connection
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py verify
```

### List All Zones
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones list
```

### Create a Zone (Add Domain to Cloudflare)
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones create example.com
```

This returns the assigned nameservers to update at your registrar.

### Find Zone by Domain Name
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones find example.com
```

### Get Zone Details
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones get <zone_id>
```

### Delete Zone
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones delete <zone_id>
```

## DNS Records

### List DNS Records
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns list <zone_id>
```

### Create DNS Record
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns create <zone_id> <type> <name> <content> [ttl] [proxied] [priority]

# Examples:
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns create abc123 A www 192.168.1.1
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns create abc123 CNAME blog target.com 1 true
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns create abc123 MX example.com mail.example.com 1 false 10
```

### Update DNS Record
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns update <zone_id> <record_id> <type> <name> <content> [ttl] [proxied]
```

### Delete DNS Record
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py dns delete <zone_id> <record_id>
```

## Cloudflare Pages

### List Pages Projects
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages list
```

### Get Project Details
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages get <project_name>
```

### List Custom Domains
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domains <project_name>
```

### Add Custom Domain to Pages
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain add <project_name> <domain>

# Example:
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain add my-site clippa.net
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain add my-site www.clippa.net
```

### Remove Custom Domain
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain delete <project_name> <domain>
```

## Analytics

### Full Traffic Summary
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics clippa.net
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics clippa.net 30  # last 30 days
```

Shows requests, unique visitors, page views, bandwidth, cache rate, threats blocked, and daily breakdown.

### Traffic Overview Only
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics traffic clippa.net
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics traffic clippa.net 14
```

### Top Requested Paths
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics paths clippa.net
```

### Traffic by Country
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics countries clippa.net
```

### HTTP Status Code Breakdown
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py analytics status clippa.net
```

Shows 2xx/3xx/4xx/5xx breakdown with percentages.

## Email Routing

### Get Email Routing Settings
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email example.com
```

### Enable Email Routing
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email enable example.com
```

Automatically adds and locks required MX and SPF records.

### Disable Email Routing
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email disable example.com
```

### List Destination Addresses (Account-wide)
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email addresses
```

### Add Destination Address
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email address add your@email.com
```

Destination addresses must be verified via email before use.

### Delete Destination Address
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email address delete <address_id>
```

### List Routing Rules
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rules example.com
```

### Create Routing Rule
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rule add <domain> <from> <to>

# Examples:
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rule add skills.ceo dave your@email.com
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rule add skills.ceo support@skills.ceo your@email.com
```

The `<from>` can be just the local part (e.g., `dave`) or full address.

### Delete Routing Rule
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rule delete <domain> <rule_id>
```

### Get Catch-All Rule
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email catchall example.com
```

### Set Catch-All to Forward
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email catchall example.com your@email.com
```

### Set Catch-All to Drop
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email catchall example.com drop
```

## Workflow: Set Up Email Forwarding

1. **Enable email routing:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email enable skills.ceo
   ```

2. **Add and verify destination address:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email address add your@email.com
   ```
   Check email and click verification link.

3. **Create forwarding rule:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email rule add skills.ceo dave your@email.com
   ```

4. **Optionally set catch-all:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py email catchall skills.ceo your@email.com
   ```

## Workflow: Add Domain to Cloudflare + Pages

1. **Create zone in Cloudflare:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones create clippa.net
   ```
   Note the nameservers in the response (e.g., `alex.ns.cloudflare.com`).

2. **Update nameservers at registrar (Porkbun):**
   ```bash
   python3 ~/.claude/skills/porkbun-skill/scripts/porkbun.py ns update clippa.net ns1.cloudflare.com ns2.cloudflare.com
   ```

3. **Add custom domains to Pages project:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain add my-project clippa.net
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py pages domain add my-project www.clippa.net
   ```

4. **Verify zone status:**
   ```bash
   python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py zones find clippa.net
   ```

## R2 Storage

### List R2 Buckets
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 list
```

### Create R2 Bucket
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 create mybucket
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 create mybucket weur  # Western Europe
```

Locations: `wnam` (West NA, default), `enam` (East NA), `weur` (West EU), `eeur` (East EU), `apac` (Asia Pacific)

### Get R2 Bucket Details
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 get mybucket
```

### Delete R2 Bucket
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 delete mybucket
```

### List Objects in R2 Bucket
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 objects mybucket
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py r2 objects mybucket uploads/  # with prefix
```

## KV Storage

### List KV Namespaces
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv namespaces
```

### List Keys in Namespace
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv keys <namespace_id>
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv keys <namespace_id> <prefix>
```

### Get Value
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv get <namespace_id> <key>
```

### Put Value
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv put <namespace_id> <key> <value>
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv put <namespace_id> <key> <value> <ttl_seconds>
```

### Delete Key
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py kv delete <namespace_id> <key>
```

## Common Record Types

| Type | Use Case | Proxied? |
|------|----------|----------|
| A | IPv4 address | Yes |
| AAAA | IPv6 address | Yes |
| CNAME | Alias/redirect | Yes |
| MX | Mail server | No |
| TXT | Verification/SPF | No |
| NS | Nameserver | No |

## API Token Permissions

Your token needs specific permissions for each feature. The script will tell you what's missing if you hit auth errors.

| Feature | Permission Required |
|---------|---------------------|
| Zones | Zone > Zone > Read |
| DNS Records | Zone > DNS > Edit |
| Pages | Account > Cloudflare Pages > Edit |
| Email Routing | Zone > Email Routing Rules > Edit |
| Email Addresses | Account > Email Routing Addresses > Edit |
| Workers | Account > Worker Scripts > Edit |
| R2 Storage | Account > R2 Storage > Edit |
| KV Storage | Account > Workers KV Storage > Edit |
| Analytics | Zone > Analytics > Read |

**To update permissions:**
1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Edit" on your token
3. Add the required permission under "Permissions"
4. Save and copy the new token to `~/.claude/skills/cloudflare/.env`

## Notes

- Script loads .env automatically - no need to source
- TTL of `1` means "automatic" (Cloudflare manages it)
- `proxied: true` enables Cloudflare CDN/protection (orange cloud)
- Zone creation returns assigned nameservers
- Pages custom domains auto-create DNS records when zone is active
- SSL is automatic for Pages custom domains
- Auth errors show exactly which permission is missing

## Help
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py help
```
