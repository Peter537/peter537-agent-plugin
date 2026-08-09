# Ecosystem Evidence and Safe Commands

Use this reference to identify exact-resolution evidence and select commands that do not install packages or execute dependency code. Confirm the behavior of the installed tool version before running any command; package-manager behavior and flags change.

## Contents

- [Common rules](#common-rules)
- [Language ecosystems](#language-ecosystems)
- [Containers and infrastructure](#containers-and-infrastructure)
- [CI and runtime-loaded inputs](#ci-and-runtime-loaded-inputs)
- [Primary references](#primary-references)

## Common rules

- Prefer an existing authoritative lockfile, SBOM, package-manager metadata, immutable digest, or Git SHA over fresh resolution.
- Run only already-installed tools. Do not install a scanner or package manager merely to complete a review.
- Avoid commands that restore, install, update, compile, load plugins, or run lifecycle hooks. A command named `list`, `tree`, `audit`, or `check` can still resolve packages, contact registries, write caches, or execute build logic.
- Before a networked audit, determine whether the tool sends package coordinates, lockfiles, SBOMs, source, or registry configuration. Filter to public coordinates or use offline data unless the user authorizes transmission of private inputs.
- Use a temporary isolated copy only when the user has authorized resolution and the resolver can disable scripts. Never generate or rewrite a lockfile in the reviewed working tree during a read-only review.
- Record the package-manager and scanner versions because lock interpretation and advisory behavior can differ by version.
- Check all workspaces, optional groups, development and test groups, build plugins, and platform-specific sections. A root lockfile may or may not cover every nested project.
- Compare manifest and lockfile consistency. Exact entries in a stale or partial lockfile are not reliable evidence of the requested graph.

## Language ecosystems

| Ecosystem | Dependency-bearing files and exact evidence | Safe inspection when already installed | Execution or coverage hazards |
| --- | --- | --- | --- |
| JavaScript / TypeScript | `package.json`, `package-lock.json`, `npm-shrinkwrap.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `yarn.lock`, `.yarnrc.yml`, `bun.lock`, version catalogs | Parse the lockfile; use `npm audit --package-lock-only --json` only after confirming it will not modify files; use existing lockfile-aware OSV scanning | `npm`, `pnpm`, Yarn, and Bun installs can run lifecycle scripts; tree commands may depend on mutable `node_modules`; registry and override settings can redirect identities |
| Python | `pyproject.toml`, `requirements*.txt`, constraints, `uv.lock`, `poetry.lock`, `pdm.lock`, `Pipfile.lock`, `pylock.toml`, wheel metadata | Parse the lock; use an already-installed `pip-audit` against explicit locked inputs or an existing environment; use lockfile-aware OSV scanning | Resolution can run legacy setup code, build wheels, contact private indexes, or mutate environments; unpinned requirements do not establish exact transitive versions |
| .NET | project files, `Directory.Packages.props`, `packages.config`, `packages.lock.json`, `project.assets.json`, `.deps.json`, solution files | Parse lock/assets files; use `dotnet package list --include-transitive --vulnerable --no-restore` or the installed SDK's equivalent only when the no-restore behavior is supported | Listing can implicitly restore without `--no-restore`; MSBuild evaluation and custom targets can execute code; central and conditional versions require per-target evaluation |
| Go | `go.mod`, `go.sum`, `go.work`, `vendor/modules.txt` | Parse `go.mod` and vendor metadata; use already-installed OSV-Scanner or `govulncheck` only after confirming its analysis mode and network behavior | `go.sum` proves checksums, not the selected graph by itself; commands may download modules; replace directives and private module proxies can change identity |
| Rust | `Cargo.toml`, `Cargo.lock`, workspace manifests | Parse `Cargo.lock`; use already-installed `cargo audit`; use `cargo tree --locked` only if it will not fetch or build | Cargo resolution can access registries; proc macros and `build.rs` execute code during builds; OSV-Scanner Rust call analysis compiles dependencies and executes `build.rs` |
| JVM (Maven / Gradle) | `pom.xml`, Gradle build and settings files, version catalogs, dependency lockfiles, `verification-metadata.xml`, wrapper properties | Parse committed locks and verification metadata; run an existing scanner against those files | Maven and Gradle dependency tasks can download artifacts and execute settings, build scripts, plugins, extensions, or init scripts; Maven transitive OSV resolution can send public coordinates to deps.dev or a registry |
| PHP | `composer.json`, `composer.lock` | Parse `composer.lock`; use `composer audit --locked --format=json` only after verifying installed-version behavior | Never run `composer install` for an audit; plugins and scripts can execute code; repositories can override Packagist identity |
| Ruby | `Gemfile`, `Gemfile.lock`, `*.gemspec`, `gems.locked` | Parse the lockfile; use already-installed `bundle-audit` without updating its database unless network use is acceptable | `bundle install`, gem extensions, plugins, and gemspec evaluation can execute code; multiple platforms may resolve differently |
| Dart / Flutter | `pubspec.yaml`, `pubspec.lock`, workspace files | Parse `pubspec.lock`; use an existing advisory scanner that understands Dart | `pub get` resolves and writes state; Git and path dependencies need separate commit or source verification; build hooks can execute code |
| Elixir / Erlang | `mix.exs`, `mix.lock`, Rebar config and lockfiles | Parse `mix.lock` and Rebar locks; use installed Hex audit capabilities only if they do not mutate | Evaluating Mix projects and fetching Hex/Rebar dependencies can execute project or dependency code and write caches |
| Haskell | `*.cabal`, `cabal.project`, `cabal.project.freeze`, `stack.yaml`, `stack.yaml.lock` | Parse freeze and lock files; inspect immutable package hashes and Git commits | Solver and build commands can download, configure, and compile packages; flags and compiler versions affect the graph |
| R | `DESCRIPTION`, `renv.lock`, `pak.lock`, repository configuration | Parse the lockfile and repository fields; inspect installed package metadata without loading packages | Restoring or loading R packages can run install hooks, compile native code, and contact configured repositories |
| C / C++ | `conanfile.*`, `conan.lock`, `vcpkg.json`, `vcpkg-configuration.json`, CMake dependency declarations, Meson wraps, Bazel modules/workspaces, vendored trees | Parse lockfiles, checksums, wrapper metadata, Git SHAs, and vendored provenance; use OSV commit scanning when appropriate | Build configuration can execute arbitrary commands; vendored-version detection is approximate; registries and source archives require independent integrity checks |

Also inventory Swift package manifests and resolved files, CocoaPods and Carthage locks, NuGet central catalogs, Bazel modules, Nix flakes and locks, Terraform providers, Helm chart locks, pre-commit hooks, and any repository-specific resolver not covered above. Mark unsupported exact resolution explicitly instead of omitting it.

## Containers and infrastructure

- Inventory every `FROM`, `image:`, build-stage, service, job container, devcontainer feature, Helm chart, Terraform provider/module, and downloaded binary or script.
- Prefer immutable OCI digests. A tag, including a semantic version or `latest`, is not immutable exact evidence. Record the publisher and registry as part of identity.
- Scan an image only with an already-installed scanner and without pulling or running it unless the user authorizes those actions. Distinguish the declared base from the locally present image and the deployed digest.
- Inspect package installation commands inside container definitions and the lock or repository snapshot they use. A digest-pinned base does not pin later `apt`, `apk`, `pip`, or other network installations.
- Treat Terraform `.terraform.lock.hcl`, Helm `Chart.lock`, provider checksums, module Git SHAs, Nix `flake.lock`, and similar files as supply-chain evidence, while verifying that all supported target platforms are represented.

## CI and runtime-loaded inputs

- Record every GitHub Action `uses:` coordinate, reusable workflow, CI orb/plugin, job image, downloaded tool, package-manager bootstrap, and release action. Prefer immutable commit SHAs for third-party actions and verify that the SHA belongs to the expected repository and release.
- Review CI token permissions, secret access, fork behavior, artifact handling, cache poisoning boundaries, and scripts fetched with `curl`, `wget`, PowerShell, or package runners.
- Inventory runtime plugins, extension manifests, drivers, providers, MCP servers, browser extensions, model downloads, dynamically loaded libraries, and executable assets. Resolve their source, exact version or digest, integrity evidence, privileges, and update path.
- Treat local path dependencies as first-party only after verifying that they stay inside the intended repository boundary. Treat Git URLs, archives, URL dependencies, and private registries as separate identities.

## Primary references

- [OSV-Scanner project source scanning](https://google.github.io/osv-scanner/usage/scan-source)
- [OSV-Scanner supported artifacts and manifests](https://google.github.io/osv-scanner/supported-languages-and-lockfiles/)
- [GitHub guidance for secure use of third-party actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [OCI image specification](https://github.com/opencontainers/image-spec)
- [Package URL specification](https://github.com/package-url/purl-spec)
