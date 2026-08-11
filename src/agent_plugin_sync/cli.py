"""agent-plugin-sync CLI.

    agent-plugin-sync bootstrap [root] [--force]   Seed plugin.json + mcp.json from gemini-extension.json (one-time)
    agent-plugin-sync generate  [root]             Write all harness manifests from plugin.json
    agent-plugin-sync check     [root]             Fail if any output is stale (CI drift guard)
    agent-plugin-sync validate  [root]             Validate the com.google.cloud source against its schema

[root] defaults to the current directory. It may be a single plugin (contains
plugin.json) or a monorepo (plugin.json in subdirectories); every plugin found is
processed.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from agent_plugin_sync import bootstrap, generators, io, model, validate
from agent_plugin_sync.generators import artifact


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="agent-plugin-sync")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("bootstrap", "generate", "check", "validate"):
        p = sub.add_parser(name)
        p.add_argument("root", nargs="?", default=".", help="plugin root or monorepo (default: .)")
        if name == "bootstrap":
            p.add_argument("--force", action="store_true", help="overwrite existing plugin.json")

    args = parser.parse_args(argv)
    root = pathlib.Path(args.root).resolve()

    if args.command == "bootstrap":
        cmd_bootstrap(root, args.force)
    elif args.command == "generate":
        cmd_generate(root)
    elif args.command == "check":
        cmd_check(root)
    elif args.command == "validate":
        cmd_validate(root)


def cmd_bootstrap(root: pathlib.Path, force: bool) -> None:
    roots = _resolve_roots(root, "gemini-extension.json")
    multi = len(roots) > 1
    for plugin_root in roots:
        if multi:
            print(f"# {_label(root, plugin_root)}")
        plugin_path = plugin_root / "plugin.json"
        if plugin_path.exists() and not force:
            print(f"↷ skip {plugin_path} (exists; use --force to overwrite)")
            continue
        result = bootstrap.bootstrap(plugin_root)
        io.write_json(plugin_path, result.plugin)
        print(f"✔ wrote {plugin_path}")
        if result.mcp is not None:
            mcp_path = plugin_root / "mcp.json"
            io.write_json(mcp_path, result.mcp)
            print(f"✔ wrote {mcp_path}")
    print("→ Review inferred fields (required, default, homepage, keywords) before committing.")


def cmd_generate(root: pathlib.Path) -> None:
    roots = _resolve_roots(root, "plugin.json")
    multi = len(roots) > 1
    for plugin_root in roots:
        if multi:
            print(f"# {_label(root, plugin_root)}")
        for f in _build_outputs(plugin_root):
            io.write_file(plugin_root / f.path, f.contents)
            print(f"✔ wrote {f.path}")


def cmd_check(root: pathlib.Path) -> None:
    roots = _resolve_roots(root, "plugin.json")
    checked = 0
    stale: list[str] = []
    for plugin_root in roots:
        for f in _build_outputs(plugin_root):
            checked += 1
            path = plugin_root / f.path
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != f.contents:
                stale.append(f"{_label(root, plugin_root)}: {f.path}")
    if stale:
        for s in stale:
            print(f"  - out of date: {s}", file=sys.stderr)
        _fail("generated files are stale; run `agent-plugin-sync generate` and commit")
    print(f"✔ all {checked} generated files up to date across {len(roots)} plugin(s)")


def cmd_validate(root: pathlib.Path) -> None:
    roots = _resolve_roots(root, "plugin.json")
    multi = len(roots) > 1
    all_ok = True
    for plugin_root in roots:
        result = validate.validate_plugin(plugin_root)
        if result.ok:
            print(f"✔ {_label(root, plugin_root)}: valid" if multi else "✔ source is valid")
        else:
            all_ok = False
            print(f"✖ {_label(root, plugin_root)}:", file=sys.stderr)
            for e in result.errors:
                print(f"  - {e}", file=sys.stderr)
    if not all_ok:
        _fail("source failed schema validation")


def _resolve_roots(root: pathlib.Path, marker: str) -> list[pathlib.Path]:
    roots = model.discover_roots(root, marker)
    if not roots:
        _fail(f"no {marker} found at or under {root}")
    return roots


def _build_outputs(plugin_root: pathlib.Path) -> list[artifact.GeneratedFile]:
    """Validate, then produce the output files for one plugin (in memory)."""
    result = validate.validate_plugin(plugin_root)
    if not result.ok:
        for e in result.errors:
            print(f"  - {e}", file=sys.stderr)
        _fail(f"{plugin_root}: source failed validation; fix plugin.json and retry")
    return generators.generate_all(model.load_model(plugin_root))


def _label(root: pathlib.Path, plugin_root: pathlib.Path) -> str:
    """Short name for a plugin root, relative to the invocation root."""
    return plugin_root.name if plugin_root == root else str(plugin_root.relative_to(root))


def _fail(message: str) -> None:
    print(f"✖ {message}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
