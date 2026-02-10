#!/usr/bin/env python3
"""Debug script to see what's actually in the calendar"""

import sys
from datetime import datetime, timedelta

try:
    import win32com.client
except ImportError:
    print("pywin32 not installed")
    sys.exit(1)

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("[*] Connecting to Outlook...")
outlook = win32com.client.Dispatch("Outlook.Application")
namespace = outlook.GetNamespace("MAPI")
print("[OK] Connected")

# Get calendar
calendar = namespace.GetDefaultFolder(9)  # olFolderCalendar
items = calendar.Items

# IMPORTANT: Set IncludeRecurrences to False to avoid getting all recurring instances
items.IncludeRecurrences = False
items.Sort("[Start]")

# Get today's date range
today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)

print(f"\n[*] Looking for events on: {today_start.strftime('%Y-%m-%d (%A)')}")
print(f"[*] Date range: {today_start} to {today_end}")

# Try to restrict - but we'll also manually filter
start_str = today_start.strftime("%m/%d/%Y %H:%M %p")
end_str = today_end.strftime("%m/%d/%Y %H:%M %p")

print(f"\n[*] Filter string: [Start] >= '{start_str}' AND [Start] < '{end_str}'")

# Apply restriction
filter_str = f"[Start] >= '{start_str}' AND [Start] < '{end_str}'"
restricted_items = items.Restrict(filter_str)

print(f"\n[*] Outlook Restrict returned {restricted_items.Count} items")

# Now manually check each one
print("\n" + "="*80)
print("EVENTS FOUND:")
print("="*80)

count = 0
for item in restricted_items:
    try:
        subject = item.Subject or "Untitled"
        start_dt = item.Start
        end_dt = item.End

        # Check if this is actually today
        if start_dt.date() == today_start.date():
            count += 1
            start_time = start_dt.strftime("%I:%M %p").lstrip('0')
            end_time = end_dt.strftime("%I:%M %p").lstrip('0')

            # Get response status
            try:
                response_status = item.ResponseStatus
                status_map = {0: "None", 1: "Organizer", 2: "Tentative", 3: "Accepted", 4: "Declined"}
                status_str = status_map.get(response_status, "Unknown")
            except:
                status_str = "Unknown"

            print(f"\n{count}. {subject}")
            print(f"   Time: {start_time} - {end_time}")
            print(f"   Date: {start_dt.strftime('%Y-%m-%d')}")
            print(f"   Status: {status_str}")
            print(f"   Location: {item.Location or 'None'}")
        else:
            print(f"\n[WRONG DATE] {subject}")
            print(f"   Expected: {today_start.date()}")
            print(f"   Got: {start_dt.date()}")

    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*80)
print(f"TOTAL EVENTS FOR TODAY: {count}")
print("="*80)
