# Project Overview

An intelligent AWS Landing Zone design tool that leverages AWS Bedrock, Strands framework, AWS Diagram MCP Server, and JIRA/Confluence integration to automatically generate comprehensive, Well-Architected Framework-compliant landing zone architectures with professional diagrams, implementation guides, and automatic backlog publishing.

## Folder Structure

lzbot-5000/
├── lzbot/                      # Main package
│   ├── __init__.py            # Package exports
│   ├── agent.py               # AI agent with validation
│   ├── clients.py             # MCP client management
│   ├── file_handler.py        # File operations
│   ├── input_handler.py       # CLI processing with validation
│   ├── logging_config.py      # Structured logging framework
│   ├── exceptions.py          # Custom exception types
│   └── validation.py          # Pydantic models for I/O validation
├── tests/                      # Comprehensive test suite
│   ├── run_tests.py           # Interactive test runner
│   ├── test_config.py         # Updated test configuration
│   ├── test_jira_mcp.py       # JIRA integration tests
│   ├── test_confluence_mcp.py # Confluence integration tests
│   └── test_confluence_attachment.py # Attachment functionality
├── outputs/                   # Generated diagrams and documentation
├── DEPLOYMENT.md              # Production deployment guide
├── OPERATIONS.md              # Day-to-day operations guide
├── integration_test.py        # Integration test suite
├── test_validation.py         # Validation system tests
├── examples/                  # Example outputs and usage
├── main.py                    # Application entry point
├── pyproject.toml             # Modern Python packaging
├── .env.example              # Environment template
└── README.md                 # Readme file

## Documentation
- ** Go through README.md file to understand the current state of the project and update README.md after each iteration if required. Keep documentation clear and avoid duplicates.
- ** Maintain DEPLOYMENT.md and OPERATIONS.md.
## Coding Standards

## General Principles
- **Readability:** Prioritize clear, concise, and easily understandable code.
- **Maintainability:** Write code that is easy to modify and extend in the future.
- **Efficiency:** Consider performance implications, but prioritize clarity unless performance is critical.
- **Testing:** Always update test cases and add new test cases for new functionalities when making changes. Run all test cases and make sure all test cases are succeeded.

## Code Style
- **PEP 8 Compliance:** Adhere strictly to PEP 8 style guide for Python code.
- **Indentation:** Use 4 spaces for indentation.
- **Line Length:** Aim for a maximum line length of 79 characters.
- **Imports:** Organize imports at the top of the file, grouped by standard library, third-party, and local imports.

## Naming Conventions
- **Variables and Functions:** Use `snake_case` for variable and function names.
- **Classes:** Use `PascalCase` for class names.
- **Constants:** Use `ALL_CAPS` for module-level constants.
- **Private Members:** Prefix private class members with a single underscore (`_`).

## Type Hinting
- **Use Type Hints:** Employ type hints consistently for function parameters and return values.
- **Clarity:** Ensure type hints are clear and accurately reflect the expected types.

## Docstrings
- **Use Google Style Docstrings:** Follow the Google style guide for docstrings for functions, methods, and classes.
- **Comprehensive:** Include a brief summary, arguments, return values, and any raised exceptions.

## Error Handling
- **Specific Exceptions:** Catch specific exceptions rather than broad `Exception` clauses.
- **Informative Error Messages:** Provide clear and helpful error messages for debugging.

## Testing
- **Unit Tests:** Encourage writing unit tests for individual functions and methods.
- **Folder:** All tests should be inside tests folder