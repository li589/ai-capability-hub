---
name: web-design-docs
description: Complete guide for building React frontends with PRD + Technical Architecture templates. Covers 3D scenes, routing, data models, and responsive design.
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
- Supabase handles auth, database, and storage for most backend needs
- Prioritize React + Supabase client SDK; only add backend for server-side needs (e.g., LLM API calls)
- Minimize external services unless explicitly requested
- Prefer React over plain HTML
- For 3D projects: three, @react-three/fiber, @react-three/drei, @react-three/postprocessing

**Supabase Guidelines:**
- Don't use Supabase in both frontend and backend; if backend exists, use it only there
- Delegate auth to Supabase by default
- Use official Supabase SDK only (not pg or knex)
- Avoid physical foreign keys; use logical (application-level) foreign keys
- Grant `SELECT` to `anon` role, `ALL PRIVILEGES` to `authenticated` role
- Use `with check` for insert/update policies, `using` for delete policies

**Format:**
```markdown
## 1. Architecture Design
[Mermaid diagram showing layers: Frontend, Backend (optional), Data, External Services]

## 2. Technology Description
- Frontend: React@18 + tailwindcss@3 + vite
- Initialization Tool: vite-init
- Backend: Supabase / Express@4 / None
- Database: Supabase (PostgreSQL) (if applicable)

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
- After invoking the **web-artisan** skill followed by the **web-design-docs** skill and the PRD document has been generated, you MUST use the **NotifyUser** tool to notify the user that the PRD document is ready for review and approval before proceeding with implementation.

### Development Phase
Once documents are confirmed (either existing or newly created and approved by user):
- Implement the solution following the PRD and Technical Architecture
- Apply the design guidelines below for exceptional aesthetics
- Follow all technical constraints and architecture decisions from the documents
