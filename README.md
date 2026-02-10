# PM Daily Planning Skills for Claude Code

> A comprehensive task management system for Product Managers using Claude Code, integrating with Outlook and Obsidian.

---

## 🎯 What is This?

A lean, automated daily planning system that helps Product Managers:
- Auto-fetch flagged emails and calendar from Outlook
- Generate structured daily plans in Obsidian
- Track tasks across days with intelligent carryover
- Maintain a clean backlog system

Built using **Claude Code skills** - reusable automation workflows that run via slash commands.

---

## ✨ Features

### Three Main Skills:

**1. `/plan-my-day`** - Morning Planning
Auto-fetches your flagged emails and accepted meetings from Outlook, pulls pre-planned tasks from backlog, and generates a structured daily plan in Obsidian.

**2. `/add-task`** - Quick Task Capture
Add tasks to today's plan or schedule them for future dates. Supports natural language dates and multiple task categories.

**3. `/end-of-day-cleanup`** - Evening Cleanup
Automatically moves uncompleted tasks back to backlog at 11:45 PM. Preserves original carryover dates so you can see which tasks have been lingering.

---

## 📋 Prerequisites

Before installing, make sure you have:

- ✅ **Claude Code** installed ([Get it here](https://claude.com/claude-code))
- ✅ **Outlook Desktop** app (Windows) configured with your account
- ✅ **Obsidian** or any markdown editor ([Download Obsidian](https://obsidian.md))
- ✅ **Python 3.7+** with `pywin32` package
- ✅ **Git** (for cloning this repository)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Python Dependencies

```bash
pip install pywin32
```

### Step 2: Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/pm-daily-planning-skills.git
cd pm-daily-planning-skills
```

### Step 3: Copy Skills to Claude Code Directory

**Windows:**
```bash
# Copy all three skills
xcopy /E /I skills\plan-my-day %USERPROFILE%\.claude\skills\plan-my-day
xcopy /E /I skills\add-task %USERPROFILE%\.claude\skills\add-task
xcopy /E /I skills\end-of-day-cleanup %USERPROFILE%\.claude\skills\end-of-day-cleanup
```

**macOS/Linux:**
```bash
# Copy all three skills
cp -r skills/plan-my-day ~/.claude/skills/
cp -r skills/add-task ~/.claude/skills/
cp -r skills/end-of-day-cleanup ~/.claude/skills/
```

### Step 4: Configure Your Obsidian Vault Path

Edit the config file:
```bash
# Windows
notepad %USERPROFILE%\.claude\skills\plan-my-day\config\vault-path.txt

# macOS/Linux
nano ~/.claude/skills/plan-my-day/config/vault-path.txt
```

Add your Obsidian vault path (one line):
```
C:\Users\YOUR_NAME\Documents\ObsidianVault\VAULT_NAME
```

Or wherever you want your daily plans to be stored.

### Step 5: Create Obsidian Vault Structure

Inside your Obsidian vault, create this folder:
```
YourVault/
└── DailyPlans/
    ├── backlog.md (will be auto-created)
    └── YYYY/
        └── MM/
            └── YYYY-MM-DD.md (auto-created by /plan-my-day)
```

### Step 6: Test It!

Restart Claude Code (or run `/reload-skills`), then:

```bash
/plan-my-day
```

You should be prompted for your focus work goal, and a daily plan will be generated! 🎉

---

## 📖 How to Use

### Morning Routine (9:00 AM)

```bash
/plan-my-day
```

**What it does:**
1. Fetches your flagged emails due today from Outlook
2. Fetches your accepted meetings from Outlook calendar
3. Pulls any pre-planned tasks from backlog
4. Prompts you for your main focus work goal
5. Generates a structured daily plan in Obsidian

**Output:** `DailyPlans/2026/02/2026-02-10.md`

**Example Plan:**
```markdown
## 🧠 Focus Work
- [ ] Complete PRD for authentication feature
- [ ] Review dashboard designs
  - *Carried over from:* 2026-02-08

## 💬 Communications
- [ ] Respond to stakeholder about roadmap

## 📧 Flagged Emails Due Today (3)
- [ ] **John Doe**: PRD feedback needed
- [ ] **Jane Smith**: Q2 planning sync

## 📅 Calendar & Meetings (2)
**Morning:**
- 10:00 AM - 11:00 AM: Team Standup

**Available Focus Time:** 6.5 hours
```

### Throughout the Day

**Add a new task:**
```bash
/add-task
```

Or quick mode:
```bash
/add-task tomorrow focus Complete API documentation
/add-task friday comms Send update to stakeholders
```

**Supported categories:**
- `focus` - Deep work requiring concentration
- `comms` - Emails, Teams messages, communication
- `learning` - Courses, training, reading
- `work` - General work tasks

**Natural language dates:**
- `today`, `tomorrow`
- `monday`, `friday` (next occurrence)
- `feb 15`, `march 3`
- `2026-03-10`

### Evening Routine (11:45 PM - Automatic)

The system automatically runs cleanup, but you can trigger manually:

```bash
/end-of-day-cleanup
```

**What it does:**
1. Finds all unchecked tasks in today's plan
2. Moves them to backlog with "Carried over from: DATE"
3. Removes unchecked tasks from daily plan
4. Marks today's plan as "complete"

**Important:** The carryover date is ALWAYS the original date when the task was first carried over. This helps you see which tasks have been lingering!

---

## 🎓 Key Concepts

### Task Flow

```
1. Add task via /add-task
   ↓
2. If date has no plan → Goes to backlog.md
   If date has plan → Added directly to plan
   ↓
3. Run /plan-my-day → Pulls tasks from backlog into daily plan
   ↓
4. Work on tasks during the day (check them off)
   ↓
5. End of day (11:45 PM) → Unchecked tasks → Back to backlog as "carryover"
   ↓
6. Next day's /plan-my-day → Pulls carryover tasks
```

### Carryover Task Integration

Carryover tasks are **integrated into their respective sections**, not in a separate section:

```markdown
## 🧠 Focus Work
- [ ] New task for today
- [ ] Old task
  - *Carried over from:* 2026-02-08  # Shows original date
- [ ] Another old task
  - *Carried over from:* 2026-02-09
```

This makes it easy to see all focus work together, and the "Carried over from" date shows task age.

---

## ⚙️ Advanced Setup

### Windows Task Scheduler (Auto End-of-Day Cleanup)

To run cleanup automatically at 11:45 PM every day:

1. Open Task Scheduler
2. Create Basic Task:
   - **Name:** Claude Daily Plan Cleanup
   - **Trigger:** Daily at 11:45 PM
   - **Action:** Start a program
   - **Program:** `python`
   - **Arguments:** `C:\Users\YOUR_NAME\.claude\skills\plan-my-day\scripts\end_of_day_cleanup.py --config`

### Customizing the Plan Template

Edit `~/.claude/skills/plan-my-day/SKILL.md` to customize:
- Section order
- Section headers
- Default prompts

---

## 🛠️ Troubleshooting

### Outlook Connection Issues

**Error:** `Failed to connect to Outlook`

**Solutions:**
1. Make sure Outlook Desktop app is installed (not just web version)
2. Open Outlook and make sure you're logged in
3. Try restarting Outlook
4. Check that you've opened Outlook at least once after installation

### Skills Not Showing Up

**Run in Claude Code:**
```bash
/reload-skills
```

Or restart Claude Code completely.

### Vault Path Not Found

**Check your config:**
```bash
cat ~/.claude/skills/plan-my-day/config/vault-path.txt
```

Make sure the path:
- Is absolute (not relative)
- Uses forward slashes `/` or escaped backslashes `\\`
- Points to an existing directory

### Tasks Not Being Removed from Backlog

After creating a daily plan, the script should automatically remove tasks from backlog. If not:

```bash
# Manually run removal
cd ~/.claude/skills/plan-my-day/scripts
python get_backlog_tasks_for_date.py "YOUR_VAULT_PATH" --date 2026-02-10 --remove
```

---

## 📁 File Structure

```
pm-daily-planning-skills/
├── README.md (this file)
├── SETUP.md (detailed setup guide)
├── LICENSE
├── .gitignore
├── skills/
│   ├── plan-my-day/
│   │   ├── SKILL.md
│   │   ├── config/
│   │   │   └── vault-path.txt.example
│   │   └── scripts/
│   │       ├── get_accepted_meetings_for_today.py
│   │       ├── get_flagged_emails_today.py
│   │       ├── get_backlog_tasks_for_date.py
│   │       └── end_of_day_cleanup.py
│   ├── add-task/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── backlog_manager.py
│   │       └── parse_date.py
│   └── end-of-day-cleanup/
│       └── SKILL.md
├── docs/
│   ├── examples/
│   │   └── sample-daily-plan.md
│   └── screenshots/
└── requirements.txt
```

---

## 🤝 Contributing

Found a bug? Have a feature request? Contributions are welcome!

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📝 Learning Resources

### What I Learned Building This

**Skills:** Reusable automation workflows with slash commands
- Package Python scripts as Claude Code skills
- Define custom prompts and interactions
- Maintain state across sessions via config files

**Agents:** Autonomous sub-tasks for parallel execution
- Spawn parallel agents to fetch calendar and emails simultaneously
- Keep main context clean while handling complex operations
- Return structured data for integration

### More About Claude Code

- [Claude Code Documentation](https://claude.com/claude-code)
- [Building Custom Skills Guide](https://docs.anthropic.com/claude/docs/claude-code-skills)
- [Claude API (Tool Use)](https://docs.anthropic.com/claude/docs/tool-use)

---

## 📄 License

MIT License - feel free to use and modify for your own PM workflows!

---

## 🙏 Credits

Built during Week 2 of learning Claude Code by **Shreya Ganguly** (Microsoft PM).

Special thanks to the PM peer group for testing and feedback!

---

## 💡 Tips for PMs

1. **Block focus time immediately** after running `/plan-my-day`
2. **Batch email processing** - don't constantly check, use your flagged emails list
3. **Review carryover dates** - if a task has been carrying over for 3+ days, consider:
   - Breaking it into smaller tasks
   - Delegating it
   - Removing it if it's no longer relevant
4. **End-of-day reflection** - Use the Reflection section in your daily plan to capture learnings

Happy planning! 🚀

---

**Questions?** Open an issue or reach out to the PM community!
