# Master Skills Guide

## Table of Contents
1. [What are Skills?](#what-are-skills)
2. [Skill Anatomy](#skill-anatomy)
3. [Creating Skills](#creating-skills)
4. [Best Practices](#best-practices)
5. [Skill Template](#skill-template)
6. [Meta-Skill: Skills Creator](#meta-skill-skills-creator)
7. [Examples](#examples)

---

## What are Skills?

Skills are custom prompt-based tools that extend Claude Code's capabilities for specific tasks or workflows. They are:

- **Reusable**: Once created, can be invoked repeatedly
- **Composable**: Can chain together to form workflows
- **Project-specific**: Tailored to your project's needs
- **Documented**: Self-contained with instructions and metadata

### When to Create a skill

Create a skill when you have:
- A repetitive task that follows a consistent pattern
- A complex workflow that requires multiple steps
- Domain-specific knowledge that needs to be applied consistently
- A task that would benefit from standardized output format
- A process that should chain with other skills

### When NOT to Create a Skill

Don't create a skill for:
- One-off tasks
- Simple operations covered by built-in tools
- Tasks that vary significantly each time
- Overly generic operations

---

## Skill Anatomy

Every skill consists of two main parts:

### 1. YAML Frontmatter (Metadata)

Defines the skill's configuration and behavior:

```yaml
---
name: skill-name
description: Brief description of what the skill does
trigger:
  - keyword: word
  - pattern: "regex pattern"
arguments:
  - name: arg_name
    description: What this argument does
    required: true/false
    default: value
inputs:
  type: file_type
  source: where input comes from
outputs:
  type: output_type
  location: where to save output
  format: structure of output
tools:
  - ToolName1
  - ToolName2
chain:
  upstream:
    - skill-that-feeds-this
  downstream:
    - skill-that-uses-this-output
tags:
  - category1
  - category2
---
```

### 2. Markdown Instructions

Detailed instructions for Claude to follow when executing the skill.

---

## Creating Skills

### Step 1: Define the Purpose

Ask yourself:
- What problem does this skill solve?
- What inputs does it need?
- What outputs should it produce?
- How will it be triggered?

### Step 2: Map the Workflow

Break down the task into phases:
1. Input analysis/validation
2. Processing steps
3. Output generation
4. Quality checks

### Step 3: Identify Required Tools

List Claude Code tools needed:
- Read, Write, Edit (file operations)
- Grep, Glob (search/find)
- Bash (command execution)
- WebSearch, WebFetch (research)
- Task (spawn agents)

### Step 4: Design the Output

Define:
- Output format (markdown, JSON, code, etc.)
- File naming conventions
- Directory structure
- Metadata to include

### Step 5: Write Instructions

Create clear, step-by-step instructions:
- Use numbered phases
- Include decision trees for conditional logic
- Specify quality standards
- Provide examples

### Step 6: Test and Refine

- Test with various inputs
- Refine instructions based on results
- Add edge case handling
- Document limitations

---

## Best Practices

### Naming Conventions

- **Skill names**: lowercase-with-hyphens
- **File names**: match skill name (e.g., `skill-name.md`)
- **Arguments**: snake_case
- **Tags**: lowercase, specific

### Writing Instructions

**DO:**
- Use clear, imperative language
- Break complex tasks into phases
- Include quality standards
- Provide concrete examples
- Specify tools to use
- Define success criteria

**DON'T:**
- Be vague or ambiguous
- Assume context
- Skip error handling
- Forget edge cases
- Overcomplicate simple tasks

### Trigger Patterns

**Keywords**: Simple words that suggest the skill
```yaml
trigger:
  - keyword: flashcards
  - keyword: review cards
```

**Patterns**: Regex patterns for specific phrases
```yaml
trigger:
  - pattern: "create .* from"
  - pattern: "generate .* for"
```

### Chaining Skills

Skills can feed into each other:

```yaml
chain:
  upstream:
    - data-collector  # Provides input to this skill
  downstream:
    - report-generator  # Uses this skill's output
  metadata_pass:
    - source_file
    - timestamp
```

### Output Organization

Use consistent directory structures:
```
project/
├── .claude/
│   └── skills/
│       ├── skill-one.md
│       └── skill-two.md
└── outputs/
    ├── category1/
    └── category2/
```

---

## Skill Template

Use this as a starting point for new skills:

```markdown
---
name: your-skill-name
description: One-line description of what this skill does
trigger:
  - keyword: primary-trigger
  - keyword: secondary-trigger
  - pattern: "pattern-based trigger"
arguments:
  - name: required_arg
    description: What this argument represents
    required: true
  - name: optional_arg
    description: Optional configuration
    required: false
    default: default_value
inputs:
  type: input_type
  source: where_input_comes_from
  required_sections:
    - Section1
    - Section2
outputs:
  type: output_type
  location: path/to/output/[variable].extension
  format: description of output structure
tools:
  - Read
  - Write
  - Grep
  - Glob
  - WebSearch
  - Bash
chain:
  upstream:
    - upstream-skill-name
  downstream:
    - downstream-skill-name
  metadata_pass:
    - key1
    - key2
tags:
  - category
  - type
  - domain
---

# Skill Name

## Description
Detailed description of what this skill does, when to use it, and what problems it solves.

## Trigger
Explain when Claude should invoke this skill based on user requests.

## Instructions

When executing this skill, follow this systematic methodology:

### 1. Input Analysis Phase

- Step 1: Validate inputs
- Step 2: Extract required information
- Step 3: Check prerequisites

### 2. Processing Phase

- Step 1: Main processing logic
- Step 2: Handle edge cases
- Step 3: Generate intermediate results

### 3. Output Generation Phase

- Step 1: Format output
- Step 2: Add metadata
- Step 3: Save to appropriate location

### 4. Quality Assurance

Ensure output meets these criteria:
- **Criterion 1**: Description
- **Criterion 2**: Description
- **Criterion 3**: Description

### 5. Error Handling

If errors occur:
- Handle specific error types
- Provide helpful feedback
- Suggest corrective actions

## Output Format

```markdown
[Specify exact output format/template here]
```

## Tools to Utilize

- **ToolName**: Purpose and when to use it
- **ToolName**: Purpose and when to use it

## Example Invocation

**User:** "Example user request"

**Response should include:**
- Expected action 1
- Expected action 2
- Expected output

## Success Criteria

The skill has succeeded when:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Limitations

Known limitations or edge cases:
- Limitation 1
- Limitation 2
```

---

## Meta-Skill: Skills Creator

Here's a skill that creates other skills:

```markdown
---
name: skill-creator
description: Generate new Claude Code skills from specifications
trigger:
  - keyword: create skill
  - keyword: new skill
  - keyword: skill creator
  - pattern: "create .* skill for"
  - pattern: "generate skill (for|to)"
arguments:
  - name: purpose
    description: What the new skill should accomplish
    required: true
  - name: input_type
    description: Type of input the skill accepts
    required: false
  - name: output_type
    description: Type of output the skill produces
    required: false
  - name: complexity
    description: Complexity level (simple, moderate, complex)
    required: false
    default: moderate
inputs: null
outputs:
  type: markdown
  location: .claude/skills/[skill-name].md
  format: Complete skill definition with YAML frontmatter and instructions
tools:
  - Read
  - Write
  - AskUserQuestion
chain:
  upstream: null
  downstream: null
tags:
  - meta
  - skill-generation
  - development
---

# Skill Creator

## Description
A meta-skill for generating new Claude Code skills. Creates properly formatted skill definitions with YAML frontmatter and detailed instructions.

## Trigger
Use this skill when the user wants to create a new custom skill for their project.

## Instructions

When creating a new skill, follow this systematic methodology:

### 1. Requirements Gathering Phase

**Step 1: Understand the Purpose**
- Ask clarifying questions about what the skill should accomplish
- Identify the problem it solves
- Determine the target use cases
- Understand the expected workflow

**Step 2: Define Inputs and Outputs**
- What data/files does the skill need?
- What should it produce?
- What format should outputs take?
- Where should outputs be saved?

**Step 3: Identify Dependencies**
- What tools are needed?
- Does it chain with other skills?
- What prerequisites exist?

### 2. Skill Design Phase

**Step 1: Design the Metadata**

Create YAML frontmatter with:
- **name**: kebab-case name derived from purpose
- **description**: Clear, one-line summary
- **trigger**: 3-5 keywords and 1-2 patterns
- **arguments**: All required and optional arguments
- **inputs**: Input type and source
- **outputs**: Output type, location pattern, and format
- **tools**: All Claude Code tools needed
- **chain**: Upstream/downstream relationships
- **tags**: 2-4 relevant tags

**Step 2: Structure the Instructions**

Organize into clear phases:
1. Input Analysis/Validation Phase
2. Processing Phase(s)
3. Output Generation Phase
4. Quality Assurance

**Step 3: Add Quality Standards**

Include:
- Success criteria
- Error handling
- Edge cases
- Quality checklist

**Step 4: Provide Examples**

Add:
- Example invocation
- Expected inputs
- Expected outputs
- Common use cases

### 3. Implementation Phase

**Step 1: Write Complete Skill File**

Generate a complete .md file with:
- Complete YAML frontmatter
- Detailed phase-by-phase instructions
- Quality standards
- Examples
- Tools documentation
- Success criteria

**Step 2: Choose Appropriate Complexity**

- **Simple**: 2-3 phases, basic tools, straightforward logic
- **Moderate**: 3-5 phases, multiple tools, some conditionals
- **Complex**: 5+ phases, advanced tools, complex workflows

**Step 3: Optimize for Reusability**

- Use variables for file paths
- Make arguments flexible
- Support multiple input types when possible
- Provide defaults for optional arguments

### 4. Documentation Phase

**Step 1: Document Usage**

Clearly explain:
- When to use this skill
- How to invoke it
- What arguments are required
- What outputs to expect

**Step 2: Document Limitations**

List:
- Known edge cases
- Unsupported scenarios
- Performance considerations
- Dependencies

### 5. Output Generation

Save the skill file to `.claude/skills/[skill-name].md`

Include in the output:
```markdown
# Skill Created: [Skill Name]

## Location
.claude/skills/[skill-name].md

## Usage
Invoke with:
- `/[skill-name] [arguments]`
- Or by using trigger keywords/patterns

## Quick Start
[Brief example of how to use the skill]

## Next Steps
1. Test the skill with sample inputs
2. Refine based on results
3. Add to project CLAUDE.md if needed
```

### 6. Quality Standards

Ensure the generated skill meets these criteria:

- **Complete**: Has all required metadata and sections
- **Clear**: Instructions are unambiguous
- **Consistent**: Follows naming and formatting conventions
- **Documented**: Includes examples and explanations
- **Tested**: Mentally verify the workflow makes sense
- **Maintainable**: Easy to update and modify

## Tools to Utilize

- **AskUserQuestion**: Gather requirements and clarify details
- **Read**: Check existing skills for patterns and consistency
- **Write**: Save the generated skill file

## Example Invocation

**User:** "Create a skill for generating API documentation from Python code"

**Response should:**
1. Ask clarifying questions about:
   - Input: Which Python files or modules?
   - Output: What documentation format? (Markdown, HTML, etc.)
   - Details: What should be documented? (Classes, functions, parameters?)
2. Design appropriate metadata:
   - name: api-doc-generator
   - Tools: Read, Grep, Glob, Write, Bash
   - Arguments: source_path, output_format, include_private
3. Create phased instructions:
   - Phase 1: Scan Python files for docstrings
   - Phase 2: Extract function/class signatures
   - Phase 3: Format documentation
   - Phase 4: Generate table of contents
4. Include quality standards for documentation completeness
5. Save to `.claude/skills/api-doc-generator.md`

## Success Criteria

The skill creation has succeeded when:
- [ ] Complete YAML frontmatter with all required fields
- [ ] Clear, phase-based instructions
- [ ] Quality standards defined
- [ ] Examples provided
- [ ] File saved to correct location
- [ ] Skill is ready to be invoked immediately

## Templates for Common Skill Types

### Documentation Generator
- Input: Source code files
- Processing: Extract, parse, format
- Output: Documentation files
- Tools: Read, Grep, Glob, Write

### Code Analyzer
- Input: Code files
- Processing: Analyze patterns, detect issues
- Output: Analysis report
- Tools: Read, Grep, Glob, Bash

### Content Creator
- Input: Topic or source material
- Processing: Research, structure, write
- Output: Formatted content
- Tools: WebSearch, WebFetch, Read, Write

### File Transformer
- Input: Files in format A
- Processing: Parse, transform, validate
- Output: Files in format B
- Tools: Read, Write, Edit

### Project Generator
- Input: Project specifications
- Processing: Create structure, boilerplate
- Output: Project scaffold
- Tools: Write, Bash, Glob

## Limitations

- Cannot create skills requiring tools not available in Claude Code
- Complex multi-agent workflows may need manual refinement
- Skills requiring external APIs need manual API key configuration
```

---

## Examples

### Example 1: Simple Skill (File Organizer)

```markdown
---
name: file-organizer
description: Organize files by extension into categorized directories
trigger:
  - keyword: organize files
  - keyword: sort files
  - pattern: "organize .* by extension"
arguments:
  - name: source_dir
    description: Directory to organize
    required: true
  - name: create_structure
    description: Create standard directory structure
    required: false
    default: true
inputs:
  type: directory
  source: file system
outputs:
  type: organized directory structure
  location: [source_dir]/organized/
  format: Files sorted by extension into subdirectories
tools:
  - Bash
  - Glob
chain:
  upstream: null
  downstream: null
tags:
  - file-management
  - organization
  - utility
---

# File Organizer

## Description
Organizes files in a directory by their extensions into categorized subdirectories.

## Instructions

### 1. Discovery Phase
- Use Glob to list all files in source directory
- Identify unique file extensions
- Group files by extension

### 2. Organization Phase
- Create subdirectories for each extension type
- Move files to appropriate directories
- Handle files without extensions

### 3. Reporting Phase
- Generate summary of organization
- List files moved
- Report any errors

## Quality Standards
- No files lost or duplicated
- Clear naming conventions
- Summary report generated
```

### Example 2: Moderate Skill (Test Generator)

```markdown
---
name: test-generator
description: Generate unit tests for Python functions
trigger:
  - keyword: generate tests
  - keyword: create tests
  - pattern: "write tests for"
arguments:
  - name: source_file
    description: Python file to generate tests for
    required: true
  - name: test_framework
    description: Testing framework (pytest, unittest)
    required: false
    default: pytest
inputs:
  type: python file
  source: user-specified path
outputs:
  type: python test file
  location: tests/test_[source_filename].py
  format: pytest/unittest format
tools:
  - Read
  - Write
  - Grep
  - Bash
chain:
  upstream: null
  downstream:
    - test-runner
tags:
  - testing
  - python
  - code-generation
---

# Test Generator

## Instructions

### 1. Analysis Phase
- Read source file
- Extract all function definitions
- Identify function parameters and return types
- Note any dependencies

### 2. Test Design Phase
- Create test cases for each function:
  - Happy path (normal inputs)
  - Edge cases (boundary values)
  - Error cases (invalid inputs)
- Design test fixtures if needed

### 3. Generation Phase
- Create test file with proper imports
- Generate test functions
- Add docstrings explaining test purpose
- Include assertions

### 4. Validation Phase
- Verify test syntax
- Ensure imports are correct
- Run basic validation

## Quality Standards
- Minimum 3 test cases per function
- Clear test names
- Proper assertions
- Runs without errors
```

### Example 3: Complex Skill (Project Scaffolder)

```markdown
---
name: project-scaffolder
description: Create complete project structure with boilerplate code
trigger:
  - keyword: create project
  - keyword: scaffold project
  - pattern: "new .* project"
arguments:
  - name: project_name
    description: Name of the project
    required: true
  - name: project_type
    description: Type (python-lib, web-app, ml-project)
    required: true
  - name: include_tests
    description: Include test directory and setup
    required: false
    default: true
  - name: include_ci
    description: Include CI/CD configuration
    required: false
    default: false
inputs: null
outputs:
  type: project directory structure
  location: ./[project_name]/
  format: Complete project with files and structure
tools:
  - Write
  - Bash
  - AskUserQuestion
chain:
  upstream: null
  downstream:
    - test-generator
    - doc-generator
tags:
  - project-management
  - scaffolding
  - boilerplate
---

# Project Scaffolder

## Instructions

### 1. Planning Phase
- Gather requirements through AskUserQuestion
- Determine project structure based on type
- Identify required configuration files

### 2. Structure Creation Phase
- Create directory structure
- Generate configuration files
- Create initial module files

### 3. Boilerplate Generation Phase
- Write README.md template
- Create setup.py or package.json
- Add .gitignore
- Create CLAUDE.md if requested

### 4. Testing Setup Phase
- Create test directory
- Add test configuration
- Generate sample tests

### 5. CI/CD Setup Phase (if requested)
- Add GitHub Actions or similar
- Create deployment configuration

### 6. Documentation Phase
- Generate setup instructions
- Create usage examples
- Add contributing guidelines

## Quality Standards
- All required files present
- Configuration valid
- Structure follows best practices
- Documentation complete
```

---

## Skill Directory Organization

Recommended structure for projects with multiple skills:

```
your-project/
├── .claude/
│   ├── skills/
│   │   ├── core/              # Essential project skills
│   │   │   ├── build.md
│   │   │   └── deploy.md
│   │   ├── development/       # Development workflow skills
│   │   │   ├── test-gen.md
│   │   │   └── doc-gen.md
│   │   ├── analysis/          # Code analysis skills
│   │   │   ├── linter.md
│   │   │   └── complexity.md
│   │   └── utils/             # Utility skills
│   │       ├── file-org.md
│   │       └── cleanup.md
│   └── commands/              # Alternative: use commands/
├── CLAUDE.md                  # Reference skills in project guide
└── SKILLS.md                  # This file (optional, for reference)
```

---

## Advanced Topics

### Conditional Logic in Skills

Use decision trees in instructions:

```markdown
### 2. Processing Phase

**If** input is type A:
  - Step 1a
  - Step 2a
**Else if** input is type B:
  - Step 1b
  - Step 2b
**Else**:
  - Show error and ask for clarification
```

### Error Recovery

Include error handling procedures:

```markdown
### Error Handling

**If** file not found:
  1. Search for similar filenames
  2. Ask user if they meant one of them
  3. Proceed with confirmed file

**If** parsing fails:
  1. Identify line causing error
  2. Attempt partial processing
  3. Report what was processed successfully
```

### Metadata Passing in Chains

Pass data between chained skills:

```yaml
chain:
  upstream:
    - data-collector
  downstream:
    - report-generator
  metadata_pass:
    - source_file_path
    - collection_timestamp
    - record_count
```

Instructions should reference metadata:
```markdown
### 1. Initialization Phase
- Read metadata from upstream skill: `source_file_path`
- Use `collection_timestamp` for report header
- Validate `record_count` matches expected input
```

---

## Quick Reference

### Skill Creation Checklist

- [ ] Name is clear and descriptive (kebab-case)
- [ ] Description is concise (one line)
- [ ] Triggers cover common use cases (3-5 total)
- [ ] Arguments are well-defined
- [ ] Required arguments are clearly marked
- [ ] Default values for optional arguments
- [ ] Input/output types specified
- [ ] Tools list is complete
- [ ] Chain relationships defined (if applicable)
- [ ] Tags are relevant and specific
- [ ] Instructions are phase-based
- [ ] Quality standards included
- [ ] Examples provided
- [ ] Error handling covered
- [ ] Success criteria defined

### Common Tools by Use Case

| Use Case | Tools |
|----------|-------|
| File operations | Read, Write, Edit, Glob |
| Code search | Grep, Glob, Read |
| Research | WebSearch, WebFetch |
| Command execution | Bash |
| Complex workflows | Task |
| User interaction | AskUserQuestion |

### YAML Frontmatter Quick Template

```yaml
---
name: skill-name
description: What it does
trigger:
  - keyword: word
arguments:
  - name: arg
    description: desc
    required: true
inputs: null
outputs:
  type: type
  location: path
tools:
  - ToolName
chain:
  upstream: null
  downstream: null
tags:
  - tag
---
```

---

## Resources

### File Locations
- Skills: `.claude/skills/*.md` or `.claude/commands/*.md`
- Main guide: `CLAUDE.md` (reference skills here)
- This guide: `SKILLS.md` (optional reference)

### Naming Standards
- **Skills**: kebab-case (e.g., `test-generator`)
- **Files**: Match skill name (e.g., `test-generator.md`)
- **Arguments**: snake_case (e.g., `source_file`)
- **Tags**: lowercase (e.g., `testing`, `python`)

### Useful Patterns

**Documentation skills**: `doc-*` prefix
**Testing skills**: `test-*` prefix
**Generation skills**: `*-generator` suffix
**Analysis skills**: `*-analyzer` suffix
**Utility skills**: No specific pattern

---

**Remember**: Skills are meant to make repetitive tasks easier and more consistent. Start simple, test thoroughly, and refine based on actual usage.
