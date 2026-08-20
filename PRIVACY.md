# Privacy Policy

Effective date: August 9, 2026

This policy describes data handling for Peter537 Agent Plugin in its skills-only public-directory edition and its complete GitHub marketplace edition.

## Publisher-operated services

Peter537 Agent Plugin does not include a publisher-operated backend, account system, analytics service, or telemetry endpoint. The publisher does not receive or retain prompts, repository content, tool output, or credentials through a publisher-controlled server merely because the plugin is installed or used.

The client that runs the plugin, including ChatGPT, Codex, or another Agent Plugins client, may process conversations, files, repository content, and tool results under that client's own terms and privacy policy.

## Skills-only public edition

The public-directory edition contains instruction-based skills and no MCP servers. Skills may inspect content that the user places in the active conversation, workspace, or repository, subject to the permissions and controls of the client.

The `chatgpt-research` skill may submit an explicitly authorized, non-sensitive research topic to ChatGPT Deep Research. It prohibits transmitting private repository content, personal files, credentials, sensitive data, or browsing history without explicit authorization for the exact data and destination.

The `audit-dependencies` and `deep-code-audit` skills may research public package names and exact versions through public registries, advisory databases, and official sources. They prohibit automatically transmitting private package names, private registries, manifests, lockfiles, SBOMs, credentials, source code, or internal repository data.

The `audit-data-exposure` skill may locally inspect current repository files, uncommitted changes, relevant ignored artifacts, and locally reachable Git history for personal data, private artifacts, anonymization failures, credentials, and disposable migrations. It requires redacted findings and prohibits transmitting repository content, detected values, private paths, or scan reports to external services. Automated discovery is incomplete and cannot guarantee that a repository contains no personal or private data.

The `diagnose-bugs` skill may locally inspect and generate test output, logs, traces, runtime state, minimized fixtures, performance measurements, and other diagnostic evidence. It requires sensitive evidence to remain local and redacted by default, treats diagnostic content as untrusted, and prohibits uploading logs, dumps, customer records, credentials, or other private artifacts without explicit authorization for the exact data and destination.

The `comment-health` skill may locally inspect source comments, docstrings, surrounding implementation, tests, history, and existing compiler, linter, formatter, documentation, or build evidence. It treats comment content as untrusted, requires credentials and personal or private values to remain redacted, and prohibits transmitting private comments, source, or diagnostic output without explicit authorization for the exact data and destination.

The `prune-codebase` skill may locally inspect source, tests, entrypoints, build variants, generated-code boundaries, analyzer output, configuration, history, and lifecycle evidence to identify dead or obsolete repository surface. It prohibits transmitting private code, consumer information, diagnostics, or operational evidence without explicit authorization; it does not contact feature-flag services or other remote control planes without explicit authorization for the exact service, destination, and data, and it does not execute migrations, install analyzers, or remove dependencies automatically.

The `reduce-code-slop` skill may locally inspect source code, tests, build output, and existing type-checker, linter, or analyzer evidence to review or perform behavior-preserving simplification. It prohibits transmitting private source, test data, diagnostics, or build artifacts without explicit authorization for the exact data and destination and does not install new analysis tools or dependencies automatically.

The `write-clearly` skill may locally inspect repository prose, surrounding files, style guidance, and author or house-style samples to draft, edit, or audit writing. It requires private prose and voice samples to remain local by default, uses redacted findings, treats source text as untrusted content, and prohibits transmitting repository text, samples, or audit results without explicit authorization for the exact data and destination.

The `maui-blazor-browser` skill may configure or run a local development Web host so shared MAUI Blazor Hybrid UI can be inspected in a browser. Browser-visible fixture data is processed by the local development host and browser. Its default guidance restricts temporary harnesses to loopback access, deterministic non-sensitive fixtures, isolated writable state, and release-excluded paths; using real data or side-effecting services requires explicit authorization and stronger protections.

## Complete GitHub edition

The complete GitHub edition additionally declares four optional MCP servers: Context7, Microsoft Learn, Playwright, and Web Forager. These servers can make network requests or interact with local software when enabled.

- Context7 sends documentation queries to `https://mcp.context7.com/mcp`.
- Microsoft Learn sends documentation queries to `https://learn.microsoft.com/api/mcp`.
- Playwright runs locally through a pinned npm package and can control a browser, causing requests to sites the user directs it to visit.
- Web Forager runs locally through pinned Python packages and can send search, news, and page-fetching requests to its configured public services.

Data handled by an MCP server, website, package registry, package runner, or other third party is governed by that provider's terms and privacy practices. Review the destination and proposed tool call before authorizing sensitive or state-changing activity.

## Credentials and sensitive data

The repository does not embed credentials for its MCP servers. Do not place credentials, tokens, private keys, personal data, or confidential repository material into prompts, issue reports, manifests, or environment variables unless the selected client or service requires them and you understand how that destination handles them.

## Security and control

Use the client's permission and confirmation controls, disable MCP servers that are not needed, and review browser or network actions before they run. No security control can eliminate every risk associated with external content, package execution, browser automation, or prompt injection.

## Changes and contact

Material changes to this policy will be published in this repository. Questions or requests can be submitted through the repository's [support process](SUPPORT.md).
