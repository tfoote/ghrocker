# ghrocker

## Overview

This is an extension for rocker https://github.com/osrf/rocker

It provides bindings to locally test a site expected to be hosted in github pages locally. 

## Usage

    ghrocker PATH_TO_GH_PAGES_REPOSITORY


The browse to http://localhost:4000
Or launch it via:

    sensible-browser http://localhost:4000

## Releasing to PyPI

Publishing `ghrocker` to PyPI is automated via GitHub Actions using [PyPI Trusted Publishing (OIDC)](https://docs.pypi.org/trusted-publishers/), eliminating the need for manually managed API tokens.

### How It Works & What Is Configured

The workflow defined in [`.github/workflows/publish-pypi.yaml`](.github/workflows/publish-pypi.yaml) is split into two isolated jobs:
1. **`build`**: Checks out the repository, installs `build`, builds the source distribution (`.tar.gz`) and wheel (`.whl`) into `dist/`, and uploads them as a build artifact.
2. **`publish-to-pypi`**: Runs in the dedicated `pypi` GitHub Actions environment with `id-token: write` permission (and without repository checkout access). It downloads the built distribution artifacts and uses [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish) to exchange a short-lived GitHub OIDC token with PyPI to publish the release.

**Trusted Publisher Configuration on PyPI (`https://pypi.org/p/ghrocker`):**
- **Owner**: `tfoote`
- **Repository**: `ghrocker`
- **Workflow name**: `publish-pypi.yaml`
- **Environment name**: `pypi`

### Steps to Trigger a Release

1. **Bump the version**: Update the `version` field in [`pyproject.toml`](pyproject.toml) (e.g., `"0.0.11"`), commit, and merge/push to `main`.
2. **Publish a GitHub Release**:
   - Via the GitHub UI: Go to [Releases -> Draft a new release](https://github.com/tfoote/ghrocker/releases/new), create/select a tag matching the version (e.g., `v0.0.11`), add release notes, and click **Publish release**.
   - Or via the GitHub CLI:
     ```bash
     gh release create v0.0.11 --generate-notes
     ```
3. **Verify**: Publishing the release automatically triggers the `Publish to PyPI` workflow. You can also trigger the workflow manually at any time from the **Actions** tab via `workflow_dispatch`.

