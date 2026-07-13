# Security Policy

## Supported Versions

Mirumoji follows [`Semantic Versioning`](https://semver.org/) from `3.0.0` onward

Security fixes are applied to the latest `3.x` release line

| Version  | Supported          |
| -------- | ------------------ |
| `3.4.x`  | :white_check_mark: |
| `< 3.4.0`  | :x:                |

## Reporting a Vulnerability

Please report security issues **privately**. Do not open a public issue for a
vulnerability.

1. **Preferred:** use GitHub's private vulnerability reporting. Go to the
   repository's **Security** tab &rarr; **Report a vulnerability**
   ([`Security Advisories`](https://github.com/svdC1/mirumoji/security/advisories/new)).
2. **Alternative:** email `svdc1mail@gmail.com` with the details below.

Please include:

- The affected surface (server, frontend, CLI/GUI launcher, or Docker image)
  and version.
- A description of the vulnerability and its impact.
- Steps to reproduce or a proof of concept, if available.

## What to Expect

- An acknowledgement within **7 days**.
- An assessment and, where applicable, a fix targeting the next `3.x` patch
  release.
- Credit in the release notes if you would like to be named.

Mirumoji is self-hosted and runs on the user's own machine. The server's CORS
policy is intentionally open for local use. Take care before exposing an
instance to an untrusted network. See
[`Sharing Outside Your Network`](https://svdc1.github.io/mirumoji/docs/guides/sharing/)
in the documentation.
