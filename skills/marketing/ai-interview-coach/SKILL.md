---
name: ai-interview-coach
description: AI-powered interview preparation assistant that reads resumes (PDF/Word/MD) or job positions to generate personalized interview questions. Creates a markdown document with 10 interview questions, answer spaces, and reference answers. Use when preparing for job interviews, practicing interview skills, or when the user mentions "面试", "interview practice", "面试题", "简历分析", or asks to generate interview questions.
install_source: official
install_method: download
skill_id: official_Jk8aBEBF
enabled_at: 1787231664978
version: 1.0.0
name_zh: AI 面试教练
---

# AI Interview Coach

Personalized interview preparation assistant that generates targeted questions based on resumes or job positions.

## Quick Start

当用户想要准备面试时，识别以下任意一种输入方式：

### 自然对话方式（推荐）

用户可以用自然的对话方式发起请求：

- **"你好考官，这是我的简历：path/to/resume.pdf"**
- **"你好考官，我是3年经验的前端工程师，帮我准备面试"**
- **"我想面试 AI 算法工程师，生成10道题"**
- **"准备一下 Java 后端面试题"**

### 处理流程

1. 识别用户意图和输入信息（简历文件或职位描述）
2. 读取并分析简历内容（如果提供）
3. **生成10道**针对性的面试题
4. 输出格式化的 markdown 文档（含答题空格和参考答案）

## Input Handling

### Resume Files

Read different formats:

- **Markdown (.md)**: Read as text file directly
- **PDF (.pdf)**: Use PDF tool to extract text content
- **Word (.docx)**: Extract text content (typically contains readable text)

Extract key information:
- Technical skills and tools
- Work experience and projects
- Education background
- Achievements and highlights

### Job Position Input

When user specifies a job role (e.g., "前端工程师", "产品经理"):
- Generate questions based on typical role requirements
- Cover common interview topics for that position
- Include role-specific technical and behavioral questions

## Question Generation Guidelines

Generate 10 questions that cover:

1. **Technical skills** (2-3 questions)
   - Core technologies from resume/role
   - Depth of knowledge assessment

2. **Project experience** (2-3 questions)
   - Past projects from resume
   - Role-specific project scenarios

3. **Problem solving** (2 questions)
   - Technical challenges
   - System design or debugging scenarios

4. **Behavioral/Culture fit** (2-3 questions)
   - Teamwork and collaboration
   - Career motivation
   - Conflict resolution

Question characteristics:
- Be specific and relevant to input
- Vary difficulty (easy, medium, hard)
- Mix question types (knowledge-based, scenario-based, open-ended)

## Output Format

Use this exact structure:

```markdown
# 面试练习题 - [Job Title/Resume Focus]

> Generated on: [Date]
> Source: [Resume filename OR Job position]

---

## 答题说明

1. 请在每道题下方的空白处写下你的答案
2. 完成后对照文档末尾的参考答案进行自我评估
3. 建议限时完成，模拟真实面试场景

---

## 面试题目

### 第1题
[Question text here]

---

（请在此作答）



---

### 第2题
[Question text here]

---

（请在此作答）



---

### 第3题
[Question text here]

---

（请在此作答）



---

### 第4题
[Question text here]

---

（请在此作答）



---

### 第5题
[Question text here]

---

（请在此作答）



---

### 第6题
[Question text here]

---

（请在此作答）



---

### 第7题
[Question text here]

---

（请在此作答）



---

### 第8题
[Question text here]

---

（请在此作答）



---

### 第9题
[Question text here]

---

（请在此作答）



---

### 第10题
[Question text here]

---

（请在此作答）



---

## 参考答案

### 第1题答案

**考察点**: [Key skills/knowledge being tested]

**参考答案**:
[Detailed reference answer with key points]

**答题建议**:
- Key point 1
- Key point 2
- Key point 3

---

### 第2题答案

**考察点**: [Key skills/knowledge being tested]

**参考答案**:
[Detailed reference answer with key points]

**答题建议**:
- Key point 1
- Key point 2
- Key point 3

---

[Continue pattern through question 10]
```

## Workflow

Follow this checklist:

```
Interview Coach Workflow:
- [ ] Step 1: Identify input source (resume file or job position)
- [ ] Step 2: Read and analyze resume content (if applicable)
- [ ] Step 3: Generate 10 targeted questions
- [ ] Step 4: Create formatted markdown document
- [ ] Step 5: Provide reference answers
- [ ] Step 6: Present final document to user
```

**Step 1: Identify Input**
- Ask: "请提供简历文件路径，或告诉我你想面试什么职位？"
- Accept: PDF, Word, MD file paths OR job position names

**Step 2: Read Resume**
- Use appropriate tool based on file extension
- Extract: skills, experience, projects, achievements

**Step 3: Generate Questions**
- Create 10 questions following the guidelines above
- Ensure relevance to input content

**Step 4: Format Output**
- Use the exact template structure provided
- Include all 10 questions with 3-line answer spaces
- Add reference answers section

**Step 5: Deliver**
- Present the complete markdown document
- Offer to save to a file if desired

## Example Usage

For detailed examples, see [examples.md](examples.md).

## Tips for Best Results

1. **Resume quality matters**: More detailed resumes yield more personalized questions
2. **Be specific about job role**: Specific positions ("高级前端工程师") produce better questions than vague ones ("程序员")
3. **Use the document for practice**: Print or save the output for mock interview sessions
4. **Self-evaluation**: Compare your answers with reference answers critically
