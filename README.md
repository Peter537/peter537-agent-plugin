# Peter537 Agent Plugin

Peter537 Agent Plugin is a portable [Agent Plugins v1](https://agent-plugins.org/) package containing reusable skills for software research, planning, reader-first multilingual writing, source-comment health, evidence-driven bug diagnosis, behavior-preserving code simplification, codebase pruning, code and dependency audits, repository data-exposure reviews, supply-chain security, documentation, UI design, and MAUI Blazor browser development. The complete GitHub edition also includes optional MCP integrations.

## Included skills

| Skill | Purpose |
| --- | --- |
| `audit-data-exposure` | Review current repository content and reachable Git history for personal data, private artifacts, anonymization failures, and disposable migrations. |
| `audit-dependencies` | Review every dependency and software supply-chain input before package changes or on request. |
| `chatgpt-research` | Orchestrate and verify multi-source ChatGPT Deep Research. |
| `comment-health` | Audit and safely improve source comments without losing contracts, rationale, documentation, or tool semantics. |
| `deep-code-audit` | Audit correctness, security, architecture, and maintainability across a codebase or scoped change. |
| `deep-planning` | Research and clarify complex software changes before implementation. |
| `diagnose-bugs` | Reproduce, localize, diagnose, and repair concrete local or CI defects with regression evidence. |
| `docs-audit` | Audit and rebuild repository documentation against implementation evidence. |
| `maui-blazor-browser` | Develop and verify MAUI Blazor Hybrid UI through a safe Web companion or temporary browser harness. |
| `prune-codebase` | Prove and retire dead or obsolete repository surface without guessing about consumers or compatibility. |
| `reduce-code-slop` | Review and simplify scoped C# and Python code without changing behavior or hiding diagnostics. |
| `ui-design-and-polish` | Design, audit, refine, and verify accessible product interfaces. |
| `write-clearly` | Draft, edit, and audit repository prose for clarity, reader fit, fidelity, and voice in its source language. |

## Included MCP servers

| Server | Transport | Purpose |
| --- | --- | --- |
| `context7` | Streamable HTTP | Retrieves current library documentation from Context7. |
| `microsoft-learn` | Streamable HTTP | Searches and reads public Microsoft Learn documentation. |
| `playwright` | stdio | Automates browser interactions with Playwright. |
| `web-forager` | stdio | Provides DuckDuckGo web and news search plus Jina Reader fetching. |

## Requirements and trust

- `chatgpt-research` requires ChatGPT Deep Research and signed-in in-app Browser control.
- `audit-dependencies` keeps explicit reviews read-only, does not execute dependency code or install scanners, and automatically researches only public package coordinates.
- `diagnose-bugs` keeps diagnostic evidence local and redacted, preserves existing work, and requires separate authorization for high-risk or external actions.
- `comment-health` keeps source comments and native-tool evidence local, protects comments with legal, documentation, or machine semantics, and previews broad cleanup candidates before editing.
- `prune-codebase` treats analyzer results as candidates, preserves uncertain dynamic and external consumers, and previews broad removal candidates before editing.
- `reduce-code-slop` inspects source, tests, and existing verification output locally, preserves justified complexity, and does not install analyzers or dependencies.
- `write-clearly` keeps repository prose and author samples local by default, preserves protected meaning and format, and reports related findings outside the authorized edit scope without changing those files.
- `playwright` requires Node.js 18 or newer.
- `web-forager` requires `uv` and provisions a supported Python 3.10-3.13 runtime through `uvx`.
- The MCP servers use the network, and Playwright can interact with a browser. Review tool calls and third-party terms before use.
- If Node.js or `uv` is unavailable, the affected local MCP server may be disabled while the skills and other MCP servers remain usable.

## Install the complete GitHub edition

The published `v0.2.0` GitHub marketplace edition contains ten skills and all four MCP servers. The Codex CLI is not required.

1. In ChatGPT/Codex desktop, open **Plugins**, open the **Add** menu, and select **Add plugin marketplace**.
2. Enter `Peter537/peter537-agent-plugin` as the source.
3. Enter `v0.2.0` as the Git ref.
4. Leave **Sparse paths** empty and add the marketplace.
5. Open **Peter537 Plugins**, install **Peter537 Agent Plugin**, and start a new task so its skills and MCP tools are loaded.

## Install from Skills.sh

[![skills.sh](https://skills.sh/b/Peter537/peter537-agent-plugin)](https://skills.sh/Peter537/peter537-agent-plugin)

This route installs the skill directories in this repository. It does not install `plugin.json`, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, `mcp.json`, or the four optional MCP servers.

List the available skills:

```powershell
npx skills add Peter537/peter537-agent-plugin --list
```

Install one skill:

```powershell
npx skills add Peter537/peter537-agent-plugin --skill deep-planning
```

Install every discovered skill:

```powershell
npx skills add Peter537/peter537-agent-plugin --skill "*"
```

`chatgpt-research` still requires ChatGPT Deep Research and signed-in in-app Browser control; installing it through Skills.sh does not provide those capabilities.

Skills.sh availability is separate from repository compatibility and begins only after Skills.sh has observed a telemetry-enabled installation and refreshed its catalog.

## Install from the OpenAI shared Plugins Directory

The public-directory edition is submitted separately from the GitHub release. Its `v0.2.0` bundle contains all ten skills but does not include the four MCP servers; it becomes available only after OpenAI review and publication. Once available, search for **Peter537 Agent Plugin** in the shared Plugins Directory, open its details, and select the plus button to install it.

## Optional: Codex CLI

The Codex CLI is not required to install either desktop edition. Existing CLI users can instead add and install the GitHub marketplace with:

```powershell
codex plugin marketplace add Peter537/peter537-agent-plugin --ref v0.2.0
codex plugin add peter537-agent-plugin@peter537
```

Start a new Codex CLI session after installation so the plugin components are loaded.

## Other Agent Plugins clients

Clone or download this repository and follow the installation workflow provided by your client. Conformant clients discover the root `plugin.json`, skills under `skills/`, and MCP servers in `mcp.json`; component and transport support can vary, so consult the [compatible clients list](https://agent-plugins.org/compatible-clients).

## Example requests

- `Use $audit-data-exposure to review this repository and its reachable history for personal data, private artifacts, and one-off migrations.`
- `Use $audit-dependencies to review every dependency and software supply-chain input in this repository.`
- `Use $deep-planning to plan this repository change.`
- `Use $deep-code-audit to audit this codebase.`
- `Use $diagnose-bugs to reproduce, diagnose, and fix this flaky CI failure.`
- `Use $docs-audit to refresh this project's documentation.`
- `Use $maui-blazor-browser to make this MAUI Blazor Hybrid UI safely browser-testable.`
- `Use $reduce-code-slop to simplify this C# or Python code without changing its behavior.`
- `Use $ui-design-and-polish to improve this product UI.`
- `Use $write-clearly to improve this repository prose without changing its meaning or voice.`
- `Use $chatgpt-research to compare the current official guidance.`
- `Use $comment-health to review changed source comments for accuracy, value, and protected semantics.`
- `Use $prune-codebase to find proven dead or obsolete repository surface and report removal candidates for approval.`

## Version

Current version: `0.2.0`.

## Support, privacy, and terms

See [Support](SUPPORT.md), [Privacy](PRIVACY.md), and [Terms](TERMS.md) before installing or reporting an issue.

## License

Released under the [MIT License](LICENSE).
