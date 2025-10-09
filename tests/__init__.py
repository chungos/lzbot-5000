"""
Test suite for LZBot-5000 - AWS Landing Zone Designer with JIRA/Confluence Integration

This package contains comprehensive test cases for:
- JIRA integration functionality
- Confluence page creation and management
- AWS architecture documentation publishing
- Error handling and edge cases
- End-to-end workflow integration
"""

__version__ = "1.0.0"
__author__ = "LZBot-5000 Team"

# Test categories
JIRA_TESTS = [
    "test_jira_mcp",
    "test_jira_simple"
]

CONFLUENCE_TESTS = [
    "test_confluence_mcp", 
    "test_confluence_simple",
    "test_confluence_integration",
    "test_confluence_edge_cases"
]

ALL_TESTS = JIRA_TESTS + CONFLUENCE_TESTS

def get_test_description():
    """Get description of available test categories."""
    return {
        "jira": "Tests for JIRA integration (epic, sprint, story creation)",
        "confluence": "Tests for Confluence page creation and content management", 
        "integration": "End-to-end workflow tests for AWS architecture publishing",
        "edge_cases": "Error handling and edge case validation tests"
    }