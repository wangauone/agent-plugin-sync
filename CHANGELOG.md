# Changelog

## [0.1.4](https://github.com/wangauone/agent-plugin-sync/compare/0.1.3...0.1.4) (2026-08-26)


### Features

* require $schema in plugin.json ([#4](https://github.com/wangauone/agent-plugin-sync/issues/4)) ([a2ed746](https://github.com/wangauone/agent-plugin-sync/commit/a2ed7460acc2bf78484b44cc03af974728bb7b25))

## [0.1.3](https://github.com/wangauone/agent-plugin-sync/compare/0.1.2...0.1.3) (2026-08-24)


### Bug Fixes

* **ci:** read job.workflow_sha in step env, not job env ([00dca68](https://github.com/wangauone/agent-plugin-sync/commit/00dca685ab3a7eeedab7666db406a3d163d2684c))

## [0.1.2](https://github.com/wangauone/agent-plugin-sync/compare/0.1.1...0.1.2) (2026-08-20)


### Features

* **ci:** move a stable tag on each release for ad-hoc runs ([6502afe](https://github.com/wangauone/agent-plugin-sync/commit/6502afe71e762d4e438d4df01876d843eb3a8e88))


### Bug Fixes

* **ci:** move the stable tag through the refs API ([07a4ba7](https://github.com/wangauone/agent-plugin-sync/commit/07a4ba71aa3ed2129fcf96a9729955b15e0dc1d4))
* **ci:** point stable at the latest release, not the branch head ([8d6ecc7](https://github.com/wangauone/agent-plugin-sync/commit/8d6ecc7a30b1bbcfdc80634a95eaeba9d65ee8db))
* **ci:** resolve the tool version from job_workflow_sha ([8dcdfb3](https://github.com/wangauone/agent-plugin-sync/commit/8dcdfb325edf0175b6f9a7ec2283867175cdd4fe))
* **ci:** use job.workflow_sha, the documented context name ([7aa088f](https://github.com/wangauone/agent-plugin-sync/commit/7aa088f0449daa0855a7206893e07ec6fe0237b8))

## [0.1.1](https://github.com/wangauone/agent-plugin-sync/compare/0.1.0...0.1.1) (2026-08-20)


### Features

* add agent-plugin-sync harness manifest generator ([0826fc6](https://github.com/wangauone/agent-plugin-sync/commit/0826fc66f7adb4412b7e544383c72eb8bd913d01))
* add Codex/Antigravity generators, enforce no $schema, rename extension models to PluginExtension ([a488de5](https://github.com/wangauone/agent-plugin-sync/commit/a488de5ac906b704fcfbe70871d80f3cf82a480b))
* carry the Codex interface block through generation ([e147e1f](https://github.com/wangauone/agent-plugin-sync/commit/e147e1f7f4ef665a3d8de64e87536d68aab3f898))


### Bug Fixes

* only emit cwd for ./-relative commands in migrate ([9c18e21](https://github.com/wangauone/agent-plugin-sync/commit/9c18e2124b31ebf5b58af3f3b1aae9dd1f6c2886))
* translate plugin-root path placeholders in args (migrate + gemini) ([ea9f29e](https://github.com/wangauone/agent-plugin-sync/commit/ea9f29eec8df313e7697f3c1f350fc165377a0a2))
