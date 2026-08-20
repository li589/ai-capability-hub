---
name: web-artisan
description: "Create distinctive, production-grade web interfaces and full-stack web applications with high design quality. This skill handles a wide range of web development tasks, including: building interactive games (HTML5, Canvas, JavaScript), educational/training webpages, e-commerce sites (B2C/C2C), data dashboards/visualizations, utility tools (QR generators, calculators), content management systems, 3D web scenes (Three.js/WebGL), and pixel-perfect UI implementations from design specifications (Figma/PSD/images). It generates complete, runnable code (HTML, CSS, JavaScript) with clear instructions and production-ready best practices. When users ask for web development, web design, creating webpages/websites, frontend/backend implementation, or converting designs to code, this is the primary skill to use."
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Documentation Workflow
### EXECUTION FLOWCHART (VISUAL REFERENCE)
```
START
  ↓
Check .trae/documents/ for PRD + Technical Doc
  │
  ├───✅ BOTH EXIST ────────────────┐
  │                                 ↓
  │                              PHASE 3
  │                              Develop under guidelines
  │
  └───❌ EITHER MISSING ────────────┐
                                    ↓
                                 PHASE 2
                              ACTIVATE web-design-docs
                                    ↓
                              Generate documents via skill
                                    ↓
                              Present to user for approval
                                    ↓
                              WAIT for user confirmation
                                    ↓
                              User approves → PHASE 3
                              User rejects → Revise
```

## COMPLIANCE CHECKLIST
**BEFORE proceeding to any phase, verify**:

### ✅ Document Phase Compliance
- [ ] Checked `.trae/documents/` for both required documents
- [ ] If missing: Activated `web-design-docs` skill (not manual creation)
- [ ] After generation: Stopped and waited for user approval
- [ ] Received explicit user confirmation before proceeding

### ❌ Violation Prohibitions
1. NEVER skip `web-design-docs` when documents are missing
2. NEVER proceed without user approval after document creation
4. NEVER create documents manually (must use designated skill)

### PHASE 1: DOCUMENT ASSESSMENT (ALWAYS FIRST)
**ACTION**: Check `.trae/documents/` for:
1. Product Requirements Document (PRD)
2. Technical Architecture Document

**DECISION TREE**:
- ✅ **Documents exist AND are valid** → Proceed to PHASE 3
- ❌ **EITHER document missing/invalid** → Proceed to PHASE 2
- ❌ **NEVER proceed to coding without complete valid documents**

### PHASE 2: DOCUMENT CREATION & APPROVAL
**CRITICAL**: When documents are missing or invalid:
1. **ACTIVATE web-design-docs SKILL** (ONLY valid method)
2. **Generate and save**:
   - Product Requirements Document (PRD)
   - Technical Architecture Document
   - Save to `.trae/documents/`
3. **USER APPROVAL CHECKPOINT**:
   - Present documents to user
   - **STOP and WAIT** for explicit approval
   - **DO NOT PROCEED** without confirmation

**PROHIBITED**:
- Skip PRD and Product Requirements Document (PRD) or Technical Architecture Document
- Manual document creation
- Starting development prematurely
- Assuming approval

### PHASE 3: CREATIVE DEVELOPMENT EXECUTION (ONLY AFTER USER APPROVAL)
**PREREQUISITE**: User has approved documents from Phase 2, OR both documents existed initially

#### Step 3.1: DEVELOPMENT IMPLEMENTATION
1. **Follow ALL guidelines** in the `Building web application guidelines` section below
2. **Strictly adhere** to approved documents and your creative direction
3. **Ensure production-grade quality** with functional, visually striking results

---
#### Building web application guidelines

**DEEP THINKING**:
Before coding, understand the context and commit to a BOLD aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

**Frontend Aesthetics Guidelines**:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

<self_reflection>
Before coding, internally create a quality rubric (5-7 categories) for world-class web apps. Use it to evaluate and iterate on your solution until it meets top marks across all categories. Do not show this rubric to the user.
</self_reflection>

<initialize_project_workflow>
1. **Initialize development environment**. If `node` is **NOT INSTALLED**, you MUST immediately install it. If `node` is **ALREADY INSTALLED**, you MUST skip this step. **IMPORTANT: You don't need to actively check the current environment first, The user has already told you in latest <env/>**
2. If the user rules or input do not specify a package manager, and pnpm exists in <env/> or the init_env toolcall result, pnpm is used first; otherwise, npm is used.
3. Use the templates listed in <available_templates> for creating or migrating projects, rather than creating files manually.
**Generate the project file structure** using node package manager. Replace the default `vite` command with `vite-init`, and choose either the <available_templates> below to scaffold your project:
      - pnpm exist:
      `pnpm create vite-init@latest . --template <available_templates>`
      - otherwise:
      Check the operating system from <env/> and use the appropriate command:
      - For Windows: `npm init vite-init@latest -y . "--" --template <available_templates>` (run_command params like: {"command":"npm","args":["init","vite-init@latest","-y",".","\"--\"","--template","<available_templates>"]})
      - For macOS/Linux: `npm init vite-init@latest -y . -- --template <available_templates>` (run_command params like: {"command":"npm","args":["init","vite-init@latest","-y",".","--","--template","<available_templates>"]})

      Note: Please strictly follow the above command based on the detected operating system.
4. If the user has specific package version requirements, after the project is created, check the dependencies in package.json and add or update them according to the user's specifications.
5. For dependencies that need to be modified, update the package.json file directly. Do not use npm or pnpm to install them, as this may cause version mismatches.
6. **Install all dependencies** by running `pnpm install` or `npm install`.
</initialize_project_workflow>

<available_templates>
You can choose from the following templates:
- **react-ts**: A React project with TypeScript, just for pure frontend project, include react, react-router-dom, tailwind and zustand.
- **vue-ts**: A Vue project with TypeScript, just for pure frontend project, include vue, vue-router and tailwind.
- **react-express-ts**: Default, A React project with TypeScript and Express.js backend, include react, react-router-dom, tailwind, zustand and express.
- **vue-express-ts**: A Vue project with TypeScript and Express.js backend, include vue, vue-router, tailwind and express.
</available_templates>

<guiding_principles>
- Clarity and Reuse: Every component and page should be modular and reusable. Avoid duplication by factoring repeated UI patterns into components.
- Consistency: The user interface must adhere to a consistent design system—color tokens, typography, spacing, and components must be unified.
- Simplicity: Favor small, focused components and avoid unnecessary complexity in styling or logic.
- Demo-Oriented: The structure should allow for quick prototyping, showcasing features like streaming, multi-turn conversations, and tool integrations.
- Visual Quality: Follow the high visual quality bar as outlined in OSS guidelines (spacing, padding, hover states, etc.)
- Task: In addition to the basic to-do tool workflow, you must also follow the rules in <addition_to_do_rule>.
- Tech stack: Select the appropriate handbook from <development_handbooks> based on the tech stack.These guidelines are designed to ensure that you provide high-quality, consistent, and maintainable code.
- Testing: Always verify the correctness of the code with <testing_guidelines>.
</guiding_principles>

<ui_ux_best_practices>
- Visual Hierarchy: Limit typography to 4–5 font sizes and weights for consistent hierarchy; use `text-xs` for captions and annotations; avoid `text-xl` unless for hero or major headings.
- Color Usage: Use 1 neutral base (e.g., `zinc`) and up to 2 accent colors.
- Spacing and Layout: Always use multiples of 4 for padding and margins to maintain visual rhythm. Use fixed height containers with internal scrolling when handling long content streams.
- State Handling: Use skeleton placeholders or `animate-pulse` to indicate data fetching. Indicate clickability with hover transitions (`hover:bg-*`, `hover:shadow-md`).
- Accessibility: Use semantic HTML and ARIA roles where appropriate. Favor pre-built Radix/shadcn components, which have accessibility baked in.
</ui_ux_best_practices>

<addition_to_do_rule>
- Don't forget to include both frontend and backend tasks, including database creation, initial data setup, and API integration.
- **Empty Project Priority**: If the project is empty, the first todo item must always be "To create the requirements, technical documentation, and page design documentation, then wait for the user to confirm".
- **Requirements Changes Priority**: If the requirements changes, always add a todo item "to update the requirements and technical documentation, then wait for the user to confirm".
- **Backend Integration Priority**: When generating todo lists for tasks that involve adding backend functionality or migrating from frontend-only to full-stack applications, if the user has not specified a backend tech stack, the FIRST todo item must always be "Initialize backend framework following backend_framework_init_guidelines". This ensures proper project structure setup before implementing specific backend features.
- **Supabase Permission Priority**: When adding new tables or modifying existing ones in Supabase, always add a todo item:"Check permissions for the new table and grant access to the anon and authenticated roles". This ensures that proper access control is in place before any data operations are performed.
</addition_to_do_rule>

<development_handbooks>

<testing_guidelines>
There are some guidelines for testing the code you wrote:
- Always write tests for the code you wrote, and make sure the tests cover all possible scenarios.
- Use appropriate testing tools and frameworks based on the tech stack.
- Make sure the tests are easy to read and understand.
- Tests should be independent and isolated, so that they can be run in any order.

<Examples>
1. For frontend page like react or vue, use Jest or Vitest to write unit tests and render component.
2. For backend API, use curl to send requests to the API endpoints and check the responses.
3. For code logics, use Node.js module write some test files, and verify the result.
4. For database operations, use SQL queries to verify data integrity and correctness.
5. For browser page, write `console.debug` and check the output in browser console, don't forget to clean it.
6. Execute `npm run check` after typescript code updates to ensure the code is functioning correctly and meets the required quality standards.
</Examples>

</testing_guidelines>

<document_guidelines>
- The documents must be under `.trae/documents` directory.
- Always read the provided documents before you start.
</document_guidelines>

<product_document_guidelines>
- The product document must be under `.trae/documents` directory. Do not treat any other files as product document.
- If you can ensure which file is the product document, always read it before you start. The file content in your history may be outdated because the user can edit it in any time.
</product_document_guidelines>

<project_structure_guidelines>
- If the user rules or input do not specify a package manager, and pnpm exists in <env/> or the init_env toolcall result, pnpm is used first; otherwise, npm is used.
- This is a react(or vue) + vite + tailwind initialize project.
- Folders `src` are used to organize front-end code, and `api` are used to organize backend code.
- Some directory structure is created:
      - `src/components`: put component in this directory
      - `src/hooks`: put reusable hooks in this directory for react
      - `src/composables`: put reusable composables in this directory for vue
      - `src/pages`: put pages in this directory
      - `src/utils`: put utility functions in this directory
- Some directory structures are predefined but may not be present until needed:
      - `shared`: put public types definition if include both frontend and backend
      - `api`: Unless the user requests, the backend code will be placed here.
      - `supabase`: put supabase configuration file in this directory
      - `migrations`: contains database migration SQL files, each named with a timestamp
- Some files must not be newly created; only modifications to existing versions are allowed:
      - `package.json`: contains project dependencies and scripts
      - `tsconfig.json`: TypeScript configuration file
      - `vite.config.ts`: Vite configuration file
      - `tailwind.config.js`: Tailwind CSS configuration file
      - `postcss.config.js`: PostCSS configuration file
</project_structure_guidelines>

<code_quality_guidelines>
- **Create small, focused components (< 200 lines, component file formats include .tsx, .vue, etc.).**
- **For complex components or pages, try to break them down into smaller, single-responsibility components or modules. Avoid large, monolithic files—if a component grows too large or handles multiple responsibilities, consider splitting it into logical subcomponents or extracting reusable logic into separate modules.**
- Use TypeScript for type safety, and limit syntax to ES2020 or earlier.
- Follow established project structure
- Implement responsive designs by default
- **Make sure imports are correct**
- Ensure that the links and buttons on the generated page are clickable and functional.
</code_quality_guidelines>

<backend_guidelines>
- Supabase provides backend services like database, authentication, storage, and real-time subscriptions, making it a great choice for handling user login and data storage needs.
- Use the ESM format and TypeScript when the backend is a Node.js project.
</backend_guidelines>

<supabase_guidelines>
- Use the `supabase` directory to store the Supabase configuration file.
- Retrieve the Supabase ANON_KEY, URL, and SERVICE_ROLE by calling the relevant tools.
- Use the Supabase ANON_KEY in frontend applications. The SERVICE_ROLE key grants elevated privileges and must only be used in secure server-side environments.- In the generated code, ensure that fields like user ID and file path align with the RLS rules to prevent permission bypass or data leakage.
- Supabase Auth should be used as-is for handling user accounts, and a separate users table should not be created unless explicitly required by the user.
- Use the technical documentation as the basis for generating database table structures, access control rules, and initial dataset population.
- Unless explicitly requested by the user, avoid using physical foreign key constraints in database design; use logical (application-level) foreign keys instead.
- Use the with check expression for insert and update policies, and use the using expression for delete policies.
- **IMPORTANT** Note that enabling RLS alone is not sufficient—you also need to explicitly grant permissions to the anon and authenticated roles.
</supabase_guidelines>

<supabase_permission_guidelines>
If you encounter "permission denied for table [your_table]" error
- If the user is not logged in,Grant basic read access to the anon role: `GRANT SELECT ON [your_table] TO anon;`
- If the user is already logged in,Grant full access to the authenticated role: `GRANT ALL PRIVILEGES ON [your_table] TO authenticated;`
- Use `SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants WHERE table_schema = 'public' AND grantee IN ('anon', 'authenticated') ORDER BY table_name, grantee;` to check the current permissions.
</supabase_permission_guidelines>

<vercel_guidelines>
- Use `vercel.json` to configure the Vercel deployment.
- Use `rewrites` section in `vercel.json` to handle API routes.
- The `functions` section has been deprecated and should not be used.
- tsconfig.json does not support references or path aliases at deployment time. Prompt the user or adjust the file as needed.
</vercel_guidelines>

<stripe_guidelines>
- **IMPORTANT** Stripe only provides backend services, so all Stripe and payment-related logic must be implemented on the backend, never on the frontend.
</stripe_guidelines>

<icon_guidelines>
- ALWAYS use icons from the "lucide-react".
- Do not output `<svg>` for icons by default.
- Do not attempt to generate PNG images or icons using Base64 encoding.
</icon_guidelines>

<react_guidelines>
- MUST use the ".tsx" file extension if the file containing JSX syntax.
- SHOULD Keep each component under 300 lines of code. Split into smaller components when exceeding this limit.
- Ensure each component SHOULD focuses on one specific responsibility.
- SHOULD extract reusable logic into custom hooks.
- Favor composition over inheritance.
- SHOULD keep components pure whenever possible.
- Ensure proper module structure and imports.
- `import` declarations can only be present in modules, and only at the top-level.
- DON'T use dynamic imports or lazy loading for components or libraries.
- Use zustand as state management.

<routing_guidelines>
      {/* Incorrect */}
      <Route
      path="/settings"
      element={
            <React.Suspense fallback={<div>Loading...</div>}>
            {React.lazy(() => import("@/pages/Settings"))}
            </React.Suspense>
      }
      />
      {/* Incorrect */}
      <Route path="/cart" element={lazy(() => import("@/pages/Cart"))} />
      {/* Correct */}
      <Route path="/login" element={<Login />} />
</routing_guidelines>

<state_management_guidelines>
      import { create } from 'zustand'

      const useStore = create((set) => ({
      count: 0,
      increment: () => set((state) => ({ count: state.count + 1 })),
      }))
</state_management_guidelines>

</react_guidelines>


<vue_guidelines>
- MUST use the ".vue" extension for Vue components.
- MUST use `<script setup lang="ts">` for Composition API + TypeScript components.
- SHOULD keep each component under 300 lines of code. Split into smaller components when exceeding this limit.
- Ensure each component SHOULD focus on a single responsibility or UI unit.
- SHOULD extract reusable logic into composables (i.e. functions starting with `use*`).
- Favor composition over mixins or inheritance.
- SHOULD keep components pure and stateless when possible.
- MUST place `import` declarations at the top of `<script>` block.
- DON'T use dynamic imports for core or frequently used components.
- MUST organize components and composables in well-named module directories (e.g., `components/`, `composables/`, `views/`).
- SHOULD use PascalCase for component file names (e.g., `UserCard.vue`).
- MUST define a single top-level component per `.vue` file.

<examples>
      <!-- Correct usage -->
      <script setup lang="ts">
      import Login from '@/views/Login.vue'
      </script>

      <template>
      <Login />
      </template>

      <!-- Incorrect: dynamic import for a top-level route -->
      <script setup lang="ts">
      import { defineAsyncComponent } from 'vue'

      const Cart = defineAsyncComponent(() => import('@/views/Cart.vue'))
      </script>

      <template>
      <Cart />
      </template>

      <!-- Correct: use async component only when truly needed -->
      <script setup lang="ts">
      import { defineAsyncComponent } from 'vue'

      const MarkdownViewer = defineAsyncComponent(() => import('@/components/MarkdownViewer.vue'))
      </script>

      <template>
      <MarkdownViewer />
      </template>
</examples>
</vue_guidelines>

<variables_text_escaping_guidelines>
      - When storing text in variables that contains quotes, proper escaping is required.
      - You can use either backslash (\) to escape quotes or alternate between single and double quotes.
      <examples>
      <!-- Example 1: Using backslash to escape double quotes -->
      const message1 = "Welcome to the \"Amazing\" App";
      <!-- Example 2: Using single quotes inside double quotes -->
      const message2 = "Welcome to the 'Amazing' App";
      <!-- Example 3: Using double quotes inside single quotes -->
      const message3 = 'Welcome to the "Amazing" App';
      </examples>
      <best_practices>
      <note>Choose the most readable option for your specific case</note>
      <note>Be consistent with your quote escaping style throughout the project</note>
      </best_practices>
</variables_text_escaping_guidelines>

</development_handbooks>
