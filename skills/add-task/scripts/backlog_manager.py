#!/usr/bin/env python3
"""
Backlog Manager for add-task skill
Manages tasks added for future dates that don't have daily plans yet
"""

import sys
import os
from datetime import datetime
import re


class BacklogManager:
    """Manages the backlog.md file for future tasks"""

    def __init__(self, vault_path):
        """
        Initialize backlog manager

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path
        self.backlog_file = os.path.join(vault_path, "DailyPlans", "backlog.md")

    def ensure_backlog_exists(self):
        """Create backlog file if it doesn't exist"""
        if not os.path.exists(self.backlog_file):
            # Create directory if needed
            os.makedirs(os.path.dirname(self.backlog_file), exist_ok=True)

            # Create initial backlog file
            initial_content = """---
title: Task Backlog
description: Tasks scheduled for dates without daily plans yet
last_updated: {timestamp}
---

# Task Backlog

Tasks added for future dates are stored here until their daily plans are created.

When you run `/plan-my-day` for a date, tasks from this backlog will be automatically added to that day's plan.

---

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))

            with open(self.backlog_file, 'w', encoding='utf-8') as f:
                f.write(initial_content)

            print(f"[*] Created backlog file: {self.backlog_file}")

    def add_task(self, date, category, task):
        """
        Add a task to the backlog

        Args:
            date: Date in YYYY-MM-DD format
            category: Task category (email/message/reading/learning/work/other)
            task: Task description

        Returns:
            bool: Success status
        """
        self.ensure_backlog_exists()

        try:
            # Read existing backlog
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse date to get day name
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")

            # Check if date section exists
            date_header = f"## {date} ({day_name})"

            if date_header not in content:
                # Add new date section at the end
                new_section = f"""
{date_header}

### {self._category_emoji(category)} {self._category_name(category)}
- [ ] {task}

---

"""
                content += new_section
            else:
                # Date section exists, check if category exists
                category_header = f"### {self._category_emoji(category)} {self._category_name(category)}"

                # Find the date section
                date_pos = content.find(date_header)
                next_date_pos = content.find("\n## ", date_pos + 1)
                if next_date_pos == -1:
                    next_date_pos = len(content)

                date_section = content[date_pos:next_date_pos]

                if category_header in date_section:
                    # Category exists, add task to it
                    category_pos = content.find(category_header, date_pos)
                    # Find next section or end
                    next_section = content.find("\n###", category_pos + 1)
                    if next_section == -1 or next_section > next_date_pos:
                        next_section = next_date_pos

                    # Insert task before next section
                    new_task = f"- [ ] {task}\n"

                    content = content[:next_section] + new_task + "\n" + content[next_section:]
                else:
                    # Category doesn't exist, add it before the --- separator
                    separator_pos = content.find("---", date_pos)
                    if separator_pos == -1 or separator_pos > next_date_pos:
                        # No separator, add before next date section
                        separator_pos = next_date_pos

                    new_category = f"""
{category_header}
- [ ] {task}

"""
                    content = content[:separator_pos] + new_category + content[separator_pos:]

            # Update last_updated timestamp
            content = re.sub(
                r'last_updated: .*',
                f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                content
            )

            # Write back
            with open(self.backlog_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[OK] Task added to backlog for {date}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to add task to backlog: {e}")
            return False

    def get_tasks_for_date(self, date):
        """
        Get all tasks for a specific date from backlog

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            dict: Tasks organized by category
        """
        self.ensure_backlog_exists()

        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse date to get day name
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            date_header = f"## {date} ({day_name})"

            if date_header not in content:
                return {}  # No tasks for this date

            # Extract the date section
            date_pos = content.find(date_header)
            next_date_pos = content.find("\n## ", date_pos + 1)
            if next_date_pos == -1:
                next_date_pos = len(content)

            date_section = content[date_pos:next_date_pos]

            # Parse tasks by category
            tasks = {}
            current_category = None

            for line in date_section.split('\n'):
                if line.startswith('### '):
                    # Category header
                    for cat in ['email', 'message', 'reading', 'learning', 'work', 'other']:
                        if cat in line.lower() or self._category_name(cat).lower() in line.lower():
                            current_category = cat
                            tasks[cat] = []
                            break
                elif line.strip().startswith('- [ ]') and current_category:
                    # Task line
                    task_text = line.strip()[6:].strip()  # Remove "- [ ] "
                    tasks[current_category].append(task_text)

            return tasks

        except Exception as e:
            print(f"[ERROR] Failed to read backlog: {e}")
            return {}

    def remove_tasks_for_date(self, date):
        """
        Remove all tasks for a specific date from backlog
        (Called after tasks are moved to daily plan)

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            bool: Success status
        """
        self.ensure_backlog_exists()

        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse date to get day name
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            date_header = f"## {date} ({day_name})"

            if date_header not in content:
                return True  # Nothing to remove

            # Find and remove the date section
            date_pos = content.find(date_header)
            next_date_pos = content.find("\n## ", date_pos + 1)
            if next_date_pos == -1:
                # Last section
                content = content[:date_pos]
            else:
                # Remove section including the separator
                content = content[:date_pos] + content[next_date_pos:]

            # Update last_updated timestamp
            content = re.sub(
                r'last_updated: .*',
                f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                content
            )

            # Write back
            with open(self.backlog_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[OK] Removed tasks for {date} from backlog")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to remove tasks from backlog: {e}")
            return False

    def remove_carryover_section(self, date):
        """
        Remove carryover section for a specific date from backlog
        (Called after carryover tasks are moved to daily plan)

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            bool: Success status
        """
        self.ensure_backlog_exists()

        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse date to get day name
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            carryover_header = f"## 🔄 Backlog due from {date} ({day_name})"

            if carryover_header not in content:
                return True  # Nothing to remove

            # Find and remove the carryover section
            carryover_pos = content.find(carryover_header)
            next_section_pos = content.find("\n## ", carryover_pos + 1)

            if next_section_pos == -1:
                # Last section - remove everything from carryover_header to end
                content = content[:carryover_pos].rstrip() + "\n"
            else:
                # Remove section up to next section
                content = content[:carryover_pos] + content[next_section_pos + 1:]

            # Update last_updated timestamp
            content = re.sub(
                r'last_updated: .*',
                f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                content
            )

            # Write back
            with open(self.backlog_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[OK] Removed carryover section for {date} from backlog")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to remove carryover section from backlog: {e}")
            return False

    def remove_all_carryover_sections(self):
        """
        Remove ALL carryover sections from backlog
        (Called when creating daily plan - all carryover tasks are now in the plan)

        Returns:
            int: Number of carryover sections removed
        """
        self.ensure_backlog_exists()

        try:
            with open(self.backlog_file, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            new_lines = []
            in_carryover = False
            sections_removed = 0

            for line in lines:
                # Check if we're entering a carryover section
                if line.startswith('## 🔄 Backlog due from'):
                    in_carryover = True
                    sections_removed += 1
                    continue  # Skip this line

                # Check if we're leaving carryover and entering a new section
                elif line.startswith('## ') and not line.startswith('###'):
                    in_carryover = False
                    new_lines.append(line)

                # Only keep lines if we're not in a carryover section
                elif not in_carryover:
                    new_lines.append(line)

            # Rejoin content
            content = '\n'.join(new_lines)

            # Clean up extra blank lines
            content = re.sub(r'\n{3,}', '\n\n', content)

            # Update last_updated timestamp
            content = re.sub(
                r'last_updated: .*',
                f'last_updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                content
            )

            # Write back
            with open(self.backlog_file, 'w', encoding='utf-8') as f:
                f.write(content)

            if sections_removed > 0:
                print(f"[OK] Removed {sections_removed} carryover section(s) from backlog")

            return sections_removed

        except Exception as e:
            print(f"[ERROR] Failed to remove carryover sections from backlog: {e}")
            return 0

    def _category_emoji(self, category):
        """Get emoji for category"""
        emoji_map = {
            'focus': '🧠',
            'comms': '💬',
            'learning': '🎓',
            'work': '💼',
            'email': '📧',
            'message': '💬',
            'reading': '📚',
            'other': '📋'
        }
        return emoji_map.get(category, '📋')

    def _category_name(self, category):
        """Get display name for category"""
        name_map = {
            'focus': 'Focus Work',
            'comms': 'Communications',
            'learning': 'Learning & Development',
            'work': 'Work Tasks',
            'email': 'Emails',
            'message': 'Messages',
            'reading': 'Reading & Learning',
            'other': 'Other Tasks'
        }
        return name_map.get(category, 'Tasks')


def main():
    """CLI interface for testing"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backlog_manager.py add <vault_path> <date> <category> <task>")
        print("  python backlog_manager.py get <vault_path> <date>")
        print("  python backlog_manager.py remove <vault_path> <date>")
        sys.exit(1)

    command = sys.argv[1]
    vault_path = sys.argv[2]

    manager = BacklogManager(vault_path)

    if command == "add":
        date = sys.argv[3]
        category = sys.argv[4]
        task = " ".join(sys.argv[5:])
        success = manager.add_task(date, category, task)
        sys.exit(0 if success else 1)

    elif command == "get":
        date = sys.argv[3]
        tasks = manager.get_tasks_for_date(date)
        if tasks:
            print(f"Tasks for {date}:")
            for category, task_list in tasks.items():
                print(f"\n{category.upper()}:")
                for task in task_list:
                    print(f"  - {task}")
        else:
            print(f"No tasks found for {date}")
        sys.exit(0)

    elif command == "remove":
        date = sys.argv[3]
        success = manager.remove_tasks_for_date(date)
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
