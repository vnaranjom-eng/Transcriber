# Contributing to Transcriber Pipecat

Thank you for your interest in contributing to Transcriber Pipecat! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Transcriber.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Push to your fork: `git push origin feature/your-feature-name`
6. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/vnaranjom-eng/Transcriber.git
cd Transcriber

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## Code Style

We follow PEP 8 style guidelines. Please ensure your code:

- Uses 4 spaces for indentation
- Has descriptive variable names
- Includes docstrings for functions and classes
- Has type hints where appropriate

### Formatting

Use `black` for code formatting:

```bash
black transcriber_pipecat/
```

### Linting

Use `flake8` for linting:

```bash
flake8 transcriber_pipecat/
```

### Type Checking

Use `mypy` for type checking:

```bash
mypy transcriber_pipecat/
```

## Testing

We use `pytest` for testing. Please add tests for any new functionality.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=transcriber_pipecat
```

## Commit Messages

Write clear and descriptive commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add support for Spanish language transcription

- Implement Spanish language model
- Add language detection
- Update documentation

Fixes #123
```

## Pull Request Process

1. Update the README.md or DOCUMENTATION.md with details of changes if needed
2. Add tests for any new functionality
3. Ensure all tests pass
4. Update the version number if applicable
5. Your PR will be reviewed by maintainers

## Bug Reports

When filing a bug report, please include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Any relevant logs or error messages

## Feature Requests

When requesting a feature, please include:

- A clear and descriptive title
- Detailed description of the proposed feature
- Use cases for the feature
- Any implementation ideas you have

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Unacceptable Behavior

- Harassment of any kind
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Questions?

Feel free to open an issue with your question, and we'll do our best to help!

## License

By contributing to Transcriber Pipecat, you agree that your contributions will be licensed under the MIT License.
