# Contributing to TinyCode

Thank you for your interest in contributing to TinyCode! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use the issue template if provided
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, Ollama version)
   - Relevant error messages or logs

### Suggesting Features

1. Check the roadmap and existing feature requests
2. Open a discussion before implementing major changes
3. Explain the use case and benefits
4. Consider backward compatibility

### Submitting Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/tinycode.git
   cd tinycode
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

3. **Make Your Changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
   - Keep commits focused and atomic

4. **Test Your Changes**
   ```bash
   # Run tests
   pytest

   # Test stress tests
   python run_stress_tests.py

   # Verify offline functionality
   python scripts/verify_offline_models.py
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature" # or "fix: resolve issue"
   ```

   Use conventional commit messages:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions or changes
   - `refactor:` Code refactoring
   - `style:` Code style changes
   - `chore:` Maintenance tasks

6. **Push and Create PR**
   ```bash
   git push origin your-branch-name
   ```
   Then create a pull request on GitHub.

## Development Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

2. **Set Up Pre-commit Hooks** (if configured)
   ```bash
   pre-commit install
   ```

3. **Download Models**
   ```bash
   ./scripts/download_models.sh
   ```

## Code Style Guidelines

### Python Code
- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions and classes

### Documentation
- Use clear, concise language
- Include code examples
- Keep README and docs up to date
- Use proper markdown formatting

### Safety and Security
- Never commit sensitive information
- Validate all user inputs
- Follow the safety guidelines in the codebase
- Test security features thoroughly

## Testing

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest test_plan_execution.py

# With coverage
pytest --cov=tiny_code
```

### Writing Tests
- Place tests in appropriate test files
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies

## Documentation

- Update relevant documentation for any changes
- Add docstrings to new functions/classes
- Update CHANGELOG.md for notable changes
- Keep examples current and working

## Review Process

Pull requests will be reviewed for:
1. Code quality and style
2. Test coverage
3. Documentation updates
4. Backward compatibility
5. Security implications
6. Performance impact

## Questions?

If you have questions, feel free to:
- Open a discussion
- Check the documentation in `/docs`
- Review existing issues and PRs

Thank you for contributing to TinyCode!