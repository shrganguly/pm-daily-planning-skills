---
name: add-task
description: Add a task to a daily plan. Supports natural language dates and 4 main categories (focus, comms, learning, work) plus legacy support.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Edit, Write, Bash
argument-hint: [due-date] [category] [task description]
---

# Add Task to Daily Plan

You are a task management assistant that adds tasks to daily plans in the user's Obsidian Vault.

## Usage

**Interactive Mode (Recommended for new users):**
```
/add-task
```
You'll be prompted for:
1. Due date (today, tomorrow, next week same day)
2. Category (focus, comms, learning, work)
3. Task description

**Quick Mode (For power users):**
```
/add-task <due-date> <category> <task description>
/add-task today focus Close on section Management PM spec
/add-task tomorrow comms Reply to Karl about roadmap
/add-task monday learning Read Q2 product strategy doc
/add-task friday work Complete Liquid files work for template finder
```

## Parameters

1. **due-date** (optional, defaults to "today")
   - Natural language: "today", "tomorrow", "friday", "5th may", "feb 10", "2026-02-15"
   - Parse into YYYY-MM-DD format

2. **category** (required)
   - `focus` - Adds to "Focus Work" section
   - `comms` - Adds to "Communications" section (combines emails and messages)
   - `email` - (Legacy) Adds to "Flagged Emails Due Today" section
   - `message` - (Legacy) Adds to "Messages & Communications" section
   - `learning` - Adds to "Learning & Development" section
   - `reading` - (Legacy) Adds to "Reading & Learning" section
   - `work` - Adds to "Work Tasks" section
   - `other` - Adds to "Additional Tasks" section

3. **task** (required)
   - The task description (rest of the command line)

## Step-by-Step Process

### 1. Parse Arguments or Prompt User

**If user provides arguments:**
Parse the command line arguments:
```bash
# Example: /add-task tomorrow email Reply to Sarah about roadmap

ARG1="tomorrow"
ARG2="email"
TASK="Reply to Sarah about roadmap"
```

**If user provides no arguments or partial arguments:**
Prompt user interactively for missing information.

### 1a. Interactive Mode (When Arguments Missing)

Use AskUserQuestion to gather ALL information at once (single prompt):

**Ask all 3 questions together:**

Question 1 - Due Date:
- Today - Add to today's daily plan
- Tomorrow - Add to tomorrow's daily plan
- Next week same day - Add to same weekday next week
- Specific date - Type in Other (e.g., "monday", "feb 10", "5th may")

Question 2 - Category:
- 🧠 Focus Work - Deep work requiring concentration
- 💬 Communications - Emails, Teams messages, any communication
- 🎓 Learning & Development - Courses, training, reading, skill development
- 💼 Work Tasks - General work tasks, project items

Question 3 - Task Description:
- Close on PM Spec - Common task for closing on specifications
- Talk to engg. - Common task for engineering conversations
- Type something - User provides custom task description via "Other" text input field

**IMPORTANT:** Ask all 3 questions in a single AskUserQuestion call for speed.

### 2. Parse Date

Convert natural language date to YYYY-MM-DD:

```python
# Use Python to parse date
cd ~/.claude/skills/add-task/scripts
python parse_date.py "tomorrow"
# Output: 2026-02-07
```

Supported formats:
- "today" → today's date
- "tomorrow" → tomorrow's date
- Day names: "monday", "tuesday", etc. → next occurrence
- "5th may", "may 5" → May 5 of current/next year
- "feb 10", "10 feb" → Feb 10 of current/next year
- ISO format: "2026-02-15" → as-is

### 3. Validate Category

Ensure category is one of: focus, comms, learning, work, email, message, reading, other

If invalid, show error:
```
❌ Invalid category: {CATEGORY}

Valid categories:
- focus      - Add focus work task
- comms      - Add communication task (email/message)
- learning   - Add learning/training task
- work       - Add work task
- email      - (Legacy) Add email task
- message    - (Legacy) Add message task
- reading    - (Legacy) Add reading task
- other      - Add miscellaneous task

Example: /add-task today focus Complete PRD for auth feature
Example: /add-task tomorrow comms Reply to stakeholders about roadmap
```

### 4. Determine File Path

Based on parsed date and vault configuration:

```bash
# Read vault path from config
VAULT_PATH=$(cat ~/.claude/skills/plan-my-day/config/vault-path.txt)

# Parse date components
YEAR=$(date -d "$DATE" +%Y)
MONTH=$(date -d "$DATE" +%m)
FILE="$VAULT_PATH/DailyPlans/$YEAR/$MONTH/$DATE.md"
```

### 5. Check if Daily Plan Exists

**If file doesn't exist:**

Add the task to the backlog instead:

```bash
cd ~/.claude/skills/add-task/scripts
python backlog_manager.py add "$VAULT_PATH" "$DATE" "$CATEGORY" "$TASK"
```

Show confirmation:
```
📝 Task added to backlog for {DATE} ({DAY_NAME})

Since the daily plan for this date doesn't exist yet, I've added your task to the backlog.

When you run `/plan-my-day` for {DATE}, this task will automatically be included in the daily plan.

💡 View backlog: {VAULT_PATH}/DailyPlans/backlog.md
```

### 6. Add Task to Appropriate Section

Read the existing daily plan file and locate the appropriate section based on category:

**Category Mapping:**

| Category | Section Header | Format |
|----------|---------------|--------|
| focus | `## 🧠 Focus Work` | `- [ ] {TASK}` |
| comms | `## 💬 Communications` | `- [ ] {TASK}` |
| learning | `## 🎓 Learning & Development` | `- [ ] {TASK}` |
| work | `## 💼 Work Tasks` | `- [ ] {TASK}` |
| email | `## 📧 Flagged Emails Due Today` | `- [ ] {TASK}` |
| message | `## 💬 Messages & Communications` | `- [ ] {TASK}` |
| reading | `## 📚 Reading & Learning` | `- [ ] {TASK}` |
| other | `## 📋 Additional Tasks` | `- [ ] {TASK}` |

**Section Insertion Logic:**

1. **If section exists:** Add task to the end of that section (before the next `##` or `---`)
2. **If section doesn't exist:** Create the section after the current last section but before "End-of-Day Review"

### 7. Insert Task

Use the Edit tool to add the task:

```python
# Find the section
# Add the task at the end of the section
# Preserve all existing content
```

For email category, also update the count in the header:
- Before: `## 📧 Flagged Emails Due Today (3)`
- After: `## 📧 Flagged Emails Due Today (4)`

### 8. Confirm Success

After adding the task, show confirmation:

```
✅ Task added successfully!

📁 File: {FILE_PATH}
📅 Date: {DATE} ({DAY_NAME})
🏷️ Category: {CATEGORY}
📝 Task: {TASK}

💡 Open the file in Obsidian to see your updated plan.
```

## Interactive Prompts Structure

**IMPORTANT:** Ask all 3 questions at once using AskUserQuestion with multiple questions:

```json
{
  "questions": [
    {
      "question": "When is this task due?",
      "header": "Due Date",
      "multiSelect": false,
      "options": [
        {
          "label": "Today",
          "description": "Add to today's daily plan"
        },
        {
          "label": "Tomorrow",
          "description": "Add to tomorrow's daily plan"
        },
        {
          "label": "Next week same day",
          "description": "Add to same weekday next week"
        },
        {
          "label": "Specific Date",
          "description": "Type date in Other (e.g., 'monday', 'feb 10', '5th may')"
        }
      ]
    },
    {
      "question": "What type of task is this?",
      "header": "Category",
      "multiSelect": false,
      "options": [
        {
          "label": "🧠 Focus Work",
          "description": "Deep work requiring concentration (PRDs, specs, design)"
        },
        {
          "label": "💬 Communications",
          "description": "Emails, Teams messages, any communication"
        },
        {
          "label": "🎓 Learning & Development",
          "description": "Courses, training, reading, skill development"
        },
        {
          "label": "💼 Work Tasks",
          "description": "General work tasks, project items"
        }
      ]
    },
    {
      "question": "What's the task? (Be specific and actionable)",
      "header": "Task",
      "multiSelect": false,
      "options": [
        {
          "label": "Close on PM Spec",
          "description": "Work on closing/finalizing product management specifications"
        },
        {
          "label": "Talk to engg.",
          "description": "Have a conversation or meeting with engineering team"
        },
        {
          "label": "Type something",
          "description": "Enter your custom task description in the Other field below"
        }
      ]
    }
  ]
}
```

This asks all 3 questions at once for faster interaction.

## Edge Cases

### If multiple dates match (e.g., "May 5" - this year or next?)

Choose the nearest future date. If May 5 has passed this year, use next year.

### If section needs to be created

Create section with proper formatting:

```markdown
## 📚 Reading & Learning

- [ ] {TASK}
  - *Estimated time:* 30 min

---
```

Insert before the "End-of-Day Review" section.

### If daily plan is for a past date

Show warning:
```
⚠️ You're adding a task to a past date ({DATE})

This might be for retroactive planning. Proceed? (y/n)
```

### If task description is very long (>100 chars)

Suggest breaking it down:
```
💡 Tip: That's a long task! Consider breaking it into smaller subtasks in the daily plan.
```

## Smart Defaults

**Keep tasks clean and simple:**
- No time estimates
- No action labels
- Just checkbox + task description

## Examples

### Example 1: Add focus work for today
```
/add-task today focus Close on section Management PM spec

→ Adds to today's plan in Focus Work section
```

### Example 2: Add communication task for tomorrow
```
/add-task tomorrow comms Reply to Karl about roadmap

→ Adds to tomorrow's plan in Communications section
```

### Example 3: Add learning task for specific date
```
/add-task feb 10 learning Read Q2 product strategy doc and deck Bindiya shared

→ Adds to Feb 10's plan in Learning & Development section
```

### Example 4: Add work task for next Monday
```
/add-task monday work Complete Liquid files work for template finder and doc gen

→ Adds to next Monday's plan in Work Tasks section
```

### Example 5: Legacy category support
```
/add-task today email Reply to stakeholders

→ Still works! Adds to today's plan (legacy support maintained)
```

## Related Skills

- `/plan-my-day` - Generate full daily plan
- `/review-day` - Review and reflect on the day (if exists)
- `/list-tasks` - Show all tasks across all days (if exists)

## Best Practices

1. **Be specific:** "Reply to John about PRD feedback" vs. "Email John"
2. **Use categories consistently:** Helps with organization and time tracking
3. **Don't over-plan:** Add only actionable tasks you'll actually do
4. **Review regularly:** Update task status as you complete them
