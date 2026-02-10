#!/usr/bin/env python3
"""
Sub-agent: Get Backlog Tasks For Date
Fetches tasks from backlog.md for a specific date and formats them for daily plan.

This is called automatically by the /plan-my-day skill.
"""

import sys
import os
from datetime import datetime

# Add add-task scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../add-task/scripts'))

try:
    from backlog_manager import BacklogManager
except ImportError:
    print("[ERROR] Could not import BacklogManager")
    print("[ERROR] Make sure backlog_manager.py exists in add-task/scripts")
    sys.exit(1)


def get_carryover_tasks(vault_path):
    """
    Get all carryover tasks (from "Backlog due from" sections) organized by category

    Returns:
        dict: Tasks organized by category with carryover date info
              e.g., {'focus': [('task text', '2026-02-09')], 'email': [...]}
    """
    try:
        backlog_file = os.path.join(vault_path, "DailyPlans", "backlog.md")

        if not os.path.exists(backlog_file):
            return {}

        with open(backlog_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse all "Backlog due from" sections
        carryover_by_category = {}
        lines = content.split('\n')
        in_carryover = False
        current_date = None
        current_category = None

        for line in lines:
            # Check for carryover section header
            if line.startswith('## 🔄 Backlog due from'):
                in_carryover = True
                # Extract date from header like "## 🔄 Backlog due from 2026-02-09 (Monday)"
                import re
                match = re.search(r'from (\d{4}-\d{2}-\d{2})', line)
                if match:
                    current_date = match.group(1)

            # Check for new main section (not in carryover anymore)
            elif line.startswith('## ') and not line.startswith('###'):
                in_carryover = False
                current_category = None
                current_date = None

            # Check for category subsections within carryover
            elif in_carryover and line.startswith('### '):
                # Map emoji headers to category names
                if '🧠' in line or 'Focus Work' in line:
                    current_category = 'focus'
                elif '📧' in line or 'Flagged Emails' in line or 'Email' in line:
                    current_category = 'email'
                elif '💬' in line or 'Communications' in line or 'Messages' in line:
                    current_category = 'comms'
                elif '💼' in line or 'Work Tasks' in line:
                    current_category = 'work'
                elif '🎓' in line or 'Learning' in line:
                    current_category = 'learning'
                elif '📚' in line or 'Reading' in line:
                    current_category = 'reading'
                else:
                    current_category = 'other'

            # Check for task lines
            elif in_carryover and current_category and line.strip().startswith('- [ ]'):
                # Extract task text (remove checkbox)
                task = line.strip()[6:].strip()

                # Initialize category if needed
                if current_category not in carryover_by_category:
                    carryover_by_category[current_category] = []

                # Add task with date
                carryover_by_category[current_category].append((task, current_date))

        return carryover_by_category

    except Exception as e:
        print(f"[ERROR] Failed to get carryover tasks: {e}")
        return {}


def get_backlog_tasks_for_date(vault_path, date):
    """
    Get backlog tasks for a specific date and format for daily plan

    Args:
        vault_path: Path to Obsidian vault
        date: Date in YYYY-MM-DD format

    Returns:
        dict: {
            'success': bool,
            'tasks_by_category': dict,
            'total_count': int,
            'formatted_sections': dict,  # Formatted markdown by category (includes carryover)
            'carryover_count': int  # Number of carryover tasks
        }
    """
    try:
        manager = BacklogManager(vault_path)

        # Get tasks for this date
        tasks = manager.get_tasks_for_date(date)

        # Get carryover tasks organized by category
        carryover_tasks = get_carryover_tasks(vault_path)

        if not tasks and not carryover_tasks:
            return {
                'success': True,
                'tasks_by_category': {},
                'total_count': 0,
                'formatted_sections': {},
                'carryover_count': 0
            }

        # Format tasks by category for daily plan
        formatted_sections = {}
        total_count = 0
        carryover_count = 0

        # Helper function to format tasks
        def format_task_list(task_list, carryover_list=None):
            """Format new tasks and carryover tasks together"""
            lines = []

            # Add new tasks first
            for task in task_list:
                lines.append(f"- [ ] {task}")

            # Add carryover tasks with date indicator
            if carryover_list:
                for task, carry_date in carryover_list:
                    lines.append(f"- [ ] {task}")
                    lines.append(f"  - *Carried over from:* {carry_date}")

            return '\n'.join(lines)

        # Process all categories
        all_categories = set(tasks.keys()) | set(carryover_tasks.keys())

        for category in all_categories:
            new_tasks = tasks.get(category, [])
            carry_tasks = carryover_tasks.get(category, [])

            if not new_tasks and not carry_tasks:
                continue

            total_count += len(new_tasks)
            carryover_count += len(carry_tasks)

            # Format tasks with carryover integrated
            formatted_sections[category] = format_task_list(new_tasks, carry_tasks)

        return {
            'success': True,
            'tasks_by_category': tasks,
            'total_count': total_count,
            'formatted_sections': formatted_sections,
            'carryover_count': carryover_count
        }

    except Exception as e:
        error_msg = f"Could not fetch backlog tasks: {str(e)}"
        print(f"[ERROR] {error_msg}")

        return {
            'success': False,
            'tasks_by_category': {},
            'total_count': 0,
            'formatted_sections': {},
            'error': error_msg
        }


def remove_backlog_tasks(vault_path, date):
    """
    Remove tasks for a specific date from backlog
    (Called after daily plan is created)

    This removes:
    1. Date-specific tasks (e.g., "## 2026-02-09 (Monday)")
    2. ALL carryover sections (since they're all now in the daily plan)

    Args:
        vault_path: Path to Obsidian vault
        date: Date in YYYY-MM-DD format

    Returns:
        bool: Success status
    """
    try:
        manager = BacklogManager(vault_path)

        # Remove date-specific tasks
        date_removed = manager.remove_tasks_for_date(date)

        # Remove ALL carryover sections (not just for this date)
        # Since when we create a daily plan, all carryover tasks are moved to it
        sections_removed = manager.remove_all_carryover_sections()

        return date_removed or sections_removed > 0
    except Exception as e:
        print(f"[ERROR] Could not remove backlog tasks: {e}")
        return False


def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description='Get backlog tasks for a date')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--date', help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--remove', action='store_true', help='Remove tasks after fetching')

    args = parser.parse_args()

    # Default to today if no date provided
    if not args.date:
        args.date = datetime.now().strftime("%Y-%m-%d")

    # Get tasks
    result = get_backlog_tasks_for_date(args.vault_path, args.date)

    if result['success']:
        new_task_count = result['total_count']
        carryover_count = result.get('carryover_count', 0)
        total = new_task_count + carryover_count

        print(f"\n[OK] Found {total} total tasks for {args.date}")
        print(f"     - {new_task_count} new tasks from backlog")
        print(f"     - {carryover_count} carryover tasks from previous days")

        # Show formatted sections (integrated new + carryover)
        if result['formatted_sections']:
            print("\n" + "="*60)
            print("FORMATTED OUTPUT FOR DAILY PLAN:")
            print("(New tasks and carryover tasks integrated by category)")
            print("="*60)

            for category, formatted in result['formatted_sections'].items():
                print(f"\n### {category.upper()} SECTION:")
                print(formatted)

            print("="*60)
        else:
            print("\nNo tasks for this date.")

        # Remove tasks if requested
        if args.remove and total > 0:
            print(f"\n[*] Removing tasks from backlog...")
            if remove_backlog_tasks(args.vault_path, args.date):
                print(f"[OK] Tasks removed from backlog")
            else:
                print(f"[ERROR] Failed to remove tasks from backlog")
    else:
        print(f"\n[ERROR] Failed to fetch backlog tasks")
        print(f"[ERROR] {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == '__main__':
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
