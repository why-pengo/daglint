# Security Policy

## Supported Versions

Only the latest release of daglint receives security fixes.

| Version | Supported |
| ------- | --------- |
| Latest release | ✅ |
| All older versions | ❌ |

## Reporting a Vulnerability

Please do not report security vulnerabilities in public issues.

Instead, use [GitHub private vulnerability reporting](https://github.com/why-pengo/daglint/security/advisories/new)
(Security tab → *Report a vulnerability*). You should receive an initial
response within a week.

## Scope

daglint statically analyzes Python source with `ast.parse` and never imports
or executes the code it lints. Configuration files are loaded with
`yaml.safe_load`. Reports about daglint executing untrusted DAG code are
likely out of scope, but reports about crashes, path traversal, or unsafe
configuration handling are welcome.
