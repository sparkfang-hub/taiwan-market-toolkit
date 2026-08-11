# Security Policy

## Supported versions

The project is currently pre-1.0. Security fixes are applied to the latest code on the default branch.

## Reporting a vulnerability

Please do not publish exploit details, credentials, private market data, or other sensitive information in a public issue.

Prefer GitHub's private security-reporting / Security Advisory flow for this repository when available. If that flow is unavailable, open a public issue containing only a high-level statement that you need a private channel for a security report; do not include reproduction steps or exploit details there.

A useful private report should include:

- affected version or commit;
- affected component and execution path;
- impact and realistic attack scenario;
- minimal reproduction steps;
- suggested mitigation, if known.

## Scope notes

Taiwan Market Toolkit does not contain brokerage credentials, order execution, or private trading strategies. Integrations that fetch public market metadata should still treat network responses as untrusted input and should avoid exposing local files, secrets, or arbitrary command execution through MCP tools or other adapters.
