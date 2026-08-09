# Privacy Policy

Effective date: August 9, 2026

This policy describes data handling for Peter537 Agent Plugin in its skills-only public-directory edition and its complete GitHub marketplace edition.

## Publisher-operated services

Peter537 Agent Plugin does not include a publisher-operated backend, account system, analytics service, or telemetry endpoint. The publisher does not receive or retain prompts, repository content, tool output, or credentials through a publisher-controlled server merely because the plugin is installed or used.

The client that runs the plugin, including ChatGPT, Codex, or another Agent Plugins client, may process conversations, files, repository content, and tool results under that client's own terms and privacy policy.

## Skills-only public edition

The public-directory edition contains six instruction-based skills and no MCP servers. Skills may inspect content that the user places in the active conversation, workspace, or repository, subject to the permissions and controls of the client.

The `chatgpt-research` skill may submit an explicitly authorized, non-sensitive research topic to ChatGPT Deep Research. It prohibits transmitting private repository content, personal files, credentials, sensitive data, or browsing history without explicit authorization for the exact data and destination.

The `audit-dependencies` and `deep-code-audit` skills may research public package names and exact versions through public registries, advisory databases, and official sources. They prohibit automatically transmitting private package names, private registries, manifests, lockfiles, SBOMs, credentials, source code, or internal repository data.

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
