# GitHub Setup Guide

Follow these steps to publish your PM Daily Planning Skills to GitHub and share with your peers.

---

## Step 1: Initialize Git Repository

Open a terminal in your repository folder:

```bash
cd C:\Users\shrganguly\Documents\pm-daily-planning-skills
git init
```

---

## Step 2: Create Initial Commit

```bash
# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: PM Daily Planning Skills for Claude Code

- /plan-my-day: Auto-fetch emails/calendar and generate daily plans
- /add-task: Quick task capture with natural language dates
- /end-of-day-cleanup: Auto-move uncompleted tasks to backlog
- Integrated Outlook + Obsidian workflow
- Preserves original carryover dates for task aging visibility"
```

---

## Step 3: Create GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **+** icon in top right → **New repository**
3. Fill in details:
   - **Repository name:** `pm-daily-planning-skills`
   - **Description:** `Lean task management system for PMs using Claude Code, Outlook, and Obsidian`
   - **Public** ✓ (so peers can access)
   - **DO NOT** initialize with README (we already have one)
4. Click **Create repository**

---

## Step 4: Push to GitHub

GitHub will show you commands. Use these:

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/pm-daily-planning-skills.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Replace `YOUR_USERNAME`** with your actual GitHub username!

---

## Step 5: Verify & Share

1. Go to your repository: `https://github.com/YOUR_USERNAME/pm-daily-planning-skills`
2. Verify README.md displays correctly
3. Share the link with your PM peers!

---

## Step 6: Update README with Correct GitHub URL

After creating the repository, update the clone command in README.md:

1. Edit `README.md`
2. Find line: `git clone https://github.com/YOUR_USERNAME/pm-daily-planning-skills.git`
3. Replace `YOUR_USERNAME` with your actual GitHub username
4. Commit and push:

```bash
git add README.md
git commit -m "Update README with correct GitHub URL"
git push
```

---

## Future Updates

When you make improvements to the skills:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: XYZ"

# Push to GitHub
git push
```

---

## Making it Look Professional

### Add Topics (Tags)

On your GitHub repository page:
1. Click the ⚙️ gear icon next to "About"
2. Add topics: `claude-code`, `product-management`, `productivity`, `automation`, `outlook`, `obsidian`
3. Click **Save changes**

### Add a Screenshot

1. Take a screenshot of a sample daily plan
2. Save to `docs/screenshots/daily-plan-example.png`
3. Add to README (top section):

```markdown
![Daily Plan Example](docs/screenshots/daily-plan-example.png)
```

4. Commit and push:

```bash
git add docs/screenshots/daily-plan-example.png README.md
git commit -m "Add daily plan screenshot"
git push
```

---

## Sharing with Your Peer PMs

### Option 1: Direct Link
Share: `https://github.com/YOUR_USERNAME/pm-daily-planning-skills`

### Option 2: LinkedIn/Teams Post
```
🚀 Excited to share my Week 2 Claude Code project!

Built a lean task management system for PMs:
✅ Auto-fetches Outlook emails & calendar
✅ Generates structured daily plans in Obsidian
✅ Intelligent task carryover with age tracking

Check it out: [GitHub Link]

#ProductManagement #Automation #ClaudeCode
```

### Option 3: Create a Release

1. Go to your repo → **Releases** → **Create a new release**
2. Tag version: `v1.0.0`
3. Release title: `PM Daily Planning Skills v1.0 - Initial Release`
4. Description: Brief summary + what's included
5. Click **Publish release**

---

## Troubleshooting

### Git not installed?
Download from: https://git-scm.com/downloads

### Authentication issues?
GitHub now requires personal access tokens:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when pushing

Or set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

---

Good luck! 🎉
