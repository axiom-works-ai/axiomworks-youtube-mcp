# Contributing to axiomworks-youtube-mcp

Thank you for your interest in contributing! This project aims to be the definitive YouTube + YouTube Music MCP server.

## How to Contribute

### Reporting Issues
- Use [GitHub Issues](https://github.com/axiom-works-ai/axiomworks-youtube-mcp/issues)
- Include: what you did, what you expected, what happened, and your Python version
- For API gaps, check [API_GAPS.md](API_GAPS.md) first — it may already be documented

### Submitting Code

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Install dev dependencies: `pip install -e ".[dev]"`
4. Make your changes
5. Run tests: `pytest tests/ -v`
6. Run lint: `ruff check src/`
7. Commit with a clear message
8. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/axiom-works-ai/axiomworks-youtube-mcp.git
cd axiomworks-youtube-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Code Style

- Python 3.10+, type hints on all public functions
- `ruff` for linting (line length: 100)
- `mypy` for type checking
- Tests required for new tools
- Docstrings on all MCP tools with `Args` and `Returns` sections

### What We're Looking For

- **New tools**: Additional YouTube or YouTube Music functionality
- **Bug fixes**: Especially around edge cases in API responses
- **Documentation**: Usage examples, tutorials, translations
- **ytmusicapi upstream contributions**: See [UPSTREAM_CONTRIBUTIONS.md](UPSTREAM_CONTRIBUTIONS.md)
- **Test coverage**: Integration tests with mocked API responses

### Code of Conduct

Be respectful, constructive, and professional. We're building tools, not drama.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
