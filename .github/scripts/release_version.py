#!/usr/bin/env python3
import os
import sys
import re
import datetime
import subprocess
import argparse

CHANGELOG_FILE = 'CHANGELOG.md'

def parse_semver(version_str):
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Version '{version_str}' is not in SemVer format (X.Y.Z)")
    return int(parts[0]), int(parts[1]), int(parts[2])

def get_latest_stable_version():
    """
    Finds the latest stable SemVer release version (X.Y.Z) in the repository.
    Ignores pre-release and snapshot tags (e.g. 1.0.1-feature.1).
    """
    semver_pattern = re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$')

    # 1. Try tags reachable from HEAD
    try:
        tags = subprocess.check_output(
            ["git", "tag", "--merged", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        stable_tags = []
        for t in tags:
            m = semver_pattern.match(t.strip())
            if m:
                stable_tags.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        if stable_tags:
            stable_tags.sort()
            latest = stable_tags[-1]
            return f"{latest[0]}.{latest[1]}.{latest[2]}"
    except Exception:
        pass

    # 2. Try all tags in the repository
    try:
        tags = subprocess.check_output(
            ["git", "tag", "-l"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        stable_tags = []
        for t in tags:
            m = semver_pattern.match(t.strip())
            if m:
                stable_tags.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
        if stable_tags:
            stable_tags.sort()
            latest = stable_tags[-1]
            return f"{latest[0]}.{latest[1]}.{latest[2]}"
    except Exception:
        pass

    # 3. Try reading latest stable version heading from CHANGELOG.md
    if os.path.exists(CHANGELOG_FILE):
        try:
            with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    m = re.match(r'^##\s*\[(\d+\.\d+\.\d+)\]', line.strip())
                    if m:
                        return m.group(1)
        except Exception:
            pass

    return "0.1.0"

def bump_semver(current_version, bump_type):
    major, minor, patch = parse_semver(current_version)
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        raise ValueError(f"Unknown bump type: '{bump_type}'. Expected 'patch', 'minor', or 'major'.")
    return f"{major}.{minor}.{patch}"

def get_current_branch(explicit_branch=None):
    if explicit_branch:
        return explicit_branch.strip()
    
    env_branch = os.environ.get('GITHUB_REF_NAME') or os.environ.get('BRANCH_NAME')
    if env_branch:
        return env_branch.strip()
    
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        if branch:
            return branch
    except Exception:
        pass

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        if branch and branch != "HEAD":
            return branch
    except Exception:
        pass

    return "main"

def compute_snapshot_version(base_stable_version, branch_name):
    major, minor, patch = parse_semver(base_stable_version)
    bumped_patch = f"{major}.{minor}.{patch + 1}"
    branch_slug = re.sub(r'[/]+', '-', branch_name.strip()).strip('-')
    
    tag_pattern = re.compile(rf"^v?{re.escape(bumped_patch)}-{re.escape(branch_slug)}\.(\d+)$")
    suffixes = []
    try:
        tags = subprocess.check_output(
            ["git", "tag", "-l"],
            stderr=subprocess.DEVNULL
        ).decode('utf-8').splitlines()
        for t in tags:
            m = tag_pattern.match(t.strip())
            if m:
                suffixes.append(int(m.group(1)))
    except Exception:
        pass

    next_suffix = max(suffixes) + 1 if suffixes else 1
    return f"{bumped_patch}-{branch_slug}.{next_suffix}"

def update_changelog_file(new_version):
    today = datetime.date.today().isoformat()
    new_release_heading = f"## [{new_version}] -- {today}"
    
    if not os.path.exists(CHANGELOG_FILE):
        content = f"# Changelog\n\n## [unreleased]\n\n{new_release_heading}\n"
    else:
        with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        if re.search(r'^## \[unreleased\]\s*$', content, flags=re.MULTILINE):
            content = re.sub(
                r'^## \[unreleased\]\s*$',
                f"## [unreleased]\n\n{new_release_heading}",
                content,
                count=1,
                flags=re.MULTILINE
            )
        else:
            content = f"# Changelog\n\n## [unreleased]\n\n{new_release_heading}\n\n" + content

    with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    parser = argparse.ArgumentParser(description="SemVer bumper and Keep a Changelog manager")
    parser.add_argument("action", choices=["patch", "minor", "major", "snapshot"],
                        help="Action to perform: SemVer bump (patch, minor, major) for official release, or snapshot")
    parser.add_argument("--branch", dest="branch", default=None,
                        help="Branch name for snapshot pre-releases (auto-detected if omitted)")
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true",
                        help="Preview version calculation without modifying CHANGELOG.md")
    
    args = parser.parse_args()
    current_stable = get_latest_stable_version()

    if args.action == "snapshot":
        branch = get_current_branch(args.branch)
        new_version = compute_snapshot_version(current_stable, branch)
        prefix = "[Dry Run] " if args.dry_run else ""
        print(f"{prefix}Branch snapshot pre-release ('{branch}'): {current_stable} -> {new_version}")
        print(f"{prefix}CHANGELOG.md left untouched for snapshot release.")
    else:
        new_version = bump_semver(current_stable, args.action)
        if args.dry_run:
            print(f"[Dry Run] Official release SemVer bump ({args.action}): {current_stable} -> {new_version}")
            print(f"[Dry Run] CHANGELOG.md would be updated with: ## [{new_version}] -- {datetime.date.today().isoformat()}")
        else:
            print(f"Official release SemVer bump ({args.action}): {current_stable} -> {new_version}")
            update_changelog_file(new_version)

    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as f:
            f.write(f"version={new_version}\n")

    status_msg = "previewed" if args.dry_run else "prepared"
    print(f"Version v{new_version} {status_msg} successfully.")

if __name__ == '__main__':
    main()
