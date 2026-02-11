#!/usr/bin/env python3
"""
Auto-commit script for Maurice's AI Empire
Groups changes by category and creates semantic commits
"""

import subprocess
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime

def run_cmd(cmd):
    """Execute shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_changed_files():
    """Get all changed files grouped by status"""
    output = run_cmd("git status --porcelain")

    modified = []
    added = []
    deleted = []

    for line in output.split('\n'):
        if not line:
            continue
        status = line[:2].strip()
        filepath = line[3:]

        if status == 'M':
            modified.append(filepath)
        elif status == 'A':
            added.append(filepath)
        elif status == 'D':
            deleted.append(filepath)

    return {'modified': modified, 'added': added, 'deleted': deleted}

def group_by_category(files):
    """Group files by their category/directory"""
    categories = defaultdict(list)

    for filepath in files:
        # Get first directory as category
        parts = filepath.split('/')
        if len(parts) > 1:
            category = parts[0]
        else:
            category = 'root'

        categories[category].append(filepath)

    return dict(categories)

def stage_and_commit(files, category, change_type):
    """Stage files and create a commit"""
    if not files:
        return False

    # Stage files
    for f in files:
        run_cmd(f"git add '{f}'")

    # Generate commit message
    count = len(files)
    emoji_map = {
        'automation': '🤖',
        'content_factory': '📝',
        'reports': '📊',
        'ai-vault': '🔐',
        'external': '🔗',
        'root': '✨'
    }
    emoji = emoji_map.get(category, '📦')

    if change_type == 'modified':
        msg = f"{emoji} Update {category} ({count} files)"
    elif change_type == 'added':
        msg = f"{emoji} Add {category} assets ({count} items)"
    else:
        msg = f"{emoji} Clean {category}"

    # Create commit
    cmd = f'git commit -m "{msg}"'
    result = run_cmd(cmd)

    if 'but nothing staged' not in result and 'nothing to commit' not in result:
        print(f"✅ {msg}")
        return True
    return False

def main():
    print("🚀 Auto-Commit System Starting...")

    changes = get_changed_files()

    if not any([changes['modified'], changes['added'], changes['deleted']]):
        print("✅ No changes to commit")
        return

    # Exclude pycache files
    for status in ['modified', 'added', 'deleted']:
        changes[status] = [f for f in changes[status] if '__pycache__' not in f and '.pyc' not in f]

    committed = 0

    # Process modified files
    if changes['modified']:
        modified_groups = group_by_category(changes['modified'])
        for category in sorted(modified_groups.keys()):
            if stage_and_commit(modified_groups[category], category, 'modified'):
                committed += 1

    # Process new files
    if changes['added']:
        added_groups = group_by_category(changes['added'])
        for category in sorted(added_groups.keys()):
            if stage_and_commit(added_groups[category], category, 'added'):
                committed += 1

    # Process deletions
    if changes['deleted']:
        deleted_groups = group_by_category(changes['deleted'])
        for category in sorted(deleted_groups.keys()):
            if stage_and_commit(deleted_groups[category], category, 'deleted'):
                committed += 1

    print(f"\n✨ Done! {committed} commits created")

if __name__ == '__main__':
    main()
