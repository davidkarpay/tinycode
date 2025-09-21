"""Prompt templates for various coding tasks"""

SYSTEM_PROMPT = """You are Tiny Code, an AI coding assistant powered by TinyLlama. You help with:
- Writing clean, efficient code
- Debugging and fixing issues
- Explaining code concepts
- Refactoring and optimization
- Generating tests
Be concise, accurate, and practical in your responses."""

CODE_COMPLETION_PROMPT = """Complete the following code:

{code_context}

Requirements: {requirements}

Provide a clean, working implementation."""

BUG_FIX_PROMPT = """Analyze and fix the following code issue:

Code:
{code}

Error/Issue:
{error}

Provide the corrected code with an explanation of the fix."""

CODE_EXPLAIN_PROMPT = """Explain the following code in clear, simple terms:

{code}

Focus on:
- What the code does
- How it works
- Key concepts used"""

REFACTOR_PROMPT = """Refactor the following code for better:
- Readability
- Performance
- Maintainability

Code:
{code}

Specific requirements: {requirements}"""

TEST_GENERATION_PROMPT = """Generate comprehensive tests for the following code:

{code}

Include:
- Unit tests for individual functions
- Edge cases
- Error handling tests"""

CODE_REVIEW_PROMPT = """Review the following code and provide feedback:

{code}

Consider:
- Code quality
- Potential bugs
- Performance issues
- Best practices"""