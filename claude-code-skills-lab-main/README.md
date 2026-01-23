# Hands-on Skills

A collection of hands-on skills for students to explore and practice when learning the Skills concept in Claude Code. These examples accompany **Lesson 04 of Chapter 5** in the AI Native Development book.

**Reading Material:** [Claude Code Features and Workflows](https://ai-native.panaversity.org/docs/AI-Tool-Landscape/claude-code-features-and-workflows)

## Structure

All skills are located in `.claude/skills/` - the standard location for Claude Code skills.

```
.claude/skills/
├── SKILLS-INDEX.md          ← Full skill library documentation
├── [skill-name]/
│   ├── SKILL.md             ← Frontmatter + instructions
│   ├── scripts/
│   │   └── verify.py        ← Verification script
│   └── references/          ← Optional deep-dive docs
```

## Skills (45 total)

See `.claude/skills/SKILLS-INDEX.md` for the complete categorized skill library with triggers and key values.

### Featured Skills

| Skill | Purpose |
|-------|---------|
| **browsing-with-playwright** | Browser automation using Playwright MCP |
| **building-mcp-servers** | Create MCP servers with FastMCP or TypeScript SDK |
| **building-nextjs-apps** | Next.js 16 patterns and breaking changes |
| **containerizing-applications** | Docker, docker-compose, Helm charts with 15+ gotchas |
| **context7-efficient** | Token-efficient library documentation fetcher |
| **deploying-cloud-k8s** | Deploy to AKS/GKE/DOKS with CI/CD pipelines |
| **fastapi-builder** | Build FastAPI from Hello World to production |
| **skill-creator** | Guide for creating effective Claude Code skills |
| **systematic-debugging** | 4-phase debugging methodology |
| **working-with-documents** | Word, PDF, and PowerPoint manipulation |
| **working-with-spreadsheets** | Excel with formulas and financial modeling |

### All Skill Categories

- **MCP-Backed**: browsing-with-playwright, fetching-library-docs, researching-with-deepwiki
- **Infrastructure**: containerizing-applications, operating-k8s-local, deploying-cloud-k8s, deploying-kafka-k8s, deploying-postgres-k8s
- **Application**: building-nextjs-apps, fastapi-builder, configuring-better-auth, building-rag-systems, scaffolding-openai-agents
- **UI/Frontend**: styling-with-shadcn, building-chat-interfaces, building-chat-widgets, streaming-llm-responses
- **Development**: systematic-debugging, operating-production-services, evaluation
- **Documents**: working-with-spreadsheets, working-with-documents, docx, pdf, pptx, xlsx
- **Context Engineering**: context-fundamentals, context-optimization, context-degradation, memory-systems, multi-agent-patterns, tool-design
- **Meta**: creating-skills, skill-creator, skill-validator, installing-skill-tracker
