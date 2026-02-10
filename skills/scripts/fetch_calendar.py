#!/usr/bin/env python3
"""
Outlook Calendar Fetcher for Daily Planning System
Fetches today's calendar events from Microsoft Graph API
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

try:
    from msal import PublicClientApplication
    import requests
except ImportError:
    print("❌ Required libraries not installed.")
    print("Run: pip install msal requests")
    sys.exit(1)


class OutlookCalendarFetcher:
    """Fetches calendar events from Microsoft Outlook/365"""

    def __init__(self, config_path=None):
        """Initialize with config file path"""
        if config_path is None:
            # Default config path
            skill_dir = Path(__file__).parent.parent
            config_path = skill_dir / "config" / "credentials.json"

        self.config_path = Path(config_path)
        self.token_cache_path = self.config_path.parent / ".token_cache"
        self.config = self._load_config()
        self.app = self._create_msal_app()

    def _load_config(self):
        """Load credentials from config file"""
        if not self.config_path.exists():
            print(f"❌ Config file not found: {self.config_path}")
            print("\n📝 Please create config file with:")
            print(json.dumps({
                "client_id": "YOUR_CLIENT_ID",
                "tenant_id": "YOUR_TENANT_ID",
                "authority": "https://login.microsoftonline.com/YOUR_TENANT_ID",
                "scope": ["https://graph.microsoft.com/Calendars.Read"]
            }, indent=2))
            sys.exit(1)

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _create_msal_app(self):
        """Create MSAL public client application"""
        authority = self.config.get('authority')
        client_id = self.config.get('client_id')

        if not authority or not client_id:
            print("❌ Invalid config: missing client_id or authority")
            sys.exit(1)

        return PublicClientApplication(
            client_id=client_id,
            authority=authority,
            token_cache=self._get_token_cache()
        )

    def _get_token_cache(self):
        """Load or create token cache"""
        from msal import SerializableTokenCache

        cache = SerializableTokenCache()

        if self.token_cache_path.exists():
            with open(self.token_cache_path, 'r') as f:
                cache.deserialize(f.read())

        return cache

    def _save_token_cache(self):
        """Save token cache to disk"""
        if self.app.token_cache.has_state_changed:
            with open(self.token_cache_path, 'w') as f:
                f.write(self.app.token_cache.serialize())

    def _get_access_token(self, force_reauth=False):
        """Get access token (from cache or via authentication)"""
        scope = self.config.get('scope', ['https://graph.microsoft.com/Calendars.Read'])

        # Try to get token from cache
        accounts = self.app.get_accounts()

        if accounts and not force_reauth:
            print("🔐 Using cached authentication...")
            result = self.app.acquire_token_silent(scope, account=accounts[0])
            if result and 'access_token' in result:
                return result['access_token']

        # Need interactive authentication
        print("\n🔐 Authentication required. Opening browser...")
        print("Please sign in with your Microsoft work account.")

        # Device flow authentication (works better for CLI)
        flow = self.app.initiate_device_flow(scopes=scope)

        if "user_code" not in flow:
            raise Exception("Failed to create device flow")

        print(f"\n📋 To sign in, use a web browser to open the page:")
        print(f"   {flow['message']}")
        print("\nWaiting for authentication...")

        result = self.app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self._save_token_cache()
            print("✅ Authentication successful!")
            return result['access_token']
        else:
            error = result.get('error_description', 'Unknown error')
            raise Exception(f"Authentication failed: {error}")

    def fetch_today_events(self, force_reauth=False):
        """Fetch today's calendar events"""
        try:
            # Get access token
            token = self._get_access_token(force_reauth)

            # Set up time range (today, from start to end)
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            # Format for Microsoft Graph API
            start_time = today_start.isoformat() + 'Z'
            end_time = today_end.isoformat() + 'Z'

            # Microsoft Graph API endpoint
            endpoint = "https://graph.microsoft.com/v1.0/me/calendar/calendarView"

            # Query parameters
            params = {
                '$select': 'subject,start,end,location,attendees,isAllDay,showAs,organizer',
                '$orderby': 'start/dateTime',
                'startDateTime': start_time,
                'endDateTime': end_time
            }

            # Make API request
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            print(f"📅 Fetching events for {today_start.strftime('%Y-%m-%d')}...")

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code == 200:
                events_data = response.json()
                events = self._parse_events(events_data.get('value', []))
                print(f"✅ Found {len(events)} events")
                return events
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                print(f"❌ API error: {error_msg}")
                return []

        except Exception as e:
            print(f"❌ Error fetching calendar: {e}")
            return []

    def _parse_events(self, raw_events):
        """Parse raw events into clean format"""
        parsed_events = []

        for event in raw_events:
            # Extract basic info
            subject = event.get('subject', 'Untitled')
            is_all_day = event.get('isAllDay', False)

            # Parse start/end times
            start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))

            # Convert to local time
            start_local = start_dt.astimezone()
            end_local = end_dt.astimezone()

            # Format times
            if is_all_day:
                start_time = "All day"
                end_time = ""
            else:
                start_time = start_local.strftime("%I:%M %p").lstrip('0')
                end_time = end_local.strftime("%I:%M %p").lstrip('0')

            # Calculate duration
            duration_min = int((end_local - start_local).total_seconds() / 60)

            # Get location
            location = event.get('location', {}).get('displayName', '')

            # Get attendees count
            attendees = event.get('attendees', [])
            attendee_count = len(attendees)

            # Get organizer
            organizer = event.get('organizer', {}).get('emailAddress', {}).get('name', '')

            # Determine priority/importance
            show_as = event.get('showAs', 'busy')  # busy, free, tentative, etc.

            parsed_events.append({
                'subject': subject,
                'start': start_time,
                'end': end_time,
                'start_datetime': start_local.isoformat(),
                'end_datetime': end_local.isoformat(),
                'duration_minutes': duration_min,
                'location': location,
                'attendee_count': attendee_count,
                'organizer': organizer,
                'show_as': show_as,
                'is_all_day': is_all_day
            })

        return parsed_events

    def format_for_daily_plan(self, events):
        """Format events for daily plan markdown"""
        if not events:
            return "No meetings scheduled for today"

        # Separate into morning/afternoon/evening
        morning = []
        afternoon = []
        evening = []

        total_meeting_time = 0

        for event in events:
            total_meeting_time += event['duration_minutes']

            # Create formatted line
            if event['is_all_day']:
                line = f"- All day: {event['subject']}"
            else:
                line = f"- {event['start']} - {event['end']}: {event['subject']}"

                if event['location']:
                    line += f" ({event['location']})"

            # Categorize by time
            hour = datetime.fromisoformat(event['start_datetime']).hour

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

        # Calculate available focus time (8-hour day minus meetings)
        available_minutes = 480 - total_meeting_time  # 480 min = 8 hours
        available_hours = available_minutes / 60

        formatted += f"\n**Available Focus Time:** {available_hours:.1f} hours"

        return formatted


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Fetch Outlook calendar events')
    parser.add_argument('--test', action='store_true', help='Run test fetch')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--reauth', action='store_true', help='Force re-authentication')
    parser.add_argument('--config', type=str, help='Config file path')

    args = parser.parse_args()

    try:
        # Create fetcher
        fetcher = OutlookCalendarFetcher(config_path=args.config)

        # Fetch events
        events = fetcher.fetch_today_events(force_reauth=args.reauth)

        if not events:
            print("\n📅 No events found for today")
            if args.json:
                print(json.dumps([]))
            return

        # Output results
        if args.json:
            print(json.dumps(events, indent=2))
        elif args.test:
            print(f"\nFound {len(events)} events:")
            for event in events:
                if event['is_all_day']:
                    print(f"- All day: {event['subject']}")
                else:
                    print(f"- {event['start']} - {event['end']}: {event['subject']}")
        else:
            formatted = fetcher.format_for_daily_plan(events)
            print("\n" + formatted)

    except KeyboardInterrupt:
        print("\n\n⚠️ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
