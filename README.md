# Cloudflare Skill for Claude Code

Manage Cloudflare zones, DNS, Pages, R2, KV, email routing, and analytics via natural language.

## Security Notice

**Review the code before adding credentials.** This skill (and any skill) has access to your API keys. Before creating your `.env` file:

1. Read `scripts/cloudflare.py` yourself
2. Understand what API calls it makes
3. Only then add your credentials

This applies to every skill you install, not just this one.

## Requirements

- Python 3 (no pip packages needed - uses only standard library)

## Install

```bash
git clone https://github.com/skillsceo/cloudflare ~/.claude/skills/cloudflare
```

## Setup

1. Get credentials from [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens)

2. Create `.env`:
```bash
cp ~/.claude/skills/cloudflare/.env.example ~/.claude/skills/cloudflare/.env
```

3. Add credentials:
```bash
export CLOUDFLARE_ACCOUNT_ID=your_account_id
export CLOUDFLARE_API_KEY=your_global_api_key
export CLOUDFLARE_EMAIL=your@email.com
```

4. Verify:
```bash
python3 ~/.claude/skills/cloudflare/scripts/cloudflare.py verify
```

## Usage

Just ask Claude naturally:

- "Add an A record for api.example.com pointing to 192.168.1.1"
- "What's the traffic for example.com this week?"
- "Set up email forwarding for hello@example.com to me@gmail.com"
- "Add example.com as a custom domain to my-pages-project"
- "List all my Cloudflare zones"

## Features

- **Zones**: Create, list, find, delete domains
- **DNS**: A, AAAA, CNAME, MX, TXT, NS records
- **Pages**: Custom domains for Cloudflare Pages
- **Analytics**: Traffic, visitors, bandwidth, paths, countries
- **Email Routing**: Forwarding rules, catch-all
- **R2 Storage**: Buckets and objects
- **KV Storage**: Namespaces, keys, values

## License

MIT
