#!/usr/bin/env python3
"""
Date Parser for add-task skill
Converts natural language dates to YYYY-MM-DD format
"""

import sys
from datetime import datetime, timedelta
import re


def parse_natural_date(date_str):
    """
    Parse natural language date to YYYY-MM-DD format

    Supports:
    - "today", "tomorrow"
    - Day names: "monday", "tuesday", etc.
    - Month day: "5th may", "may 5", "feb 10", "10 feb"
    - ISO format: "2026-02-15"

    Returns:
        str: Date in YYYY-MM-DD format
    """
    date_str = date_str.lower().strip()
    today = datetime.now()

    # Handle "today"
    if date_str == "today":
        return today.strftime("%Y-%m-%d")

    # Handle "tomorrow"
    if date_str == "tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # Handle day names (monday, tuesday, etc.)
    day_names = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6
    }

    if date_str in day_names:
        target_day = day_names[date_str]
        current_day = today.weekday()
        days_ahead = (target_day - current_day) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week if it's the same day
        next_date = today + timedelta(days=days_ahead)
        return next_date.strftime("%Y-%m-%d")

    # Handle ISO format (YYYY-MM-DD)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        # Validate it's a real date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except:
            pass

    # Handle month day formats
    # Patterns: "5th may", "may 5", "feb 10", "10 feb", "5 may", "may 5th"
    month_names = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12
    }

    # Remove ordinal suffixes (st, nd, rd, th)
    date_str_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)

    # Try "month day" pattern (e.g., "may 5")
    for month_name, month_num in month_names.items():
        if month_name in date_str_clean:
            # Extract day number
            day_match = re.search(r'\b(\d{1,2})\b', date_str_clean)
            if day_match:
                day = int(day_match.group(1))

                # Determine year (current year or next year)
                current_year = today.year
                try:
                    target_date = datetime(current_year, month_num, day)

                    # If date is in the past, use next year
                    if target_date < today:
                        target_date = datetime(current_year + 1, month_num, day)

                    return target_date.strftime("%Y-%m-%d")
                except ValueError:
                    # Invalid day for month
                    return None

    # If nothing matched
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_date.py <date_string>")
        print("Examples:")
        print("  python parse_date.py today")
        print("  python parse_date.py tomorrow")
        print("  python parse_date.py friday")
        print("  python parse_date.py \"5th may\"")
        print("  python parse_date.py \"feb 10\"")
        sys.exit(1)

    date_str = " ".join(sys.argv[1:])
    result = parse_natural_date(date_str)

    if result:
        print(result)
        sys.exit(0)
    else:
        print(f"ERROR: Could not parse date: {date_str}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
