# CLAUDE.md

## Project Overview
This is an AI/ML experimentation workspace containing multiple projects focused on learning and experimenting with AI agents, machine learning technologies, and related frameworks.

## Workspace Philosophy
This is an **experimentation and learning environment**. Prioritize functionality and rapid iteration over perfection. The goal is to explore, learn, and build working prototypes.

## Claude Code Best Practices

### 1. Workflow Orchestration
- Break complex tasks into smaller, manageable steps
- Use TaskCreate to track multi-step processes
- Use TaskUpdate to mark progress (in_progress, completed)
- Create dependencies between tasks when needed
- Prefer parallel execution for independent tasks

### 2. Subagent Strategy
- Use Task tool with subagent_type for complex, multi-step tasks
- Use Explore agent for codebase exploration and research
- Use Bash agent for terminal operations and git commands
- Use general-purpose agent for complex code modifications
- Use Plan agent for designing implementation approaches

### 3. Self-Improvement Loop
- After completing tasks, review what worked well and what didn't
- Update this CLAUDE.md file with new patterns that prove effective
- Create skills for repetitive tasks
- Document successful patterns for future reference

### 4. Verification Before Done
- Run `kubectl get pods` after deployments to verify they're running
- Check logs with `kubectl logs` for any errors
- Test services with `kubectl port-forward` or external access
- Validate configurations before committing
- Use `kubectl describe` to get detailed resource information

### 5. Autonomous Bug Fixing
- Use `kubectl describe pod <name>` to understand issues
- Check events with `kubectl get events` for recent problems
- Use `kubectl logs <pod-name> --previous` for crashed containers
- Leverage `kubectl debug` for troubleshooting running containers
- Create targeted fixes rather than broad changes

### 6. Core Principles
- **Start Simple**: Begin with minimal viable solutions
- **Iterate Fast**: Make small, frequent improvements
- **Verify Continuously**: Check status after each major change
- **Document Decisions**: Add comments and documentation for non-obvious choices
- **Preserve Working Code**: Don't fix what isn't broken

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

### Kubernetes
- Use the kubernetes-deployer skill for deployments
- Follow standard Kubernetes resource definitions
- Include health checks in all production deployments
- Use proper resource requests and limits
- Implement proper service discovery patterns

### JavaScript/TypeScript
- Used for web interfaces, Node.js backends, or tooling
- May interact with Python backends or AI services
- Keep it simple and functional

## Working Guidelines

### DO:
- Experiment and try new approaches
- Create quick prototypes to test ideas
- Use comments to explain complex logic or non-obvious decisions
- Keep API keys and secrets in `.env` files (never commit them)
- Create virtual environments for Python projects
- Read existing code before making changes
- Use the Task tools to track complex multi-step workflows
- Leverage skills for domain-specific operations
- Create proper resource quotas and limits in Kubernetes
- Implement monitoring and health checks
- Document non-obvious architectural decisions

### DON'T:
- Over-engineer solutions for simple problems
- Add unnecessary abstractions or complexity
- Write extensive documentation for experimental code
- Worry about perfect test coverage
- Refactor working code unless explicitly asked
- Commit sensitive credentials or API keys
- Skip verification after major changes

## Git Practices

- Commit messages should be clear and descriptive
- Group related changes in single commits
- Don't commit `.env` files, API keys, or credentials
- Virtual environment directories (`.venv/`) are gitignored
- Use descriptive branch names for feature work

## Agent-Specific Notes

When working with AI agents or LLM-based code:
- Be mindful of API costs during experimentation
- Log important interactions for debugging
- Handle API errors gracefully (timeouts, rate limits)
- Use environment variables for API keys and configuration

## Kubernetes-Specific Guidelines

### For AI/ML Workloads:
- Use resource quotas to prevent runaway resource consumption
- Implement proper node affinity for specialized hardware (GPU/TPU)
- Include startup, liveness, and readiness probes in all deployments
- Use persistent volumes for model storage and training data
- Configure proper tolerations for GPU nodes

### Deployment Patterns:
- Use Deployments instead of raw Pods for production workloads
- Implement proper service discovery between components
- Use ConfigMaps for configuration, Secrets for sensitive data
- Set up proper monitoring and logging
- Implement proper security contexts

## When Unsure

If requirements are unclear:
- Make reasonable assumptions for experimental code
- Ask questions only when decisions have significant impact
- Default to simpler approaches over complex ones
- Document assumptions in comments if needed
- Use the Task system to break down unclear requirements

---

**Remember**: This is a learning and experimentation workspace. The goal is to build, learn, and iterate quickly. Perfect is the enemy of good enough. This file itself is a compounding system - every improvement to this CLAUDE.md helps future work be more efficient and effective.