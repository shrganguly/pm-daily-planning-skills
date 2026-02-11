#!/usr/bin/env python3
"""
Outlook MAPI Calendar Fetcher - Simple Direct Access
Fetches today's calendar events directly from local Outlook installation
NO Azure registration, NO OAuth, NO API setup needed!
"""

import sys
from datetime import datetime, timedelta
import json

try:
    import win32com.client
except ImportError:
    print("❌ pywin32 not installed")
    print("Run: pip install pywin32")
    sys.exit(1)


class OutlookMAPIFetcher:
    """Direct access to Outlook via MAPI"""

    def __init__(self):
        """Initialize Outlook connection"""
        try:
            print("[*] Connecting to Outlook...")
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            print("[OK] Connected to Outlook successfully")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Outlook: {e}")
            print("\n[!] Make sure:")
            print("  1. Outlook desktop app is installed")
            print("  2. Outlook is configured with your account")
            print("  3. You've opened Outlook at least once")
            sys.exit(1)

    def fetch_today_events(self, accepted_only=True):
        """Fetch today's calendar appointments INCLUDING recurring meetings and exceptions

        Args:
            accepted_only: If True, only return accepted meetings (default: True)
        """
        try:
            import pythoncom

            # Get default calendar folder
            calendar = self.namespace.GetDefaultFolder(9)  # 9 = olFolderCalendar

            # Set filter for today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            print(f"[*] Fetching events for {today_start.strftime('%Y-%m-%d')}...")

            # Keywords to exclude from calendar (personal blocks, not real meetings)
            exclude_keywords = [
                'focus time',
                'lunch',
                'break',
                'personal time',
                'deep work',
                'do not schedule',
                'hold',
                'block',
                'learning time'
            ]

            # NEW APPROACH: Get master appointments and handle exceptions
            # This is the only reliable way to get modified recurring occurrences
            items = calendar.Items
            items.IncludeRecurrences = False  # Get MASTER appointments only
            items.Sort("[Start]")

            print(f"[*] Checking calendar for recurring patterns and exceptions...")

            # Parse events
            events = []
            total_found = 0
            excluded_count = 0
            exceptions_found = 0
            occurrences_found = 0

            for item in items:
                try:
                    if item.IsRecurring:
                        # This is a recurring master - check for today's occurrence
                        rec_pattern = item.GetRecurrencePattern()

                        # Check if today is within the recurrence range
                        pattern_start = rec_pattern.PatternStartDate.date()
                        pattern_end = rec_pattern.PatternEndDate.date()
                        today_date = today_start.date()

                        if pattern_start <= today_date <= pattern_end:
                            # FIRST: Check exceptions (modified occurrences)
                            try:
                                exceptions = rec_pattern.Exceptions
                                for i in range(1, exceptions.Count + 1):  # COM collections are 1-indexed
                                    try:
                                        exception = exceptions.Item(i)
                                        exception_date = exception.OriginalDate.date()

                                        if exception_date == today_date and not exception.Deleted:
                                            exceptions_found += 1
                                            modified_appt = exception.AppointmentItem

                                            event = self._parse_event(modified_appt)
                                            if event:
                                                total_found += 1

                                                # Check exclusions
                                                subject_lower = event['subject'].lower()
                                                is_excluded = any(kw in subject_lower for kw in exclude_keywords)

                                                if is_excluded:
                                                    excluded_count += 1
                                                    continue

                                                # Filter by response status
                                                if accepted_only:
                                                    if event['response_status'] in [1, 3]:  # Organizer or Accepted
                                                        events.append(event)
                                                else:
                                                    events.append(event)
                                    except:
                                        continue
                            except:
                                pass

                            # SECOND: Try to get regular occurrence (if no exception)
                            # Check if we already have this meeting from exceptions
                            already_added = any(e['subject'] == item.Subject and
                                              e['start_datetime'][:10] == today_start.strftime('%Y-%m-%d')
                                              for e in events)

                            if not already_added:
                                try:
                                    # Try to get occurrence
                                    start_time = rec_pattern.StartTime
                                    occurrence_dt = datetime.combine(today_date, start_time.time())
                                    occurrence = rec_pattern.GetOccurrence(occurrence_dt)

                                    occurrences_found += 1

                                    event = self._parse_event(occurrence)
                                    if event:
                                        total_found += 1

                                        # Check exclusions
                                        subject_lower = event['subject'].lower()
                                        is_excluded = any(kw in subject_lower for kw in exclude_keywords)

                                        if is_excluded:
                                            excluded_count += 1
                                            continue

                                        # Filter by response status
                                        if accepted_only:
                                            if event['response_status'] in [1, 3]:
                                                events.append(event)
                                        else:
                                            events.append(event)
                                except pythoncom.com_error:
                                    # No occurrence for today
                                    pass
                    else:
                        # Non-recurring appointment
                        event_start = item.Start
                        if event_start.date() == today_start.date():
                            event = self._parse_event(item)
                            if event:
                                total_found += 1

                                # Check exclusions
                                subject_lower = event['subject'].lower()
                                is_excluded = any(kw in subject_lower for kw in exclude_keywords)

                                if is_excluded:
                                    excluded_count += 1
                                    continue

                                # Filter by response status
                                if accepted_only:
                                    if event['response_status'] in [1, 3]:
                                        events.append(event)
                                else:
                                    events.append(event)

                except Exception as e:
                    # Silently skip items that can't be processed
                    continue

            if accepted_only:
                print(f"[OK] Found {exceptions_found} recurring exceptions, {occurrences_found} recurring occurrences")
                print(f"[OK] Found {len(events)} accepted meetings (out of {total_found} total, {excluded_count} personal blocks filtered)")
            else:
                print(f"[OK] Found {exceptions_found} recurring exceptions, {occurrences_found} recurring occurrences")
                print(f"[OK] Found {len(events)} events ({excluded_count} personal blocks filtered)")

            return events

        except Exception as e:
            print(f"[ERROR] Error fetching calendar: {e}")
            return []

    def _parse_event(self, item):
        """Parse Outlook appointment item"""
        try:
            # Get basic properties
            subject = item.Subject or "Untitled"

            # Get start/end times
            start_dt = item.Start
            end_dt = item.End

            # Check if all-day event
            is_all_day = item.AllDayEvent

            # Format times
            if is_all_day:
                start_time = "All day"
                end_time = ""
            else:
                start_time = start_dt.strftime("%I:%M %p").lstrip('0')
                end_time = end_dt.strftime("%I:%M %p").lstrip('0')

            # Calculate duration
            duration = end_dt - start_dt
            duration_minutes = int(duration.total_seconds() / 60)

            # Get location
            location = item.Location or ""

            # Get organizer
            try:
                organizer = item.Organizer or ""
            except:
                organizer = ""

            # Get meeting status
            meeting_status = item.MeetingStatus  # 0=non-meeting, 1=organizer, 3=attendee

            # Get response status
            try:
                response_status = item.ResponseStatus  # 0=none, 2=tentative, 3=accepted, 4=declined
            except:
                response_status = 0

            # Get categories
            try:
                categories = item.Categories or ""
            except:
                categories = ""

            # Get body/notes (first 100 chars)
            try:
                body = item.Body[:100] if item.Body else ""
            except:
                body = ""

            # Get attendees count
            try:
                recipients = item.Recipients
                attendee_count = recipients.Count if recipients else 0
            except:
                attendee_count = 0

            return {
                'subject': subject,
                'start': start_time,
                'end': end_time,
                'start_datetime': start_dt.isoformat(),
                'end_datetime': end_dt.isoformat(),
                'duration_minutes': duration_minutes,
                'location': location,
                'organizer': organizer,
                'is_all_day': is_all_day,
                'meeting_status': meeting_status,
                'response_status': response_status,
                'categories': categories,
                'attendee_count': attendee_count,
                'body_preview': body.strip()
            }

        except Exception as e:
            print(f"[!] Error parsing event: {e}")
            return None

    def format_for_daily_plan(self, events):
        """Format events for daily plan markdown"""
        if not events:
            return "No meetings scheduled for today"

        # Sort events by start time first (chronological order)
        events = sorted(events, key=lambda e: e['start_datetime'])

        # Separate into morning/afternoon/evening
        morning = []
        afternoon = []
        evening = []

        total_meeting_time = 0

        for event in events:
            # Skip declined meetings
            if event['response_status'] == 4:  # Declined
                continue

            total_meeting_time += event['duration_minutes']

            # Create formatted line
            if event['is_all_day']:
                line = f"- All day: {event['subject']}"
            else:
                line = f"- {event['start']} - {event['end']}: {event['subject']}"

                if event['location']:
                    line += f" ({event['location']})"

                # Add indicators
                if event['response_status'] == 2:  # Tentative
                    line += " [TENTATIVE]"
                if event['attendee_count'] > 10:
                    line += " [LARGE MEETING]"

            # Categorize by time
            start_dt = datetime.fromisoformat(event['start_datetime'])
            hour = start_dt.hour

            if hour < 12:
                morning.append(line)
            elif hour < 17:
                afternoon.append(line)
            else:
                evening.append(line)

        # Build formatted output
        sections = []

        if morning:
            sections.append("**Morning:**\n" + "\n".join(morning))

        if afternoon:
            sections.append("**Afternoon:**\n" + "\n".join(afternoon))

        if evening:
            sections.append("**Evening:**\n" + "\n".join(evening))

        formatted = "\n\n".join(sections)

        # Add summary
        hours = total_meeting_time // 60
        minutes = total_meeting_time % 60

        if hours > 0 and minutes > 0:
            time_str = f"{hours}h {minutes}m"
        elif hours > 0:
            time_str = f"{hours}h"
        else:
            time_str = f"{minutes}m"

        formatted += f"\n\n**Total meeting time:** {time_str}"

        # Calculate available focus time
        available_minutes = 480 - total_meeting_time  # 480 min = 8 hours
        available_hours = available_minutes / 60

        formatted += f"\n**Available Focus Time:** {available_hours:.1f} hours"

        # Add warnings if needed
        if total_meeting_time > 360:  # More than 6 hours
            formatted += "\n\n[!] **Meeting-heavy day!** Consider:"
            formatted += "\n- Declining optional meetings"
            formatted += "\n- Rescheduling if possible"
            formatted += "\n- Batching email/message responses"

        return formatted


def main():
    """Main entry point"""
    import argparse

    # Fix Windows console encoding
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='Fetch Outlook calendar via MAPI')
    parser.add_argument('--test', action='store_true', help='Run test fetch and display')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--markdown', action='store_true', help='Output as markdown (default)')
    parser.add_argument('--all', action='store_true', help='Include all meetings (tentative, declined, etc). Default: accepted only')

    args = parser.parse_args()

    try:
        # Create fetcher
        fetcher = OutlookMAPIFetcher()

        # Fetch events (accepted only by default, unless --all flag used)
        accepted_only = not args.all
        events = fetcher.fetch_today_events(accepted_only=accepted_only)

        if not events:
            print("\n[*] No events found for today")
            if args.json:
                print(json.dumps([]))
            else:
                print("\nNo meetings scheduled for today. Great time for deep work!")
            return

        # Output results
        if args.json:
            # Output as JSON
            print(json.dumps(events, indent=2, default=str))
        elif args.test:
            # Test mode - simple display
            print(f"\n[*] Found {len(events)} events:\n")
            for event in events:
                if event['is_all_day']:
                    print(f"  - All day: {event['subject']}")
                else:
                    print(f"  - {event['start']} - {event['end']}: {event['subject']}")
                    if event['location']:
                        print(f"    Location: {event['location']}")
                    if event['response_status'] == 2:
                        print(f"    Status: Tentative [TENTATIVE]")

            # Show summary
            total_time = sum(e['duration_minutes'] for e in events)
            hours = total_time // 60
            minutes = total_time % 60
            print(f"\n  Total meeting time: {hours}h {minutes}m")
            print(f"  Available focus time: {(480-total_time)/60:.1f}h")

        else:
            # Markdown format (default)
            formatted = fetcher.format_for_daily_plan(events)
            print("\n" + formatted)

    except KeyboardInterrupt:
        print("\n\n[!] Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
