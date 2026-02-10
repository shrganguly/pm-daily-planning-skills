#!/usr/bin/env python3
"""
Sub-agent: Get Accepted Meetings For Today
Fetches accepted calendar meetings from Outlook for today's date.
Filters out personal blocks (lunch, focus time, etc.)

This is called automatically by the /plan-my-day skill.
"""

import sys
import os

# Add parent directory to path to import from fetch_calendar_outlook
sys.path.insert(0, os.path.dirname(__file__))

try:
    from fetch_calendar_outlook import OutlookMAPIFetcher
except ImportError:
    print("[ERROR] Could not import OutlookMAPIFetcher")
    print("[ERROR] Make sure fetch_calendar_outlook.py is in the same directory")
    sys.exit(1)


def get_accepted_meetings_for_today():
    """
    Main function: Get accepted meetings for today

    Returns:
        dict: {
            'success': bool,
            'count': int,
            'meetings': list,
            'formatted_markdown': str,
            'total_meeting_hours': float,
            'available_focus_hours': float
        }
    """
    try:
        # Create fetcher
        fetcher = OutlookMAPIFetcher()

        # Fetch accepted meetings only (filters tentative, declined, personal blocks)
        events = fetcher.fetch_today_events(accepted_only=True)

        if not events:
            return {
                'success': True,
                'count': 0,
                'meetings': [],
                'formatted_markdown': 'No meetings scheduled for today. Great day for deep work!',
                'total_meeting_hours': 0.0,
                'available_focus_hours': 8.0
            }

        # Format for daily plan
        formatted = fetcher.format_for_daily_plan(events)

        # Calculate totals
        total_minutes = sum(e['duration_minutes'] for e in events)
        total_hours = total_minutes / 60.0
        available_hours = max(0, 8.0 - total_hours)  # Don't show negative

        return {
            'success': True,
            'count': len(events),
            'meetings': events,
            'formatted_markdown': formatted,
            'total_meeting_hours': round(total_hours, 1),
            'available_focus_hours': round(available_hours, 1)
        }

    except Exception as e:
        # If anything fails, return error but don't crash
        error_msg = f"Could not fetch calendar: {str(e)}"
        print(f"[ERROR] {error_msg}")

        return {
            'success': False,
            'count': 0,
            'meetings': [],
            'formatted_markdown': None,
            'error': error_msg
        }


def main():
    """CLI interface for testing"""
    result = get_accepted_meetings_for_today()

    if result['success']:
        print(f"\n[OK] Found {result['count']} accepted meetings")
        print(f"[OK] Total meeting time: {result['total_meeting_hours']} hours")
        print(f"[OK] Available focus time: {result['available_focus_hours']} hours")
        print("\n" + "="*60)
        print("FORMATTED OUTPUT FOR DAILY PLAN:")
        print("="*60)
        print(result['formatted_markdown'])
        print("="*60)
    else:
        print(f"\n[ERROR] Failed to fetch calendar")
        print(f"[ERROR] {result.get('error', 'Unknown error')}")
        print("\n[INFO] Skill will fall back to manual calendar input")
        sys.exit(1)


if __name__ == '__main__':
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    main()
