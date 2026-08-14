# Harness plugin layouts

Plugin structure per agent harness, focused on the three core primitives:

- **manifest** — the plugin's identity + config (`plugin.json`, `gemini-extension.json`, …)
- **MCP** — where MCP servers are declared
- **skills** — `skills/<name>/SKILL.md`

> These trees are **focused, not exhaustive.** Each harness also supports extra
> components (hooks, agents, LSP, monitors, themes, rules, …) that this tool
> neither generates nor translates, so they're omitted. Trees are validated
> against each harness's own docs (linked per section).

Who produces each layout:

| Harness | Produced by |
| --- | --- |
| Agent Plugin spec | source of truth (hand-authored / `agent-plugin-sync`) |
| Gemini CLI | `agent-plugin-sync generate` |
| Claude Code | `agent-plugin-sync generate` |
| Codex | `agent-plugin-sync generate` (`.codex-plugin/`) |
| Antigravity CLI | `agent-plugin-sync generate` (`mcp_config.json`) |

## MCP placement (our convention)

One opinionated rule keeps the plugin root clean — a single MCP file, no lookalikes:

- **Agent Plugin spec** → MCP in root `mcp.json`. The spec's *only* option; inline
  config and alternate paths are forbidden (§7.2.1, §7.2.2).
- **Vendors inline their own MCP** in their manifest — Gemini in
  `gemini-extension.json`, Claude in `.claude-plugin/plugin.json` (`mcpServers`).
- **No `.mcp.json` at the root.** The sole root-level MCP file is the spec's `mcp.json`.
- **Codex** reads `.codex-plugin/.mcp.json` (legacy), referenced from
  `.codex-plugin/plugin.json`. It can't pass user env vars through the spec
  `mcp.json` yet, so we don't route it there.
- **Antigravity** reads its own root `mcp_config.json`.

---

## Agent Plugin spec

Source: https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md

```
<plugin-root>/
├── plugin.json            # REQUIRED — manifest ($schema, name; + version, description,
│                          #            author, homepage, repository, license, keywords, extensions)
├── mcp.json               # optional — MCP servers ($schema, mcpServers)
└── skills/                # optional
    └── <name>/SKILL.md    #   REQUIRED per skill (frontmatter: name, description)
```

- Only `plugin.json` is required, **plus at least one component** (skills or MCP).
- MCP loads **only** from root `mcp.json` — inline config / alternate paths forbidden.
- Skill discovery is **non-recursive** (immediate children of `skills/`).

> The spec requires `$schema`, but our **shipped** `plugin.json` currently omits
> it so Codex routes to `.codex-plugin/` (see [Codex](#codex)). It goes back once
> Codex can pass user config through the spec.

---

## Gemini CLI

Source: https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md

```
<extension-root>/
├── gemini-extension.json  # REQUIRED — manifest (name, version)
│                          #   MCP: inline `mcpServers` map
│                          #   config: `settings[]` (name, description, envVar, sensitive)
├── GEMINI.md              # optional — context file (name set by contextFileName)
└── skills/                # optional
    └── <name>/SKILL.md
```

- MCP is **inline** in the manifest (matches our convention).

---

## Claude Code

Source: https://code.claude.com/docs/en/plugins-reference

```
<plugin-root>/
├── .claude-plugin/
│   └── plugin.json        # REQUIRED — manifest (name; + version, description, author,
│                          #            homepage, repository, license)
│                          #   MCP: inline `mcpServers` (our choice; .mcp.json also supported)
│                          #   config: `userConfig`
└── skills/                # optional — at the root, NOT inside .claude-plugin/
    └── <name>/SKILL.md
```

- **Only `plugin.json` goes in `.claude-plugin/`.** `skills/` (and everything else) live at the plugin root.
- MCP paths use `${CLAUDE_PLUGIN_ROOT}` (spec's `${PLUGIN_ROOT}` is retargeted on generate).

---

## Codex

Sources: https://learn.chatgpt.com/docs/build-plugins · https://developers.openai.com/plugins/build/plugins

Codex reads the Agent Plugin spec, but its spec `mcp.json` cannot pass user
environment variables to an MCP server: `env_vars` is rejected, `${VAR}` in `env`
is not expanded, and the ambient env is cleared
([openai/codex#36854](https://github.com/openai/codex/issues/36854)). So we
generate Codex's **legacy** `.codex-plugin/` layout in every case, which does
forward `env_vars`.

```
<plugin-root>/
├── plugin.json               # spec manifest, but WITHOUT $schema (see below)
├── .codex-plugin/
│   ├── plugin.json           # legacy manifest; mcpServers -> "./.codex-plugin/.mcp.json"
│   └── .mcp.json             # legacy MCP: command/args + env_vars (forwarded from user env)
└── skills/
    └── <name>/SKILL.md
```

- **Omit `$schema` from the root `plugin.json`.** Codex treats a root manifest as
  Agent Plugin only when its `$schema` is an `agent-plugins.org` URI; without it,
  Codex falls through to `.codex-plugin/`.
- The `mcpServers` path in `.codex-plugin/plugin.json` is **root-relative**
  (`./.codex-plugin/.mcp.json`), not relative to `.codex-plugin/`.
- `.codex-plugin/.mcp.json` uses `env_vars: [...]` so the user's environment
  reaches the server, the capability the spec `mcp.json` lacks.
- Install/discovery still needs a marketplace descriptor (`.claude-plugin/marketplace.json`).

> When Codex can pass user config through the spec, add `$schema` back and drop
> this generator; Codex (and the other spec-only clients) then read the spec directly.

---

## Antigravity CLI

Sources: https://antigravity.google/docs/cli/plugins · https://antigravity.google/docs/cli/gcli-migration

`agy plugin install` reads the root `plugin.json` leniently (name, description,
sibling `skills/`) but takes MCP only from its own `mcp_config.json`, never the
spec's `mcp.json`. So we generate `mcp_config.json` alongside the spec files.

```
<plugin-root>/
├── plugin.json            # spec manifest (AGY ignores $schema/version/extensions)
├── mcp_config.json        # MCP servers for AGY — subset of mcp.json (same mcpServers,
│                          #   without $schema or per-server type)
└── skills/
    └── <name>/SKILL.md
```

- MCP comes from `mcp_config.json`; the spec's `mcp.json` is ignored by AGY.
- AGY doesn't track version, so there's no in-place upgrade.
