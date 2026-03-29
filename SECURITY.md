# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do NOT open a public issue for security vulnerabilities.**

Instead, email: **dev@axiomworks.ai** with:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Suggested fix (if you have one)

We will acknowledge receipt within 48 hours and work on a fix.

## Scope

This MCP server handles:
- YouTube API keys (stored in `~/.config/axiomworks-youtube-mcp/`)
- Google OAuth tokens (refresh tokens stored on disk)
- YouTube Music authentication cookies/tokens

Security concerns related to credential storage, token handling, or API key exposure are in scope.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |
