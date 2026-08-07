# Peter537 Agent Plugin

Peter537 Agent Plugin is a portable [Agent Plugins v1](https://agent-plugins.org/) package containing reusable skills and MCP integrations for software research, planning, audits, documentation, UI design, and development workflows. Codex displays it as **Peter537 Agent Plugin**.

## Included skills

| Skill | Purpose |
| --- | --- |
| `chatgpt-research` | Orchestrate and verify multi-source ChatGPT Deep Research. |
| `deep-code-audit` | Audit correctness, security, architecture, dependencies, and maintainability. |
| `deep-planning` | Research and clarify complex software changes before implementation. |
| `docs-audit` | Audit and rebuild repository documentation against implementation evidence. |
| `ui-design-and-polish` | Design, audit, refine, and verify accessible product interfaces. |

## Included MCP servers

| Server | Transport | Purpose |
| --- | --- | --- |
| `context7` | Streamable HTTP | Retrieves current library documentation from Context7. |
| `microsoft-learn` | Streamable HTTP | Searches and reads public Microsoft Learn documentation. |
| `playwright` | stdio | Automates browser interactions with Playwright. |
| `web-forager` | stdio | Provides DuckDuckGo web and news search plus Jina Reader fetching. |

## Requirements and trust

- `chatgpt-research` requires ChatGPT Deep Research and signed-in in-app Browser control.
- `playwright` requires Node.js 18 or newer.
- `web-forager` requires `uv` and provisions a supported Python 3.10-3.13 runtime through `uvx`.
- The MCP servers use the network, and Playwright can interact with a browser. Review tool calls and third-party terms before use.
- If Node.js or `uv` is unavailable, the affected local MCP server may be disabled while the skills and other MCP servers remain usable.

## Install in ChatGPT/Codex desktop

### Local repository

1. Clone or download this repository and open it as the active repository in Codex.
2. Restart the ChatGPT desktop app so it discovers `.agents/plugins/marketplace.json`.
3. Open **Plugins**, choose **Peter537 Plugins**, open **Peter537 Agent Plugin**, and select the plus button to install it.
4. Start a new task so the installed skills and MCP tools are loaded.

### Public directory

After the plugin is published to the shared Plugins Directory, search for **Peter537 Agent Plugin**, open its details, and select the plus button to install it.

## Optional: Codex CLI

The Codex CLI is not required to use this plugin in the ChatGPT desktop app. If you already use the CLI, run these commands from the repository root to add its local marketplace and install the plugin:

```powershell
codex plugin marketplace add .
codex plugin add peter537-agent-plugin@peter537
```

Start a new Codex CLI session after installation so the plugin components are loaded.

## Other Agent Plugins clients

Clone or download this repository and follow the installation workflow provided by your client. Conformant clients discover the root `plugin.json`, skills under `skills/`, and MCP servers in `mcp.json`; component and transport support can vary, so consult the [compatible clients list](https://agent-plugins.org/compatible-clients).

## Example requests

- `Use $deep-planning to plan this repository change.`
- `Use $deep-code-audit to audit this codebase.`
- `Use $docs-audit to refresh this project's documentation.`
- `Use $ui-design-and-polish to improve this product UI.`
- `Use $chatgpt-research to compare the current official guidance.`

## Version

Current version: `0.1.0`.

## License

Released under the [MIT License](LICENSE).
