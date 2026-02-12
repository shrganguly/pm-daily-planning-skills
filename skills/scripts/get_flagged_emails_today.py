#!/usr/bin/env python3
"""
Sub-agent: Get Flagged Emails Due Today
Fetches emails flagged with due dates for today from Outlook Inbox and Sent Items.

This is called automatically by the /plan-my-day skill.
"""

import sys
import os
from datetime import datetime, timedelta

try:
    import win32com.client
except ImportError:
    print("❌ pywin32 not installed")
    print("Run: pip install pywin32")
    sys.exit(1)


class OutlookEmailFetcher:
    """Fetch flagged emails from Outlook"""

    def __init__(self):
        """Initialize Outlook connection"""
        try:
            print("[*] Connecting to Outlook...")
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            print("[OK] Connected to Outlook successfully")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Outlook: {e}")
            sys.exit(1)

    def fetch_flagged_emails_from_folder(self, folder_id, folder_name):
        """Fetch emails flagged with due date of today from a specific folder

        Args:
            folder_id: Outlook folder constant (6=Inbox, 5=Sent Items)
            folder_name: Human-readable folder name for logging

        Returns:
            list: List of email dictionaries with subject, sender, received time, etc.
        """
        try:
            # Get folder
            folder = self.namespace.GetDefaultFolder(folder_id)
            messages = folder.Items

            # Sort by received/sent time (most recent first)
            time_field = "[ReceivedTime]" if folder_id == 6 else "[SentOn]"
            messages.Sort(time_field, True)

            # Get today's date range
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            print(f"[*] Searching {folder_name} for flagged emails due today ({today_start.strftime('%Y-%m-%d')})...")

            flagged_emails = []
            checked_count = 0
            max_check = 500  # Only check recent emails (last 500)

            for message in messages:
                checked_count += 1
                if checked_count > max_check:
                    break

                try:
                    # Check if email is flagged
                    flag_status = message.FlagStatus
                    # 0 = not flagged, 1 = complete, 2 = flagged
                    if flag_status != 2:
                        continue

                    # Get flag due date - try both TaskDueDate and FlagDueBy
                    due_date = None
                    try:
                        # Try TaskDueDate first (this is where Outlook stores flag due dates)
                        task_due = message.TaskDueDate
                        if task_due and task_due.year != 4501:  # 4501 is Outlook's default "no date"
                            due_date = task_due.date()
                    except:
                        pass

                    # If TaskDueDate didn't work, try FlagDueBy
                    if not due_date:
                        try:
                            flag_due = message.FlagDueBy
                            if flag_due and flag_due.year != 4501:
                                due_date = flag_due.date()
                        except:
                            pass

                    # Check if due date is today
                    if due_date and due_date == today_start.date():
                        # Get timestamp (received or sent depending on folder)
                        timestamp = message.ReceivedTime if folder_id == 6 else message.SentOn

                        email_info = {
                            'subject': message.Subject or "No Subject",
                            'sender': message.SenderName or "Unknown",
                            'sender_email': message.SenderEmailAddress or "",
                            'received': timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else "",
                            'due_date': due_date.strftime("%Y-%m-%d"),
                            'importance': message.Importance,  # 0=low, 1=normal, 2=high
                            'unread': message.UnRead,
                            'size_kb': message.Size / 1024 if message.Size else 0,
                            'folder': folder_name  # Track which folder this came from
                        }
                        flagged_emails.append(email_info)

                except Exception as e:
                    # Skip emails that can't be processed
                    continue

            print(f"[OK] Checked {checked_count} emails in {folder_name}")
            print(f"[OK] Found {len(flagged_emails)} flagged emails due today")

            return flagged_emails

        except Exception as e:
            print(f"[ERROR] Error fetching emails from {folder_name}: {e}")
            return []

    def fetch_flagged_emails_today(self):
        """Fetch emails flagged with due date of today from Inbox and Sent Items

        Returns:
            list: List of email dictionaries with subject, sender, received time, etc.
        """
        all_emails = []

        # Fetch from Inbox (6 = olFolderInbox)
        inbox_emails = self.fetch_flagged_emails_from_folder(6, "Inbox")
        all_emails.extend(inbox_emails)

        # Fetch from Sent Items (5 = olFolderSentMail)
        sent_emails = self.fetch_flagged_emails_from_folder(5, "Sent Items")
        all_emails.extend(sent_emails)

        print(f"\n[OK] Total: {len(all_emails)} flagged emails due today ({len(inbox_emails)} inbox, {len(sent_emails)} sent)")

        return all_emails

    def format_for_daily_plan(self, emails):
        """Format flagged emails for daily plan markdown"""
        if not emails:
            return "No flagged emails due today. Great!"

        # Sort by importance (high first) then by received time
        sorted_emails = sorted(emails, key=lambda x: (-x['importance'], x['received']))

        lines = []

        # Categorize by importance
        high_priority = [e for e in sorted_emails if e['importance'] == 2]
        normal_priority = [e for e in sorted_emails if e['importance'] == 1]

        # Format high priority emails
        if high_priority:
            lines.append("### High Priority")
            for email in high_priority:
                unread_marker = "🔴 " if email['unread'] else ""
                folder_marker = " 📤" if email.get('folder') == "Sent Items" else ""
                lines.append(f"- [ ] {unread_marker}**{email['sender']}**: {email['subject']}{folder_marker}")
            lines.append("")

        # Format normal priority emails
        if normal_priority:
            if high_priority:  # Only add header if there were high priority ones
                lines.append("### Normal Priority")
            for email in normal_priority:
                unread_marker = "🔴 " if email['unread'] else ""
                folder_marker = " 📤" if email.get('folder') == "Sent Items" else ""
                lines.append(f"- [ ] {unread_marker}**{email['sender']}**: {email['subject']}{folder_marker}")
            lines.append("")

        return "\n".join(lines)

    def _estimate_email_time(self, email):
        """Estimate time needed to respond to email"""
        subject_lower = email['subject'].lower()

        # Quick estimates based on keywords
        if any(word in subject_lower for word in ['fyi', 'update', 'status', 'weekly']):
            return 5  # Quick read
        elif any(word in subject_lower for word in ['review', 'feedback', 'question']):
            return 15  # Moderate response
        elif any(word in subject_lower for word in ['urgent', 'escalation', 'blocker', 'critical']):
            return 25  # Detailed response needed
        else:
            return 10  # Default


def get_flagged_emails_today():
    """Main function: Get flagged emails due today"""
    try:
        fetcher = OutlookEmailFetcher()
        emails = fetcher.fetch_flagged_emails_today()

        formatted = fetcher.format_for_daily_plan(emails)

        return {
            'success': True,
            'count': len(emails),
            'emails': emails,
            'formatted_markdown': formatted
        }
    except Exception as e:
        error_msg = f"Could not fetch emails: {str(e)}"
        print(f"[ERROR] {error_msg}")

        return {
            'success': False,
            'count': 0,
            'emails': [],
            'formatted_markdown': None,
            'error': error_msg
        }


def main():
    """CLI interface for testing"""
    result = get_flagged_emails_today()

    if result['success']:
        print(f"\n[OK] Found {result['count']} flagged emails due today")
        print("\n" + "="*60)
        print("FORMATTED OUTPUT FOR DAILY PLAN:")
        print("="*60)
        print(result['formatted_markdown'])
        print("="*60)
    else:
        print(f"\n[ERROR] Failed to fetch emails")
        print(f"[ERROR] {result.get('error', 'Unknown error')}")
        print("\n[INFO] Skill will continue without email data")
        sys.exit(1)


if __name__ == '__main__':
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
