# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [unreleased]

## [1.0.0] -- 2026-11-27

### Added
- Initial release of `github-workflows`.
- Reusable cross-platform matrix CI workflow (`.github/workflows/ci.yml`).
- Reusable SemVer release workflow with automated changelog management (`.github/workflows/release.yml`).
- Reusable branch snapshot pre-release workflow (`.github/workflows/snapshot.yml`).
- Standalone release version bumper script (`.github/scripts/release_version.py`).
- Automated test suite for release script and version calculation (`tests/run_tests.sh`).
