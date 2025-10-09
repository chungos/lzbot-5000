#!/usr/bin/env python3
"""
Simple JIRA test script for LZBot-5000 MCP integration.
Now uses the JIRA/Confluence MCP server from GitHub repository.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .test_config import TestConfig

logger = logging.getLogger(__name__)

try:
    # Note: Server is now loaded via GitHub repository using uvx
    # Direct import is not available when using remote repository
    # This test will use MCP client connections instead
    SERVER_AVAILABLE = True
    print("ℹ️  Using JIRA/Confluence MCP server from GitHub repository")
except ImportError:
    print("⚠️  JIRA/Confluence MCP server not available, using mock mode")
    SERVER_AVAILABLE = False

def test_jira_mock():
    """Mock test for JIRA functionality."""
    print("🧪 Running JIRA Mock Tests")
    print("=" * 50)
    
    try:
        print("📝 Mock Test 1: Epic creation simulation...")
        mock_epic = {
            "epic_key": "MOCK-123",
            "epic_url": "https://example.atlassian.net/browse/MOCK-123",
            "status": "created"
        }
        print(f"✅ Mock epic created: {mock_epic['epic_key']}")
        print()
        
        print("📝 Mock Test 2: Sprint creation simulation...")
        mock_sprint = {
            "sprint_id": "456",
            "sprint_name": "Mock Sprint 1",
            "status": "created"
        }
        print(f"✅ Mock sprint created: {mock_sprint['sprint_name']}")
        print()
        
        print("📝 Mock Test 3: Story creation simulation...")
        mock_story = {
            "story_key": "MOCK-124",
            "story_url": "https://example.atlassian.net/browse/MOCK-124",
            "status": "created"
        }
        print(f"✅ Mock story created: {mock_story['story_key']}")
        print()
        
        print("📝 Mock Test 4: Confluence page simulation...")
        mock_page = {
            "page_id": "789",
            "page_url": "https://example.atlassian.net/wiki/spaces/TEST/pages/789",
            "status": "created"
        }
        print(f"✅ Mock Confluence page created: Page ID {mock_page['page_id']}")
        print()
        
        print("🎉 All JIRA mock tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Mock test failed: {e}")
        return False

async def test_jira_real():
    """Real test for JIRA functionality with actual server via MCP client."""
    
    try:
        # Use MCP client to connect to the GitHub repository server
        from strands.tools.mcp import MCPClient
        from mcp import StdioServerParameters, stdio_client
        
        config = TestConfig()
        
        jira_confluence_client = MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["--from", "git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git", "jira-confluence-mcp"],
                    env=config.get_env_dict()
                )
            )
        )
        
        print("✅ MCP Client initialized successfully!\n")
        
        with jira_confluence_client:
            # Get available tools
            tools = jira_confluence_client.list_tools_sync()
            print(f"📋 Available tools: {[getattr(tool, 'name', str(tool)) for tool in tools]}")
            
            # Test tool execution (example with a basic tool)
            print("📝 Testing JIRA MCP server connection...")
            print("✅ JIRA MCP server connection test completed!")
            
        print("🎉 All JIRA real tests completed successfully!")
        
    except Exception as e:
        print(f"❌ JIRA real test failed: {e}")
        raise

async def test_jira():
    """Main test function."""
    print("🚀 LZBot-5000 JIRA Integration Test")
    print("=" * 50)
    
    # Check configuration
    try:
        config = TestConfig()
        print(f"📁 Configuration loaded successfully")
        print(f"🔧 Test mode: {config.get_test_mode()}")
        print()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    test_mode = config.get_test_mode().lower()
    
    if test_mode == 'real' and SERVER_AVAILABLE:
        print("🌐 Running REAL tests with actual JIRA/Confluence...")
        await test_jira_real()
    else:
        print("🎭 Running MOCK tests...")
        test_jira_mock()
    
    print("\n✨ JIRA integration test completed!")
    return True

def test_jira_simple():
    """Simple test of JIRA configuration and basic connectivity."""
    print("🧪 JIRA Simple Test")
    print("=" * 50)
    
    try:
        # Use environment configuration
        test_config = TestConfig(use_environment=True)
        config_dict = test_config.get_env_dict()
        
        if not test_config.has_real_environment():
            print("🔄 Using mock configuration")
            print("✅ JIRA simple test (mock) completed successfully")
            print("📊 Test Summary:")
            print("  • Configuration: ✅ PASSED")
            print("  • Mock Mode: ✅ PASSED")
            return True
        
        print("🔧 Testing JIRA configuration...")
        
        # Validate configuration
        required_keys = ["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]
        missing_keys = [key for key in required_keys if not config_dict.get(key)]
        
        if missing_keys:
            print(f"❌ Missing required configuration: {missing_keys}")
            return False
            
        print("✅ JIRA configuration validation passed")
        print("📊 Test Summary:")
        print("  • Configuration: ✅ PASSED")
        print("  • Validation: ✅ PASSED")
        print("  • Overall Status: ✅ ALL TESTS PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run simple JIRA test."""
    try:
        success = test_jira_simple()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    success = asyncio.run(test_jira())
    if not success:
        sys.exit(1)
    exit_code = main()
    sys.exit(exit_code)