"""agent-plugin-sync CLI.

Two core commands:

    agent-plugin-sync generate  [root]   Write all harness manifests from plugin.json
    agent-plugin-sync validate  [root]   Check a plugin is in good shape:
                                         source is valid AND generated files are current

One-time onboarding utility:

    agent-plugin-sync migrate [root] [--force]   Seed plugin.json + mcp.json from gemini-extension.json

[root] defaults to the current directory. It may be a single plugin (contains
plugin.json) or a monorepo (plugin.json in subdirectories); every plugin found is
processed.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

from agent_plugin_sync import generators, io, loader, migrate, validate
from agent_plugin_sync.generators import artifact


def main(argv: list[str] | None = None) -> None:
    """Parse arguments and dispatch to the selected command."""
    parser = argparse.ArgumentParser(prog="agent-plugin-sync")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "validate", "migrate"):
        p = sub.add_parser(name)
        p.add_argument("root", nargs="?", default=".", help="plugin root or monorepo (default: .)")
        if name == "migrate":
            p.add_argument("--force", action="store_true", help="overwrite existing plugin.json")

    args = parser.parse_args(argv)
    root = pathlib.Path(args.root).resolve()

    if args.command == "generate":
        cmd_generate(root)
    elif args.command == "validate":
        cmd_validate(root)
    elif args.command == "migrate":
        cmd_migrate(root, args.force)


def cmd_generate(root: pathlib.Path) -> None:
    """Write all harness manifests for each plugin found."""
    roots = _resolve_roots(root, "plugin.json")
    multi = len(roots) > 1
    for plugin_root in roots:
        if multi:
            print(f"# {_label(root, plugin_root)}")
        for f in _build_outputs(plugin_root):
            io.write_file(plugin_root / f.path, f.contents)
            print(f"✔ wrote {f.path}")


def cmd_validate(root: pathlib.Path) -> None:
    """Check each plugin: source is valid AND generated files are up to date."""
    roots = _resolve_roots(root, "plugin.json")
    ok = True
    for plugin_root in roots:
        label = _label(root, plugin_root)
        result = validate.validate_plugin(plugin_root)
        if not result.ok:
            ok = False
            print(f"✖ {label}: invalid source", file=sys.stderr)
            for e in result.errors:
                print(f"  - {e}", file=sys.stderr)
            continue
        stale = _stale_files(plugin_root)
        if stale:
            ok = False
            print(f"✖ {label}: generated files out of date", file=sys.stderr)
            for s in stale:
                print(f"  - {s}", file=sys.stderr)
        else:
            print(f"✔ {label}: valid and up to date")
    if not ok:
        _fail("run `agent-plugin-sync generate` and commit, then re-validate")


def cmd_migrate(root: pathlib.Path, force: bool) -> None:
    """Seed plugin.json + mcp.json from gemini-extension.json for each plugin found."""
    roots = _resolve_roots(root, "gemini-extension.json")
    multi = len(roots) > 1
    for plugin_root in roots:
        if multi:
            print(f"# {_label(root, plugin_root)}")
        plugin_path = plugin_root / "plugin.json"
        if plugin_path.exists() and not force:
            print(f"↷ skip {plugin_path} (exists; use --force to overwrite)")
            continue
        result = migrate.migrate(plugin_root)
        io.write_json(plugin_path, result.plugin)
        print(f"✔ wrote {plugin_path}")
        if result.mcp is not None:
            mcp_path = plugin_root / "mcp.json"
            io.write_json(mcp_path, result.mcp)
            print(f"✔ wrote {mcp_path}")
    print("→ Review inferred fields (required, default, homepage, keywords) before committing.")


def _resolve_roots(root: pathlib.Path, marker: str) -> list[pathlib.Path]:
    roots = loader.discover_roots(root, marker)
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
    return generators.generate_all(loader.load_model(plugin_root))


def _stale_files(plugin_root: pathlib.Path) -> list[str]:
    """Paths whose on-disk contents differ from freshly generated output."""
    stale: list[str] = []
    for f in generators.generate_all(loader.load_model(plugin_root)):
        path = plugin_root / f.path
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != f.contents:
            stale.append(f.path)
    return stale


def _label(root: pathlib.Path, plugin_root: pathlib.Path) -> str:
    """Short name for a plugin root, relative to the invocation root."""
    return plugin_root.name if plugin_root == root else str(plugin_root.relative_to(root))


def _fail(message: str) -> None:
    print(f"✖ {message}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
