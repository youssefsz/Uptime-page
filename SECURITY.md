# Security policy

## Supported versions

Uptime Page is currently pre-1.0. Security fixes are applied to the latest revision of the `master` branch. Older commits and forks are not maintained by this project.

## Report a vulnerability

Do not disclose suspected vulnerabilities in a public issue, discussion, or pull request.

Use GitHub's [private vulnerability reporting form](https://github.com/youssefsz/Uptime-page/security/advisories/new). If private reporting is unavailable, contact the maintainer through the contact details on the [project owner's profile](https://github.com/youssefsz) and ask for a private reporting channel.

Include enough information to reproduce and assess the issue:

- Affected version or commit
- Vulnerability type and affected component
- Reproduction steps or a minimal proof of concept
- Expected and observed impact
- Relevant deployment assumptions
- Any suggested mitigation, if known

You should receive an acknowledgement within seven days. The maintainer will investigate, coordinate a fix and release, and credit reporters who want attribution. Please allow reasonable time for remediation before publishing details.

## Security considerations for operators

- Replace the example JWT secret and admin password before deployment.
- Terminate TLS at a trusted reverse proxy and avoid exposing the dashboard unnecessarily.
- Use a dedicated PostgreSQL role with only the permissions the application needs.
- Treat monitor URLs as privileged input. The application makes server-side HTTP requests to them, so only trusted administrators should be able to create or edit monitors.
- Keep the application image and dependencies current, and review the repository's automated security-check results.
- Back up the database and protect logs, configuration, and backup files as sensitive data.

This policy covers the Uptime Page codebase. Vulnerabilities in third-party services, operator-managed infrastructure, or unsupported modifications should be reported to their respective maintainers.
