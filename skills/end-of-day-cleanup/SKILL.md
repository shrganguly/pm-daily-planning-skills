---
name: end-of-day-cleanup
description: Manually trigger end-of-day cleanup to move unchecked tasks to backlog. Backup for automatic 11:45 PM cleanup.
disable-model-invocation: false
user-invocable: true
allowed-tools: Bash, Read
argument-hint: [date]
---

# End of Day Cleanup

Manually trigger the end-of-day cleanup process to move unchecked tasks from a daily plan to the backlog.

## Purpose

This skill provides a **manual backup** for the automatic cleanup that runs at 11:45 PM every night. Use it:
- When the automatic cleanup fails
- To clean up a specific past date
- To test the cleanup process
- When you want to clean up early (before 11:45 PM)

## Usage

```bash
# Clean up today's plan (default)
/end-of-day-cleanup

# Clean up a specific date
/end-of-day-cleanup 2026-02-05
/end-of-day-cleanup yesterday
```

## Process

### 1. Parse Arguments (if any)

If a date is provided, parse it:
- "today" → today's date
- "yesterday" → yesterday's date
- ISO format: "2026-02-05" → as-is
- If no argument → default to today

### 2. Run Cleanup Script

Execute the cleanup script:

```bash
cd ~/.claude/skills/plan-my-day/scripts

# For today (default)
python end_of_day_cleanup.py --config

# For specific date (if needed in future)
# The script currently uses today's date automatically
```

The script will:
1. Read the daily plan for the specified date
2. Extract all unchecked tasks (- [ ] format)
3. Organize them by section (emails, focus work, reading, etc.)
4. Add them to backlog under "Backlog due from <date>" section
5. Report how many tasks were carried over

### 3. Display Results

Show the user what happened:

**If tasks were carried over:**
```
✅ End-of-day cleanup completed!

📊 Summary:
- 5 tasks carried over to backlog
  - Focus Work: 3 tasks
  - Emails: 2 tasks

📋 Backlog Location:
  {VAULT_PATH}/DailyPlans/backlog.md

💡 These tasks will appear in tomorrow's daily plan under "Old Tasks Backlog"

Next Steps:
- Run `/plan-my-day` tomorrow to see carried-over tasks
- Or manually review backlog.md now
```

**If no tasks to carry over:**
```
🎉 All tasks completed!

No unchecked tasks found in today's plan. Nothing to carry over.

Great job staying on top of your work! 🚀
```

**If daily plan doesn't exist:**
```
⚠️ No daily plan found for {DATE}

Cannot run cleanup - no plan exists for this date.

💡 Tip: Run `/plan-my-day` first to create a daily plan.
```

**If cleanup fails:**
```
❌ Cleanup failed

Error: {ERROR_MESSAGE}

Troubleshooting:
1. Check that vault path is configured correctly
2. Verify the daily plan file exists
3. Check backlog.md is accessible
4. Try running manually:
   cd ~/.claude/skills/plan-my-day/scripts
   python end_of_day_cleanup.py --config
```

## Important Notes

### Idempotency
Running cleanup multiple times on the same day will:
- Add duplicate carryover sections to backlog
- Should be avoided - cleanup is designed to run once per day

To avoid duplicates:
- Check backlog.md first for existing carryover sections
- Only run cleanup once per day
- Use automatic scheduling (runs at 11:45 PM)

### Automatic vs Manual

**Automatic (Recommended):**
- Runs via Windows Task Scheduler at 11:45 PM
- Setup: `powershell ~/.claude/skills/plan-my-day/scripts/setup_daily_cleanup.ps1`
- No manual intervention needed
- Consistent timing

**Manual (Backup):**
- Use this skill when automatic fails
- Useful for testing
- Can specify custom dates
- Run anytime during the day

### What Gets Carried Over

The cleanup extracts ALL unchecked tasks:
- ✅ **Flagged Emails** (- [ ]) - **MUST be carried over** to 📧 Flagged Emails section
- ✅ Unchecked message/communication tasks (- [ ])
- ✅ Unchecked reading/learning tasks (- [ ])
- ✅ Unchecked focus work tasks (- [ ] or numbered)
- ✅ Unchecked work/other tasks (- [ ])
- ❌ Calendar meetings (not carried over - informational only)
- ❌ Completed tasks (- [x])
- ❌ End-of-day review checklist
- ❌ Daily notes (free-form content)

**IMPORTANT:** Flagged emails MUST always be carried over since they represent actionable items that weren't completed during the day. They should appear in the backlog under "📧 Flagged Emails" section.

### Backlog Structure

Carried-over tasks are stored as:

```markdown
## 🔄 Backlog due from 2026-02-06 (Friday)

*5 tasks carried over from Friday*

### 📧 Emails
- [ ] Task 1
  - *Carried over from:* 2026-02-06

### 🧠 Focus Work
- [ ] Task 2
  - *Carried over from:* 2026-02-06
```

## Examples

### Example 1: Run cleanup at end of day
```
User: /end-of-day-cleanup

Result:
✅ 3 tasks carried over to backlog
  - Focus Work: 2 tasks
  - Emails: 1 task
```

### Example 2: Clean up yesterday's plan (forgot to run)
```
User: /end-of-day-cleanup yesterday

Result:
✅ 7 tasks carried over from 2026-02-05
```

### Example 3: All tasks completed
```
User: /end-of-day-cleanup

Result:
🎉 All tasks completed! Nothing to carry over.
```

## Related Skills

- `/plan-my-day` - Generate daily plan (will show carried-over tasks)
- `/add-task` - Add tasks to future dates or backlog

## Automatic Cleanup Status

To check if automatic cleanup is scheduled:
```bash
# Windows Task Scheduler
Get-ScheduledTask -TaskName "ClaudeCode-DailyPlanCleanup"
```

To set up automatic cleanup:
```powershell
cd ~/.claude/skills/plan-my-day/scripts
.\setup_daily_cleanup.ps1
```

## Best Practices

1. **Let automatic run first** - Don't manually trigger if automatic hasn't run yet (wait until after 11:45 PM)
2. **Check backlog before running** - Avoid creating duplicate carryover sections
3. **Complete tasks during the day** - Best practice is to check off completed tasks so cleanup is accurate
4. **Review carried-over tasks** - Next morning, prioritize clearing old backlog items

---

*This skill is a manual backup for the automatic cleanup process. For best results, set up automatic scheduling.*
