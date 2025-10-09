# Test Suite for LZBot-5000

This directory contains comprehensive test cases for the LZBot-5000 AWS Landing Zone Designer with JIRA/Confluence integration.

## Test Structure

### JIRA Tests
- **`test_jira_mcp.py`** - MCP client-based JIRA testing
- **`test_jira_simple.py`** - Direct JIRA server testing

### Confluence Tests  
- **`test_confluence_mcp.py`** - Comprehensive Confluence functionality testing
- **`test_confluence_simple.py`** - Direct Confluence server testing
- **`test_confluence_integration.py`** - AWS architecture publishing workflow
- **`test_confluence_edge_cases.py`** - Error handling and edge cases

## Running Tests

### Individual Test Files
```bash
# Run JIRA tests
python tests/test_jira_mcp.py
python tests/test_jira_simple.py

# Run Confluence tests
python tests/test_confluence_mcp.py
python tests/test_confluence_simple.py
python tests/test_confluence_integration.py
python tests/test_confluence_edge_cases.py
```

### All Tests
```bash
# Run all tests (if using pytest)
pytest tests/

# Or run individually
for test in tests/test_*.py; do python "$test"; done
```

## Test Categories

### 🎯 **Basic Functionality Tests**
- Page creation and content management
- Epic, sprint, and story creation in JIRA
- JIRA-Confluence linking

### 🏗️ **AWS Architecture Integration Tests**
- Complete architecture documentation publishing
- Multi-sprint project planning
- Technical specifications and diagrams
- Implementation backlog creation

### 🛡️ **Edge Cases and Error Handling**
- Input validation (empty titles, large content, special characters)
- Network error handling (timeouts, rate limits, permissions)
- Data consistency validation
- Security testing (injection prevention)
- Concurrent operations

### 🔄 **End-to-End Workflow Tests**
- Full AWS architecture project lifecycle
- Epic → Sprints → Stories → Documentation workflow
- Cross-linking between JIRA and Confluence
- Real-world content scenarios

## Test Environment Setup

Make sure these environment variables are set:
```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_PROJECT_KEY="YOUR_PROJECT"
export JIRA_BOARD_ID="1"
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="YOUR_SPACE"
export CONFLUENCE_PARENT_PAGE_ID="page-id"
```

## Expected Test Outputs

Each test provides detailed output including:
- ✅/❌ Status for each test case
- URLs to created JIRA items and Confluence pages
- Success rate percentages
- Detailed error messages for failures
- Performance metrics and timing

## Test Coverage

- **JIRA Integration**: Epic, sprint, story creation and linking
- **Confluence Publishing**: Page creation, content formatting, macros
- **AWS Content**: Architecture diagrams, technical specs, cost analysis
- **Error Scenarios**: Invalid inputs, network issues, permissions
- **Security**: Injection prevention, access control validation
- **Performance**: Large content handling, concurrent operations

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify API tokens and URLs
2. **Permission Errors**: Check JIRA project and Confluence space permissions
3. **Network Timeouts**: Verify connectivity to Atlassian services
4. **Import Errors**: Ensure MCP server dependencies are available

### Mock vs Real Testing
- Tests with "simple" suffix use direct server calls
- Tests with "mcp" suffix use MCP client protocol
- Integration tests can use mock clients for safe testing
- Edge case tests use mock clients to simulate error conditions

## Contributing

When adding new tests:
1. Follow the existing naming convention (`test_[component]_[type].py`)
2. Include comprehensive error handling
3. Add realistic test data and scenarios
4. Document expected behaviors and edge cases
5. Update this README with new test descriptions