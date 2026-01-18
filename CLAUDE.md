# CLAUDE.md

## Project Overview
This is an AI/ML experimentation workspace containing multiple projects focused on learning and experimenting with AI agents, machine learning technologies, and related frameworks.

## Workspace Philosophy
This is an **experimentation and learning environment**. Prioritize functionality and rapid iteration over perfection. The goal is to explore, learn, and build working prototypes.

## Code Quality Standards

### Relaxed Approach (Default)
- **Focus on making it work first**, optimize later if needed
- Documentation only when something is non-obvious or complex
- Tests are optional unless critical for debugging
- Experiment freely without overthinking architecture
- Quick prototypes are encouraged

### When to be more careful
- Security-sensitive code (API keys, credentials, authentication)
- Code that will be shared or reused across projects
- Production deployments (if any)

## Primary Technologies

### Python (AI/ML)
- Python is the primary language for AI/ML experimentation
- Common libraries: LangChain, OpenAI SDK, Anthropic SDK, transformers, etc.
- Virtual environments are used (`.venv` directories)
- Follow basic PEP 8 conventions but don't be overly strict

### Agent Frameworks
- Projects may use LangChain, AutoGen, Claude SDK, or custom agent implementations
- Experimentation with agentic workflows and multi-agent systems
- Focus on understanding agent patterns and behaviors

### JavaScript/TypeScript
- Used for web interfaces, Node.js backends, or tooling
- May interact with Python backends or AI services
- Keep it simple and functional

## Project Structure

The workspace contains multiple independent projects:
- `201_p004/` - Agent-related projects
- `Calc/` - Calculator or computation projects
- `claude-code-skills-lab-main/` - Claude Code skills experimentation
- `mcp/` - MCP (Model Context Protocol) projects
- `Python-AI900/` - Azure AI learning projects
- `Qwen_p/` - Qwen model experiments
- `spec-project/` - Specification and planning projects
- `StudyNotes/` - Educational study materials

Each project is independent and may have its own conventions.

## Working Guidelines

### DO:
- Experiment and try new approaches
- Create quick prototypes to test ideas
- Use comments to explain complex logic or non-obvious decisions
- Keep API keys and secrets in `.env` files (never commit them)
- Create virtual environments for Python projects
- Read existing code before making changes

### DON'T:
- Over-engineer solutions for simple problems
- Add unnecessary abstractions or complexity
- Write extensive documentation for experimental code
- Worry about perfect test coverage
- Refactor working code unless explicitly asked
- Commit sensitive credentials or API keys

## Git Practices

- Commit messages should be clear and descriptive
- Group related changes in single commits
- Don't commit `.env` files, API keys, or credentials
- Virtual environment directories (`.venv/`) are gitignored

## Agent-Specific Notes

When working with AI agents or LLM-based code:
- Be mindful of API costs during experimentation
- Log important interactions for debugging
- Handle API errors gracefully (timeouts, rate limits)
- Use environment variables for API keys and configuration

## Communication Style

- Be concise and direct
- Focus on solutions over explanations
- Skip formalities in responses
- Assume technical competence

## When Unsure

If requirements are unclear:
- Make reasonable assumptions for experimental code
- Ask questions only when decisions have significant impact
- Default to simpler approaches over complex ones
- Document assumptions in comments if needed

---

**Remember**: This is a learning and experimentation workspace. The goal is to build, learn, and iterate quickly. Perfect is the enemy of good enough.
