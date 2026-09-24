# Security

This project is experimental. There is no stable-release security support or
guaranteed response time yet. Fixes are developed on the default branch.

## Reporting a vulnerability

Use this repository's **Security > Advisories > Report a vulnerability** option
when private vulnerability reporting is available. Include the affected commit,
a minimal reproduction, and the impact, using synthetic data.

If that option is unavailable, open an issue requesting a private contact
channel without including exploit details, credentials, or sensitive data.
Wait for a private channel before sharing those details.

## Trust boundary

Specifications and fixtures execute arbitrary Python code with the runner's
permissions. The framework is not a sandbox for untrusted tests. Reports can
contain Examples inputs, step text, exception messages, and stack traces;
review them before sharing.
