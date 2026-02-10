# Sub-Agent Architecture: get_accepted_meetings_for_today

## Overview

The `/plan-my-day` skill uses a **sub-agent pattern** to automatically fetch calendar meetings from Outlook.

## Architecture

```
User runs: /plan-my-day
        ↓
Claude Code invokes SKILL.md
        ↓
Skill calls sub-agent: get_accepted_meetings_for_today.py
        ↓
Sub-agent connects to Outlook MAPI
        ↓
Sub-agent fetches accepted meetings
        ↓
Sub-agent filters personal blocks
        ↓
Sub-agent returns formatted markdown
        ↓
Skill inserts calendar into daily plan
        ↓
Daily plan saved to Obsidian
```

## Sub-Agent: get_accepted_meetings_for_today

### Location
```
~/.claude/skills/plan-my-day/scripts/get_accepted_meetings_for_today.py
```

### Purpose
Fetch today's accepted calendar meetings from Outlook and return formatted markdown.

### What It Does

1. **Connects to Outlook** via MAPI (Windows COM interface)
2. **Fetches today's events** from default calendar
3. **Filters intelligently:**
   - ✅ Include: Accepted meetings
   - ✅ Include: Meetings you organized
   - ❌ Exclude: Tentative meetings
   - ❌ Exclude: Declined meetings
   - ❌ Exclude: Personal blocks (lunch, focus time, etc.)
4. **Formats output** as markdown:
   - Organizes by time: Morning / Afternoon / Evening
   - Marks large meetings (10+ attendees)
   - Shows location for in-person meetings
   - Calculates total meeting time
   - Calculates available focus time
5. **Returns structured data:**
   ```python
   {
       'success': True,
       'count': 14,
       'meetings': [...],
       'formatted_markdown': "**Morning:**\n- 9am: Standup\n...",
       'total_meeting_hours': 10.5,
       'available_focus_hours': 0
   }
   ```

### Error Handling

If Outlook is unavailable or any error occurs:
- Returns `{'success': False, 'error': '...'}`
- Skill falls back to manual calendar input
- User experience is uninterrupted

### Dependencies

- **pywin32**: Python Windows COM library
- **Outlook desktop app**: Must be installed and configured
- **Windows OS**: MAPI only works on Windows

### Usage

**From command line (testing):**
```bash
cd ~/.claude/skills/plan-my-day/scripts
python get_accepted_meetings_for_today.py
```

**From skill (automatic):**
The SKILL.md automatically calls this script when `/plan-my-day` runs.

## Benefits of Sub-Agent Pattern

### 1. **Separation of Concerns**
- Skill focuses on daily planning logic
- Sub-agent focuses on calendar integration
- Clean, maintainable code

### 2. **Testability**
- Sub-agent can be tested independently
- Easy to debug calendar issues
- Can run manual tests anytime

### 3. **Fallback Gracefully**
- If sub-agent fails, skill continues with manual input
- No crashes or broken workflows
- User always gets a daily plan

### 4. **Reusability**
- Other skills can use this sub-agent
- Example: `/weekly-review` could call it for week's meetings
- Example: `/meeting-prep` could call it for today's meetings

### 5. **Easy Updates**
- Update calendar logic without touching skill
- Add new filters (exclude keywords) easily
- Switch to different calendar source (Google, etc.) without skill changes

## Customization

### Add More Exclude Keywords

Edit `fetch_calendar_outlook.py`:

```python
exclude_keywords = [
    'focus time',
    'lunch',
    'break',
    'personal time',
    'deep work',
    'do not schedule',
    'hold',
    'block',
    'commute',      # Add new
    'gym',          # Add new
    'meditation'    # Add new
]
```

### Change What Meetings Are Included

Edit `get_accepted_meetings_for_today.py`:

```python
# Include tentative meetings too
events = fetcher.fetch_today_events(accepted_only=False)
```

### Format Output Differently

Edit `fetch_calendar_outlook.py`, method `format_for_daily_plan()`:

```python
# Example: Add emoji indicators
if event['attendee_count'] > 20:
    line += " 🎪 (All-hands)"
if 'demo' in event['subject'].lower():
    line += " 🎬 (Demo)"
```

## Future Enhancements

### Planned (Phase 2)

1. **Smart Focus Time Suggestions**
   - Analyze calendar gaps
   - Recommend best 2-hour block
   - Avoid back-to-back meetings

2. **Meeting Prep Reminders**
   - Flag meetings needing preparation
   - Extract meeting objectives from body
   - Link to related documents

3. **Conflict Detection**
   - Warn about double-booked slots
   - Suggest which meeting to decline
   - Calculate actual available time (not negative!)

### Possible (Phase 3)

1. **Multi-Calendar Support**
   - Personal + work calendars
   - Shared team calendars
   - Aggregate all sources

2. **Travel Time Calculation**
   - Detect in-person meetings
   - Add commute time
   - Adjust focus time accordingly

3. **AI-Powered Prioritization**
   - Rank meetings by importance
   - Suggest which to skip/delegate
   - Optimize for focus work

## Troubleshooting

### Sub-agent fails to run

**Error:** `[ERROR] Could not import OutlookMAPIFetcher`

**Solution:** Make sure `fetch_calendar_outlook.py` is in the same directory:
```bash
ls ~/.claude/skills/plan-my-day/scripts/
# Should see both files
```

---

### Outlook connection fails

**Error:** `[ERROR] Failed to connect to Outlook`

**Solution:**
1. Open Outlook desktop app
2. Make sure it's configured with your account
3. Try running script manually to test
4. Check pywin32 is installed: `pip list | grep pywin32`

---

### No meetings returned

**Possible causes:**
1. All meetings are tentative (not accepted yet)
2. All meetings filtered as personal blocks
3. Wrong calendar being checked

**Debug:**
```bash
# See all meetings (including tentative)
python get_accepted_meetings_for_today.py --all

# Check what's being filtered
# (Look for "X personal blocks filtered" message)
```

---

### Encoding errors (emojis in meeting titles)

**Fixed in current version.** The script handles UTF-8 encoding properly.

If you see encoding errors, make sure you're using the latest version of the script.

## Performance

**Typical execution time:**
- First run: ~2-3 seconds (Outlook connection)
- Subsequent runs: ~1-2 seconds (cached connection)

**Impact on /plan-my-day:**
- Adds 2-3 seconds to daily planning workflow
- Saves 30 seconds of manual typing
- **Net time saved: ~27 seconds/day**

## Security & Privacy

### Data Flow
```
Outlook (local) → Python script (local) → Daily plan (local)
```

**All data stays on your machine:**
- ✅ No cloud API calls
- ✅ No data sent to external services
- ✅ No authentication tokens stored
- ✅ Works offline (after Outlook syncs)

### Access Required
- Read access to Outlook calendar
- No write access (can't modify meetings)
- No email access (only calendar)

## Related Files

```
~/.claude/skills/plan-my-day/
├── SKILL.md                                   # Main skill definition
├── scripts/
│   ├── get_accepted_meetings_for_today.py    # Sub-agent (this)
│   └── fetch_calendar_outlook.py              # Outlook MAPI interface
├── config/
│   └── vault-path.txt                         # Obsidian vault location
└── SUB-AGENT-ARCHITECTURE.md                  # This document
```

## Testing Checklist

Before using in production:

- [ ] Test sub-agent standalone: `python get_accepted_meetings_for_today.py`
- [ ] Verify it fetches today's meetings correctly
- [ ] Check that personal blocks are filtered
- [ ] Confirm tentative meetings are excluded
- [ ] Test with no meetings day (should handle gracefully)
- [ ] Test with Outlook closed (should fail gracefully)
- [ ] Run `/plan-my-day` end-to-end
- [ ] Verify calendar section in generated plan is correct
- [ ] Check available focus time calculation

## Support

**If you need help:**
1. Test the sub-agent directly first
2. Check error messages in output
3. Review this architecture document
4. Ask Claude Code: "Debug my calendar sub-agent"

---

**Architecture designed:** 2026-02-05
**Last updated:** 2026-02-05
**Version:** 1.0
