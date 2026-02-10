#!/usr/bin/env python3
"""
End of Day Cleanup Agent
Runs automatically at 11:45 PM daily to move unchecked tasks to backlog.

This ensures incomplete tasks flow to the next day.
"""

import sys
import os
import re
from datetime import datetime

# Add add-task scripts to path for BacklogManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../add-task/scripts'))

try:
    from backlog_manager import BacklogManager
except ImportError:
    print("[ERROR] Could not import BacklogManager")
    sys.exit(1)


class EndOfDayCleanup:
    """Handles end-of-day task cleanup and carryover"""

    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.backlog_manager = BacklogManager(vault_path)

    def get_todays_plan_path(self):
        """Get path to today's daily plan"""
        today = datetime.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        date = today.strftime("%Y-%m-%d")

        plan_path = os.path.join(
            self.vault_path,
            "DailyPlans",
            year,
            month,
            f"{date}.md"
        )

        return plan_path, date

    def extract_unchecked_tasks(self, plan_content):
        """
        Extract all unchecked tasks from daily plan

        Returns:
            dict: Tasks organized by section, with tuples of (task_text, carryover_date)
                  carryover_date is None for new tasks
        """
        tasks = {
            'focus': [],
            'comms': [],
            'learning': [],
            'work': [],
            'emails': [],
            'messages': [],
            'reading': [],
            'other': []
        }

        current_section = None
        lines = plan_content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i]

            # Detect section headers
            if '🧠' in line and line.startswith('##'):
                current_section = 'focus'
            elif '💬' in line and line.startswith('##'):
                # Could be Communications or Messages (legacy)
                if 'Communications' in line:
                    current_section = 'comms'
                else:
                    current_section = 'messages'
            elif '🎓' in line and line.startswith('##'):
                current_section = 'learning'
            elif '💼' in line and line.startswith('##'):
                current_section = 'work'
            elif '📧' in line and line.startswith('##'):
                # IMPORTANT: Always carry over flagged emails
                current_section = 'emails'
            elif 'Flagged Emails' in line and line.startswith('##'):
                # Additional check for email section (in case emoji doesn't match)
                current_section = 'emails'
            elif '📚' in line and line.startswith('##'):
                current_section = 'reading'
            elif '📋' in line and line.startswith('##'):
                # Could be Work Tasks or other sections
                current_section = 'other'
            elif '🔄' in line and line.startswith('##'):
                # Old tasks backlog section
                current_section = 'other'
            elif '💡' in line and line.startswith('##'):
                # Reflection section - stop processing
                break
            elif '📅' in line and line.startswith('##'):
                # Calendar section - skip (meetings aren't tasks to carry over)
                current_section = None

            # Extract unchecked tasks (both - [ ] and numbered 1. [ ] formats)
            stripped = line.strip()
            if current_section and (stripped.startswith('- [ ]') or re.match(r'^\d+\.\s*\[\s*\]', stripped)):
                # Extract task text (remove checkbox)
                if stripped.startswith('- [ ]'):
                    task_text = stripped[6:].strip()
                else:
                    # Numbered format like "1. [ ]"
                    task_text = re.sub(r'^\d+\.\s*\[\s*\]', '', stripped).strip()

                # Skip if it's metadata line
                if task_text and not task_text.startswith('*') and not task_text.startswith('-'):
                    # Clean up task text - remove formatting like ** and other metadata
                    task_text = self._clean_task_text(task_text)

                    # Check next line for "Carried over from:" indicator
                    carryover_date = None
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        # Check if next line has carryover date
                        match = re.match(r'-\s*\*Carried over from:\*\s*(\d{4}-\d{2}-\d{2})', next_line)
                        if match:
                            carryover_date = match.group(1)

                    if task_text:
                        tasks[current_section].append((task_text, carryover_date))

            i += 1

        return tasks

    def _clean_task_text(self, text):
        """Clean task text - remove bold markers, extract main text"""
        # Remove bold markers
        text = re.sub(r'\*\*(.*?)\*\*:', r'\1:', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)

        # If it's a multi-line task with details, just take the first line
        if '\n' in text:
            text = text.split('\n')[0]

        return text.strip()

    def add_to_backlog_carryover(self, date, tasks):
        """
        Add unchecked tasks to backlog under "Backlog due from <date>" section

        Args:
            date: Date in YYYY-MM-DD format (today's date)
            tasks: Dict of tasks by category, with tuples of (task_text, original_carryover_date)
        """
        backlog_file = self.backlog_manager.backlog_file
        self.backlog_manager.ensure_backlog_exists()

        try:
            with open(backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse date for display
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")

            # Create carryover section header
            carryover_header = f"## 🔄 Backlog due from {date} ({day_name})"

            # Count total tasks
            total_tasks = sum(len(task_list) for task_list in tasks.values())

            if total_tasks == 0:
                print(f"[*] No unchecked tasks to carry over from {date}")
                return True

            # Check if section already exists (shouldn't happen, but handle it)
            if carryover_header in content:
                print(f"[!] Warning: Carryover section for {date} already exists")
                return False

            # Build carryover section
            section_lines = [f"\n{carryover_header}\n"]
            section_lines.append(f"*{total_tasks} tasks carried over from {day_name}*\n")

            # Add tasks by category
            category_map = {
                'focus': ('🧠', 'Focus Work'),
                'comms': ('💬', 'Communications'),
                'learning': ('🎓', 'Learning & Development'),
                'work': ('💼', 'Work Tasks'),
                'emails': ('📧', 'Flagged Emails'),
                'messages': ('💬', 'Messages'),
                'reading': ('📚', 'Reading & Learning'),
                'other': ('📋', 'Other Tasks')
            }

            for category, (emoji, name) in category_map.items():
                if tasks.get(category):
                    section_lines.append(f"\n### {emoji} {name}")
                    for task_tuple in tasks[category]:
                        # task_tuple is (task_text, original_carryover_date or None)
                        task_text, original_date = task_tuple
                        section_lines.append(f"- [ ] {task_text}")
                        # Use original carryover date if it exists, otherwise use today's date
                        carryover_date = original_date if original_date else date
                        section_lines.append(f"  - *Carried over from:* {carryover_date}")

            section_lines.append("\n---\n")

            # Insert at the end (before final newlines)
            new_section = '\n'.join(section_lines)
            content = content.rstrip() + '\n' + new_section + '\n'

            # Update last_updated timestamp
            content = re.sub(
                r'last_updated: .*',
                f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                content
            )

            # Write back
            with open(backlog_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[OK] Carried over {total_tasks} tasks to backlog (preserving original dates)")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to add tasks to backlog: {e}")
            return False

    def remove_unchecked_tasks(self, plan_path):
        """
        Remove all unchecked tasks from the daily plan

        Args:
            plan_path: Path to the daily plan file
        """
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            cleaned_lines = []
            skip_next_indent = False

            for i, line in enumerate(lines):
                # Check if this is an unchecked task
                stripped = line.strip()
                if stripped.startswith('- [ ]') or re.match(r'^\d+\.\s*\[\s*\]', stripped):
                    # Skip this unchecked task
                    skip_next_indent = True
                    continue

                # Skip indented metadata lines immediately after unchecked tasks
                if skip_next_indent and line.startswith('  ') and stripped.startswith('-'):
                    # This is metadata for the task (like "- *Estimated time:*")
                    continue
                else:
                    skip_next_indent = False

                # Keep this line
                cleaned_lines.append(line)

            # Write back
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)

            print(f"[OK] Removed unchecked tasks from daily plan")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to remove unchecked tasks: {e}")
            return False

    def mark_plan_complete(self, plan_path):
        """
        Mark the daily plan status as complete

        Args:
            plan_path: Path to the daily plan file
        """
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Update status from in-progress to complete
            updated_content = re.sub(
                r'status: in-progress',
                'status: complete',
                content
            )

            # Write back
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)

            print(f"[OK] Plan status updated to 'complete'")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to mark plan as complete: {e}")
            return False

    def run_cleanup(self):
        """Main cleanup process"""
        print(f"[*] Running end-of-day cleanup at {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Get today's plan
        plan_path, today_date = self.get_todays_plan_path()

        if not os.path.exists(plan_path):
            print(f"[*] No daily plan found for today ({today_date})")
            print(f"[*] Nothing to clean up")
            return True

        print(f"[*] Reading daily plan: {plan_path}")

        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_content = f.read()

            # Extract unchecked tasks
            print(f"[*] Extracting unchecked tasks...")
            tasks = self.extract_unchecked_tasks(plan_content)

            # Count tasks
            total = sum(len(task_list) for task_list in tasks.values())

            if total == 0:
                print(f"[OK] All tasks completed! Nothing to carry over.")
                # Mark plan as complete even when all tasks are done
                print(f"[*] Marking daily plan as complete...")
                self.mark_plan_complete(plan_path)
                print(f"[OK] Daily plan marked as complete")
                return True

            print(f"[*] Found {total} unchecked tasks to carry over:")
            for category, task_list in tasks.items():
                if task_list:
                    print(f"  - {category}: {len(task_list)} tasks")

            # Explicitly warn if no emails were found (they should usually be there)
            if not tasks.get('emails'):
                print(f"[*] Note: No flagged emails found to carry over")

            # Add to backlog
            print(f"[*] Adding tasks to backlog...")
            success = self.add_to_backlog_carryover(today_date, tasks)

            if success:
                # Remove unchecked tasks from daily plan
                print(f"[*] Removing unchecked tasks from daily plan...")
                self.remove_unchecked_tasks(plan_path)

                # Mark today's plan as complete
                print(f"[*] Marking daily plan as complete...")
                self.mark_plan_complete(plan_path)

                print(f"[OK] End-of-day cleanup completed successfully!")
                print(f"[OK] {total} tasks moved to backlog and removed from daily plan")
                print(f"[OK] Tasks will appear in tomorrow's 'Old tasks backlog' section")
                print(f"[OK] Daily plan marked as complete")
                return True
            else:
                print(f"[ERROR] Failed to complete cleanup")
                return False

        except Exception as e:
            print(f"[ERROR] Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='End of day cleanup for daily plans')
    parser.add_argument('vault_path', nargs='?', help='Path to Obsidian vault')
    parser.add_argument('--config', help='Use vault path from plan-my-day config', action='store_true')

    args = parser.parse_args()

    # Get vault path
    if args.config or not args.vault_path:
        # Read from config
        config_file = os.path.join(
            os.path.dirname(__file__),
            '../../plan-my-day/config/vault-path.txt'
        )

        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                vault_path = f.read().strip()
            print(f"[*] Using vault path from config: {vault_path}")
        else:
            print("[ERROR] No vault path provided and config not found")
            print("Usage: python end_of_day_cleanup.py <vault_path>")
            print("   or: python end_of_day_cleanup.py --config")
            sys.exit(1)
    else:
        vault_path = args.vault_path

    # Run cleanup
    cleanup = EndOfDayCleanup(vault_path)
    success = cleanup.run_cleanup()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
