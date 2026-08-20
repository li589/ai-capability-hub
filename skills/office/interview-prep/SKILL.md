---
name: interview-prep
description: Research a company and role, then generate a professional PowerPoint presentation for interview preparation. Optionally include a resume/CV for personalized talking points and experience highlights.
trigger_phrases:
  - interview prep
  - create interview presentation
  - prepare for interview
  - research company for interview
  - make interview slides
  - interview powerpoint
  - job interview preparation
model: opus
allowed_tools:
  - Bash(python:*)
  - Bash(python3:*)
  - Read
  - Write
  - Edit
install_source: official
install_method: download
skill_id: official_CEgHlImH
enabled_at: 1787230802672
version: 1.0.0
name_zh: 面试准备
---

# Interview Preparation PowerPoint Generator

## Overview

This Skill researches a company and specific role using AI, then generates a professional 10-20 slide PowerPoint presentation to help prepare for and present during an interview. Optionally accepts a resume/CV (PDF, Word, or text) for personalized content.

## Deployment

**Production API**: https://interview-prep-pptx-production.up.railway.app
**Frontend**: https://interview-prep-pptx-production.up.railway.app/app

The API is deployed on Railway with automatic deploys from the `interview-prep-pptx` directory.

## When to use

Use this Skill when the user asks to:
- Prepare for an interview at a company
- Research a company and role for interview
- Create interview prep slides or PowerPoint
- Generate interview presentation
- Build interview preparation materials
- Help with job interview preparation

## Decision Tree

```
User Request → Check Intent
│
├─ "Research [company] for [role]" → Run interview_research.py
│   └─ With resume? → Add --resume flag
│   └─ Want images? → Add --generate-images flag
│
├─ "Create/Generate presentation" → Run pptx_generator.py
│   └─ Check for research JSON in .tmp/
│
├─ "Edit slide..." → Run pptx_editor.py
│   └─ Text edit → --action edit-text
│   └─ Image change → --action regenerate-image or replace-image
│   └─ Add slide → --action add-slide
│
├─ "Show/List slides" → Run pptx_editor.py --action list
│
└─ "Add [experience] slide with my image" → Run pptx_editor.py --action add-slide --new-image
```

## Required Inputs

1. **Company Name** (required): The company to research
2. **Role/Position** (required): The specific job title being interviewed for

## Optional Inputs

3. **Resume/CV** (optional): Path to a PDF, DOCX, or TXT file with work experience
4. **Theme** (optional): "modern" (default), "professional", or "minimal"
5. **Generate Images** (optional): Create AI visuals for experience highlights ($0.07/image)

## Instructions

### Option A: Basic Research (No Resume)

```bash
# Step 1: Research company and role
source .env && python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}"

# Step 2: Generate PowerPoint
python execution/pptx_generator.py --input .tmp/interview_research_{company_slug}.json

# Step 3: Open the presentation
open .tmp/interview_prep_{company_slug}.pptx
```

### Option B: Personalized (With Resume)

```bash
# Step 1: Research with resume parsing
source .env && python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}" --resume "/path/to/resume.pdf"

# Step 2: Generate PowerPoint with experience highlights
python execution/pptx_generator.py --input .tmp/interview_research_{company_slug}.json

# Step 3: Open the presentation
open .tmp/interview_prep_{company_slug}.pptx
```

### Option C: Full Experience (Resume + Images)

```bash
# Step 1: Research with resume and generate images
source .env && python execution/interview_research.py --company "{COMPANY}" --role "{ROLE}" --resume "/path/to/resume.pdf" --generate-images

# Step 2: Generate PowerPoint
python execution/pptx_generator.py --input .tmp/interview_research_{company_slug}.json

# Step 3: Open the presentation
open .tmp/interview_prep_{company_slug}.pptx
```

## Important Notes

- **Company Slug**: Convert company name to lowercase with underscores (e.g., "Apple Inc" → "apple_inc")
- **Source .env**: Always source .env before running interview_research.py to load the Anthropic API key
- **Resume Formats**: Supports PDF (.pdf), Word (.docx, .doc), and text (.txt, .md)
- **Themes**: "modern" (dark blue/coral), "professional" (navy/orange), "minimal" (slate/green)

## Slide Structure

**Core Slides (Always Included):**
1. Title Slide - Company name, role, date
2. Agenda - Overview of presentation
3. Company Overview - Industry, mission, products
4. Recent News - Latest developments
5. Company Culture - Values, work environment
6. Role Analysis - Responsibilities, department
7. Skills & Metrics - Required skills, success measures
8. Interview Questions 1 - Common questions with strategies
9. Interview Questions 2 - More questions
10. Questions to Ask - Smart questions for interviewer
11. Competitive Landscape - Competitors, industry trends
12. Talking Points - Key messages to communicate

**Personalized Slides (When Resume Provided):**
13. Your Relevant Experience - Section divider
14-18. Experience Highlights - Individual slides for top 5 relevant experiences

**Closing Slides:**
- Preparation Checklist - Action items before interview
- Closing - Motivational ending

## Error Handling

**Missing dependencies:**
```bash
pip install anthropic python-pptx PyPDF2 python-docx
```

**API key not set:**
Ensure `ANTHROPIC_API_KEY` is set in `.env` file and source it before running.

**Resume parsing fails:**
Check that the file exists and is a supported format (PDF, DOCX, TXT).

## Cost

- Research: ~$0.02-0.05 per run (Claude API)
- PowerPoint: FREE (local generation)
- Images: ~$0.07/image if using --generate-images flag (Grok API)

## Example Usage

**User asks:** "Help me prepare for a Product Manager interview at Stripe"

**Your response:**
1. Ask if they have a resume to include
2. Run interview_research.py with their inputs
3. Run pptx_generator.py to create slides
4. Open the PowerPoint and confirm success
5. Tell them the file location

**User asks:** "Create interview prep for Google Software Engineer using my resume at ~/resume.pdf"

**Your response:**
1. Run with --resume flag pointing to their file
2. Generate personalized PowerPoint
3. Confirm the presentation includes their experience highlights

## Session-Based Editing

After generating a presentation, a **session is automatically created**. This allows you to make iterative edits without specifying file paths each time.

### Check Current Session
```bash
python execution/session_manager.py --status
```

### List Recent Sessions
```bash
python execution/session_manager.py --list
```

### Get Current PowerPoint File
```bash
python execution/session_manager.py --current
```

The session tracks:
- Current presentation file (.pptx)
- Original research data (.json)
- Resume (if provided)
- All edits made during the session
- Slide count

**IMPORTANT**: When the user asks to edit "the presentation" or "the slides" or "my PowerPoint", use the session to find the current file:
1. Run `python execution/session_manager.py --current` to get the filename
2. Use that filename in subsequent edit commands

## Interactive Slide Editing

After generating a presentation, users can make iterative edits through natural language commands.

### List Slides
```bash
# Get current file first
PPTX=$(python execution/session_manager.py --current)
python execution/pptx_editor.py --input .tmp/$PPTX --action list
```

Or with explicit file:
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_{company_slug}.pptx --action list
```

### Edit Text on a Slide
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_{company_slug}.pptx --action edit-text --slide {num} --find "old text" --replace "new text"
```

### Regenerate Image with AI ($0.07)
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_{company_slug}.pptx --action regenerate-image --slide {num} --prompt "New image description" --open
```

### Add New Slide with User's Image (FREE)
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_{company_slug}.pptx --action add-slide \
  --title "Experience Title" \
  --description "Description of the experience" \
  --relevance "How it relates to the role" \
  --new-image /path/to/user/image.jpg \
  --after-slide {num} --open
```

### Add New Slide with AI Image ($0.07)
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_{company_slug}.pptx --action add-slide \
  --title "Experience Title" \
  --description "Description of the experience" \
  --relevance "How it relates to the role" \
  --prompt "AI image prompt description" \
  --after-slide {num} --open
```

## Cost Summary

| Action | Cost |
|--------|------|
| Research (Claude API) | ~$0.02-0.05 |
| PowerPoint generation | FREE |
| Text edits | FREE |
| Replace image with local file | FREE |
| Add slide with user's image | FREE |
| AI image regeneration | $0.07/image |
| Add slide with AI image | $0.07/image |

## File Structure

```
interview-prep-pptx/
├── src/
│   ├── interview_research.py    # AI research script
│   ├── pptx_generator.py        # PowerPoint generation
│   ├── pptx_editor.py           # Interactive editing
│   ├── session_manager.py       # Session tracking
│   ├── interview_prep_api.py    # FastAPI REST API
│   └── grok_image_gen.py        # AI image generation
├── frontend/
│   └── index.html               # Web interface
├── requirements.txt
├── railway.json                 # Railway deployment config
├── Procfile
└── SKILL.md                     # This file
```

## Template Mode - Continue From Existing Presentation

When the user has an existing PowerPoint they want to continue editing (e.g., from a previous session), use the template workflow.

### Option D: Load Existing Template

Use this when the user says:
- "I have a presentation from last night..."
- "Continue editing my existing PowerPoint..."
- "Use this file as a starting point..."
- "Edit my presentation at .tmp/..."

```bash
# Step 1: List available templates
python execution/template_manager.py --list

# Step 2: Load template and create editing session
python execution/template_manager.py --load .tmp/interview_prep_company.pptx --create-session

# Step 3: List slides in the template
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action list

# Step 4: Make edits using pptx_editor.py
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action edit-text --slide 3 --find "old" --replace "new"

# Step 5: Add images to existing slides
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 14 --new-image .tmp/exp_img_1.jpeg --position left --width 4.5
```

### Option E: Copy Template and Regenerate with New Theme

When user wants same content but different styling:

```bash
# Step 1: Copy existing template
python execution/template_manager.py --load .tmp/interview_prep_company.pptx --copy-to .tmp/interview_prep_company_v2.pptx

# Step 2: Extract company/role info
python execution/template_manager.py --load .tmp/interview_prep_company.pptx --extract-info

# Step 3: Regenerate with new theme (if research JSON exists)
python execution/pptx_generator.py --input .tmp/interview_research_company.json --theme professional
```

### Template Manager Commands

| Command | Description |
|---------|-------------|
| `--list` | List all available templates in .tmp/ |
| `--load FILE` | Load and inspect a template |
| `--load FILE --extract-info` | Extract company/role from template |
| `--load FILE --create-session` | Create editing session from template |
| `--load FILE --copy-to NEW` | Copy template to new file |

### Working with Images from Previous Sessions

If the user has images from a previous session (e.g., `exp_img_1.jpeg` through `exp_img_5.jpeg`), add them to experience slides:

```bash
# Add images to slides 14-18 (experience slides)
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 14 --new-image .tmp/exp_img_1.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 15 --new-image .tmp/exp_img_2.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 16 --new-image .tmp/exp_img_3.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 17 --new-image .tmp/exp_img_4.jpeg --position left --width 4.5
python execution/pptx_editor.py --input .tmp/interview_prep_company.pptx --action add-image --slide 18 --new-image .tmp/exp_img_5.jpeg --position left --width 4.5 --open
```

## Decision Tree (Updated)

```
User Request → Check Intent
│
├─ "Research [company] for [role]" → Run interview_research.py
│   └─ With resume? → Add --resume flag
│   └─ Want images? → Add --generate-images flag
│
├─ "Create/Generate presentation" → Run pptx_generator.py
│   └─ Check for research JSON in .tmp/
│
├─ "Continue editing my presentation from..." → Template Mode
│   └─ Load template with template_manager.py
│   └─ Create session with --create-session
│   └─ Use pptx_editor.py for edits
│
├─ "Use this existing PowerPoint..." → Template Mode
│   └─ Copy template if needed
│   └─ Add images from .tmp/ if available
│
├─ "Edit slide..." → Run pptx_editor.py
│   └─ Text edit → --action edit-text
│   └─ Add image → --action add-image
│   └─ Image change → --action regenerate-image or replace-image
│   └─ Add slide → --action add-slide
│
├─ "Show/List slides" → Run pptx_editor.py --action list
│
└─ "Add [experience] slide with my image" → Run pptx_editor.py --action add-slide --new-image
```

## Live Interactive Editing Mode

For real-time editing while viewing the PowerPoint open on screen. User can describe changes and watch them happen.

### When to Use Live Mode

Use when user says:
- "I have the presentation open, change slide 3..."
- "While I'm looking at it, update the title..."
- "Let me watch you make the changes..."
- "I want to edit this interactively..."

### Starting Live Session

```bash
# Start and open the file
python execution/live_editor.py --start .tmp/interview_prep_company.pptx --open
```

### Live Edit Commands

```bash
# Edit text (auto-refreshes PowerPoint)
python execution/live_editor.py --edit-text --slide 3 --find "old" --replace "new"

# Add image
python execution/live_editor.py --add-image --slide 14 --image .tmp/exp_img_1.jpeg

# List slides
python execution/live_editor.py --list

# Refresh PowerPoint
python execution/live_editor.py --refresh

# Check status
python execution/live_editor.py --status

# Revert all changes
python execution/live_editor.py --revert

# End session
python execution/live_editor.py --end
```

### Decision Tree (Live Mode)

```
User Request → Check if presentation is open
│
├─ "I have it open, change..." → Live Mode
│   └─ Start session if not active: --start FILE
│   └─ Make edit: --edit-text or --add-image
│   └─ Auto-refresh shows changes
│
├─ "Watch me edit..." → Live Mode
│   └─ --start FILE --open
│   └─ Proceed with edits
│
└─ "Revert my changes" → --revert
```

## Additional Resources

- Directive: `directives/interview_prep.md`
- Interactive editing guide: `directives/pptx_interactive_edit.md`
- Template manager: `execution/template_manager.py`
- Live editor: `execution/live_editor.py`
- Project symlink: `projects/interview-prep` → `interview-prep-pptx`
