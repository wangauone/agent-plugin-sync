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
| Codex | reads the Agent Plugin spec files directly (no vendor file) |
| Antigravity CLI | `agy plugin import gemini` (converts the Gemini output) |

## MCP placement (our convention)

One opinionated rule keeps the plugin root clean — a single MCP file, no lookalikes:

- **Agent Plugin spec** → MCP in root `mcp.json`. The spec's *only* option; inline
  config and alternate paths are forbidden (§7.2.1, §7.2.2).
- **Vendors inline their own MCP** in their manifest — Gemini in
  `gemini-extension.json`, Claude in `.claude-plugin/plugin.json` (`mcpServers`).
- **No `.mcp.json` at the root.** The sole root-level MCP file is the spec's `mcp.json`.
- **Codex** reads the spec's root `mcp.json`, so it needs no vendor MCP file.

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

Codex is adopting the Agent Plugin spec, so it reads the **spec files directly** —
its layout is the [Agent Plugin spec](#agent-plugin-spec) tree (`plugin.json` +
`mcp.json` + `skills/`). `agent-plugin-sync` generates **no** Codex-specific files.

> Native (pre-spec) Codex used `.codex-plugin/plugin.json` referencing MCP via an
> `mcpServers` path field. We rely on the spec path instead.

---

## Antigravity CLI

Sources: https://antigravity.google/docs/cli/plugins · https://antigravity.google/docs/cli/gcli-migration

We don't author AGY files. AGY support goes through the **Gemini** path: install the
Gemini extension, then `agy plugin import gemini`, which converts it (manifest, MCP,
and skills) into AGY's native layout below.

```
~/.gemini/antigravity-cli/plugins/<name>/   # produced by `agy plugin import gemini`
├── plugin.json            # manifest ($schema, name; optional description)
├── mcp_config.json        # MCP servers (from the Gemini extension's mcpServers)
└── skills/                # from the Gemini extension's skills/
```
