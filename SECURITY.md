# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| :--- | :--- |
| 2.0.x | :white_check_mark: |
| 1.0.x | :x:                |

---

## ⚠️ Credential & API Key Safety

- **NEVER** commit live blockchain API keys (e.g., Etherscan API keys) or private wallet credentials.
- Store sensitive keys in a local `.env` file (which is strictly ignored by Git).
- If any API key is inadvertently exposed in git history, issues, or logs, consider it compromised and rotate it immediately.

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in the Crypto Attribution Engine:

1. **Do not open a public GitHub issue.**
2. Send an email with reproduction steps and vulnerability details to the project maintainers.
3. We will respond within 48 hours and work with you on a coordinated disclosure timeline.
