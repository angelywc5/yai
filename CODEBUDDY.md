# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## Project Overview

This is a Python 3.10 backend project following a modular architecture design pattern. The codebase emphasizes maintainability through clear separation of concerns and follows a structured development workflow.

## Development Workflow

All development follows a three-phase approach:
1. **Plan** - Define requirements and objectives
2. **Detailed Design** - Create technical specifications and architecture decisions
3. **Development** - Implement the solution

This workflow ensures thoughtful architecture decisions before code implementation.

## Common Commands

### Environment Setup
```bash
# Create virtual environment with Python 3.10
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
```

### Running the Application
```bash
# Run main application
python main.py
```

### Development Tools
```bash
# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt

# Run tests (when test suite is established)
pytest tests/

# Run specific test module
pytest tests/test_module_name.py

# Run linting
pylint src/

# Format code
black src/
```

## Code Architecture

### Modular Structure

The project follows a modular architecture pattern designed for maintainability and scalability:

```
yai/
├── src/                    # Main application source code
│   ├── core/              # Core business logic and domain models
│   ├── services/          # Service layer for business operations
│   ├── repositories/      # Data access layer
│   ├── api/               # API endpoints and controllers
│   ├── utils/             # Shared utilities and helpers
│   └── config/            # Configuration management
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation and design docs
│   ├── plans/            # Project plans
│   └── designs/          # Detailed design documents
├── main.py               # Application entry point
└── requirements.txt      # Python dependencies
```

### Design Principles

**Separation of Concerns**: Each module has a single, well-defined responsibility. The architecture separates:
- Business logic (core/)
- Data access (repositories/)
- External interfaces (api/)
- Cross-cutting concerns (utils/)

**Dependency Direction**: Dependencies flow inward toward the core domain. External layers depend on inner layers, never the reverse. This keeps business logic independent of infrastructure details.

**Configuration Management**: All environment-specific settings are centralized in the config/ module. This includes database connections, API keys, and feature flags.

### Module Responsibilities

**core/**: Contains domain models, business rules, and core algorithms. This module should have minimal external dependencies and represent the heart of the application logic.

**services/**: Orchestrates business workflows by coordinating between core logic and repositories. Services handle transaction boundaries and complex operations spanning multiple domain entities.

**repositories/**: Abstracts data persistence mechanisms. Each repository provides CRUD operations for a specific domain entity. This layer isolates the rest of the application from database implementation details.

**api/**: Exposes application functionality through REST endpoints or other interface protocols. Handles request validation, serialization, and HTTP-specific concerns.

**utils/**: Provides shared functionality like logging, validation helpers, date/time utilities, and other common operations used across modules.

## Development Guidelines

### Before Starting Development

1. Create or review the plan document in `docs/plans/`
2. Create detailed design document in `docs/designs/` including:
   - Component architecture
   - Data models
   - API contracts
   - Error handling strategy
3. Review design with stakeholders before implementation

### Code Organization

- Keep modules small and focused (generally < 300 lines)
- Use clear, descriptive names for functions and classes
- Place related functionality together in the same module
- Extract shared code into utils/ rather than duplicating

### Python 3.10 Features

This project targets Python 3.10. Leverage modern Python features:
- Structural pattern matching (match/case statements)
- Type hints with union types using `|` operator
- Better error messages from the interpreter

### Testing Strategy

Write tests at multiple levels:
- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test module interactions and external dependencies
- Place test files alongside source files or in the tests/ directory
- Name test files with `test_` prefix

### Module Dependencies

When creating new modules:
- Core modules should not depend on services or repositories
- Services can depend on core and repositories
- API layer can depend on services but should not directly access repositories
- Avoid circular dependencies between modules

## Project Initialization

For new Python backend projects in this repository:

1. Set up project structure with modular directories
2. Create `requirements.txt` with core dependencies
3. Initialize testing framework (pytest)
4. Set up code quality tools (pylint, black, mypy)
5. Create initial configuration management
6. Document key architectural decisions in design docs
