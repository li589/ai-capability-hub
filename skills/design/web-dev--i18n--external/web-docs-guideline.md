## Language Adaptation Rule

**IMPORTANT**: The templates below are STRUCTURAL REFERENCES ONLY. All output MUST match the language in `<user_input>`.

- You MUST translate ALL template headers, descriptions, and example text into the language of `<user_input>`
- For example, if `<user_input>` is in Chinese:
  - `## 1. Product Overview` → `## 1. 产品概述`
  - `[Project overview in 2 lines max]` → `[用最多2行描述项目概述]`
  - Table headers like `| Page Name | Module Name |` → `| 页面名称 | 模块名称 |`
- Do NOT output English templates directly when `<user_input>` uses a different language
- This rule applies to BOTH the PRD Template AND the Technical Architecture Template

---

#### PRD Template

**Constraints:**
- Generate pages and features required for the product to function properly, prioritizing core functionality pages
- If total pages ≤ 3, increase functional complexity and content richness within each page
- Use meaningful document names for better recognition

**Format:**
```markdown
## 1. Product Overview
[Project overview in 2 lines max]
- Brief description of main purposes, problems to solve, target users
- Target or market value of the product

## 2. Core Features

### 2.1 User Roles (if applicable)
[Only include if role distinction is necessary]
| Role | Registration Method | Core Permissions |
|------|---------------------|------------------|
| Normal User | Email registration | Browse and use basic functions |

### 2.2 Feature Module
[List ONLY essential page names with core modules]
1. **Home page**: hero section, navigation, article list
2. **Details page**: article details, user comments

### 2.3 Page Details
| Page Name | Module Name | Feature description |
|-----------|-------------|---------------------|
| Home page | Hero section | Auto-switch images at intervals, etc. |

## 3. Core Process
[Natural language description of main user flows]
[Mermaid flowchart with quoted node labels]

## 4. User Interface Design
### 4.1 Design Style
- Primary and secondary colors
- Button style (3D, rounded, etc.)
- Font and sizes
- Layout style (card-based, top navigation)
- Icon/emoji style suggestions

### 4.2 Page Design Overview
| Page Name | Module Name | UI Elements |
|-----------|-------------|-------------|
| Home page | Hero section | Style, Layout, Colors, Fonts, Animation |

### 4.3 Responsiveness
[Desktop-first, mobile-adaptive, touch optimization]

### 4.4 3D Scene Guidance (if applicable)
- Environment/HDRI and mood
- Lighting setup
- Camera settings and motion
- Composition and focal elements
- Interactions and animations
- Post-processing effects
- Asset sources and performance budgets
```

#### Technical Architecture Template

**Principles:**
- Minimize external services unless explicitly requested
- Prefer React over plain HTML
- For 3D projects: three, @react-three/fiber, @react-three/drei, @react-three/postprocessing

**Format:**
```markdown
## 1. Architecture Design
[Mermaid diagram showing layers: Frontend, Backend (optional), Data, External Services]

## 2. Technology Description
- Frontend: React@18 + tailwindcss@3 + vite
- Initialization Tool: vite-init
- Backend: Express@4 / None
- Database: PostgreSQL / MySQL / SQLite (if applicable), mock data if user preferred

## 3. Route Definitions
| Route | Purpose |
|-------|---------|
| /home | Home page with main content |

## 4. API Definitions (if backend exists)
[TypeScript type definitions, request/response schemas]

## 5. Server Architecture Diagram (if backend exists)
[Mermaid diagram: Controller → Service → Repository → Database]

## 6. Data Model (if applicable)
### 6.1 Data Model Definition
[Mermaid ER diagram]

### 6.2 Data Definition Language
[DDL statements for table creation, indexes, initial data]
```

### Post-skill workflow for doc generation:
- When you are in regular **Agent** Mode, after invoking the **web-dev** skill and the PRD and technical documents have been generated, you MUST use the **NotifyUser** tool to notify the user that the PRD document is ready for review and approval before proceeding with implementation.
- After the user has approved the PRD and technical documents, you MUST NOT block
again on high-level confirmation questions before starting implementation. If you
ask follow-up questions (e.g. via AskUserQuestion) and the user skips or does not
answer them, you MUST proceed using your recommended/default options and continue
execution without asking for additional confirmation.

### Development Phase
Once documents are confirmed (either existing or newly created and approved by user):
- Implement the solution following the PRD and Technical Architecture
- Apply the design guidelines below for exceptional aesthetics
- Follow all technical constraints and architecture decisions from the documents
