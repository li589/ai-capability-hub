---
name: article-to-blog
description: Converts a GitHub project repository or an ArXiv research paper into an engaging, illustrated blog post. Use this skill when the user asks to summarize, explain, or write a blog post about a specific GitHub repo or ArXiv article.
install_source: official
install_method: download
skill_id: official_fMrkHL7d
enabled_at: 1787232878115
version: 1.0.0
name_zh: 文章转博客
---

# Article to Blog Skill

This skill guides you through converting complex technical content (GitHub repositories or ArXiv papers) into accessible, visually appealing blog posts.

## 1. Information Gathering

When triggered, first read and understand the source material:

**For GitHub Repositories:**
- Read the `README.md`
- Inspect the file structure and read key source files or documentation to understand the architecture and features.

**For ArXiv Papers:**
- Read the paper's Abstract, Introduction, Methodology, and Conclusion.
- Extract the core problem, proposed solution, and key results/metrics.

## 2. Drafting the Blog Post

Write the blog post in **Simplified Chinese (简体中文)**. 
Format the text in Markdown following the structure in `assets/blog_template.md`.

**CRITICAL TONE REQUIREMENTS ("活人感" & "去AI味"):**
- **NO AI Clichés:** Absolutely avoid typical LLM transitional phrases such as "在这个快速发展的时代", "正如我们所见", "总之", "让我们深入探讨", "不可否认的是", "得益于", "令人振奋的是", "总而言之".
- **Human-like Voice:** Write like a real developer excitedly sharing a cool new tool or paper with a colleague over coffee. Use a natural, conversational, and slightly opinionated tone. 
- **Direct & Punchy:** Use short paragraphs, varying sentence lengths, and sharp insights. Cut out the fluff. Use everyday IT colloquialisms appropriately (e.g., "填坑", "踩坑", "神器", "硬核", "惊艳我的是", "简单粗暴").
- **Show, Don't Just Tell:** Use concrete examples instead of abstract generalizations. Express genuine curiosity or mild skepticism where appropriate ("说实话，一开始我以为它只是个噱头，直到我看了源码...").

## 3. Illustrations

An illustrated blog post must contain visual elements to break up the text:

1. **Cover Image**: If you have an image generation tool, create an attractive, stylized cover image relevant to the topic. Include it at the top of the post. If you don't have this tool, just suggest a detailed image prompt in a blockquote.
2. **Mermaid Diagrams**: Wherever beneficial (especially in the "Core Concept" or "Methodology" sections), use Mermaid.js diagrams to visually explain architectures, workflows, or comparisons. Create well-structured `mermaid` codeblocks.

## 4. Final Review
Before outputting, verify that:
- The text feels like it was written by a human technical blogger on platforms like Juejin (掘金), Zhihu (知乎), or WeChat Public Accounts.
- No boilerplate AI conclusions exist.
- At least one Mermaid diagram is present.
- A cover image or image generation prompt is included.
