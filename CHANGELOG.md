# Changelog

All notable changes to TinyCode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation restructuring
- New organized `docs/` directory with categorized documentation
- Standard project files (LICENSE, CONTRIBUTING.md, CHANGELOG.md)
- Improved documentation navigation and structure

### Changed
- Reorganized documentation from root to `docs/` directory
- Consolidated redundant documentation files
- Updated README.md for better clarity
- Enhanced CLAUDE.md with complete architecture details

## [1.0.0] - 2024-01-01

### Added
- Initial release of TinyCode
- Three-mode operation system (Chat, Propose, Execute)
- Plan-based execution framework with safety features
- RAG (Retrieval-Augmented Generation) system
- Local-first architecture using Ollama and TinyLlama
- Genetics corpus specialization
- API server with Flask and Prometheus metrics
- Docker deployment support
- Comprehensive safety infrastructure:
  - Four-tier safety levels
  - Timeout management
  - Audit logging with hash-chain integrity
  - Resource monitoring
  - Rate limiting
- Multi-format document ingestion (PDF, DOCX, code files)
- Hybrid search combining dense embeddings and BM25
- Interactive CLI with Rich formatting
- Offline operation support
- Production deployment configurations

### Security
- Path traversal protection
- Dangerous pattern detection
- Automatic backup creation before risky operations
- API key authentication for production deployments
- Hash-chain integrity for audit logs

### Documentation
- Super-user guide
- Command reference card
- Workflow diagrams
- Offline setup guide
- Production deployment guide
- RAG system documentation

## Version History

- **1.0.0** - Initial public release with full feature set
- **0.9.0** - Beta release with core functionality
- **0.5.0** - Alpha release for testing

---

For detailed information about each release, see the [GitHub Releases](https://github.com/davidkarpay/tinycode/releases) page.