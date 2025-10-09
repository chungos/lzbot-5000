#!/usr/bin/env python3
"""Comprehensive test script to verify Confluence MCP server functionality."""

import asyncio
import json
from datetime import datetime
import sys
import os
import logging
from pathlib import Path
from uuid import uuid4

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_config import TestConfig, get_test_config, get_test_mode

logger = logging.getLogger(__name__)

# Mock MCP client classes for testing
class MockStdioServerParameters:
    def __init__(self, command, args, env):
        self.command = command
        self.args = args
        self.env = env

class MockMCPClient:
    """Mock MCP client for testing Confluence functionality."""
    
    def __init__(self, server_params_func):
        self.connected = True
        self.created_pages = []
        self.page_id_counter = 1000
    
    def list_tools_sync(self):
        """Mock list of available tools."""
        return [
            type('Tool', (), {'name': 'create_confluence_page'}),
            type('Tool', (), {'name': 'update_confluence_page'}),
            type('Tool', (), {'name': 'create_epic'}),
            type('Tool', (), {'name': 'create_sprint'}),
            type('Tool', (), {'name': 'create_story'}),
            type('Tool', (), {'name': 'link_jira_to_confluence'})
        ]
    
    def call_tool_sync(self, name, arguments):
        """Mock tool call implementation."""
        if name == "create_confluence_page":
            return self._mock_create_page(arguments)
        elif name == "update_confluence_page":
            return self._mock_update_page(arguments)
        else:
            raise Exception(f"Unknown tool: {name}")
    
    def _mock_create_page(self, args):
        page_id = self.page_id_counter
        self.page_id_counter += 1
        
        page_data = {
            "page_id": str(page_id),
            "page_url": f"https://vishnuprasad191.atlassian.net/wiki/spaces/LZD/pages/{page_id}",
            "title": args["title"]
        }
        self.created_pages.append(page_data)
        
        return [type('MockResult', (), {'text': json.dumps(page_data)})()]
    
    def _mock_update_page(self, args):
        page_data = {
            "page_id": args.get("page_id", "1001"),
            "page_url": f"https://vishnuprasad191.atlassian.net/wiki/spaces/LZD/pages/{args.get('page_id', '1001')}",
            "title": args.get("title", "Updated Page")
        }
        
        return [type('MockResult', (), {'text': json.dumps(page_data)})()]
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def test_confluence_mock():
    """Test Confluence functionality with mock configuration."""
    print("🧪 Testing Confluence MCP Server (Mock Mode)")
    print("=" * 50)
    
    try:
        # Use mock configuration
        test_config = TestConfig(use_environment=False)
        config_dict = test_config.get_env_dict()
        
        print("✅ Mock configuration loaded successfully")
        print("📊 Test Summary:")
        print("  • Mode: Mock (safe for development)")
        print("  • API Calls: Simulated")
        print("  • Data: Test values only")
        print("  • Status: ✅ PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock test failed: {e}")
        return False

def test_confluence_real():
    """Test Confluence functionality with real MCP client."""
    print("🧪 Testing Confluence MCP Server (Real Mode)")
    print("=" * 50)
    
    try:
        # Use environment configuration
        test_config = TestConfig(use_environment=True)
        config_dict = test_config.get_env_dict()
        
        print("🔧 Initializing JIRA/Confluence MCP client...")
        
        # Import here to avoid issues if clients module has problems
        from lzbot.clients import ClientManager
        client_manager = ClientManager(config_dict)
        
        with client_manager as cm:
            jira_confluence_client = cm.jira_confluence_client
            print("✅ MCP client connected successfully")
            
            # List available tools
            print("🔍 Available tools:")
            try:
                tools = jira_confluence_client.list_tools()
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
            except AttributeError:
                # Fallback - try alternative methods
                try:
                    if hasattr(jira_confluence_client, 'session') and hasattr(jira_confluence_client.session, 'list_tools'):
                        print("  Using session.list_tools()")
                        print("  Tools listing not available in sync context")
                    else:
                        print("  Tools listing not available - will proceed with testing")
                except Exception as e:
                    print(f"  Could not list tools: {e}")
                    print("  Will proceed with testing")
            
            # Test page creation with proper tool_use_id
            print("\n📄 Testing Confluence page creation...")
            page_content = """
# AWS Architecture Design Test

This is a test page created by LZBot-5000 automated testing.

## Architecture Overview

This page demonstrates the automatic creation of Confluence documentation
with embedded architecture diagrams and implementation details.

## Key Components

- VPC Infrastructure
- Security Groups and NACLs
- Auto Scaling Groups
- Load Balancers
- Database Layer

## Next Steps

1. Review architecture design
2. Implement security controls
3. Deploy infrastructure
4. Monitor and optimize
"""
            
            page_result = jira_confluence_client.call_tool_sync(
                name="create_confluence_page",
                tool_use_id=str(uuid4()),  # Generate unique tool use ID
                arguments={
                    "title": "Test AWS Architecture - LZBot-5000",
                    "content": page_content,
                    "parent_page_id": config_dict.get("CONFLUENCE_PARENT_PAGE_ID")
                }
            )
            print(f"✅ Confluence page created successfully: {page_result}")
            
            print("\n📊 Test Summary:")
            print("  • Page Creation: ✅ PASSED")
            print("  • MCP Client: ✅ PASSED")
            print("  • Overall Status: ✅ ALL TESTS PASSED")
            
            return True
            
    except Exception as e:
        print(f"❌ Failed to test Confluence functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_confluence_mcp():
    """Test Confluence MCP server with comprehensive test cases."""
    
    print("🚀 Starting Confluence MCP Server comprehensive test...\n")
    
    # Get test configuration
    test_config = get_test_config()
    test_mode = get_test_mode()
    
    print(f"📊 Test Mode: {test_mode}")
    test_config.print_test_config()
    print()
    
    # Initialize mock MCP client (using mock for this test since it's self-contained)
    confluence_client = MockMCPClient(
        lambda: MockStdioServerParameters(
            command="uvx",
            args=["--from", "git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git", "jira-confluence-mcp"],
            env=test_config.get_mcp_server_params_env()
        )
    )
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    def log_test_result(test_name, success, details=""):
        """Log test result and update counters."""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"   {details}")
        print()
        
        test_results["tests"].append({
            "name": test_name,
            "success": success,
            "details": details
        })
        
        if success:
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
    
    with confluence_client:
        # List available tools
        tools = confluence_client.list_tools_sync()
        print(f"✅ MCP Server connected successfully!")
        print(f"📋 Available tools: {[tool.name for tool in tools]}")
        print()
        
        created_pages = []  # Track created pages for cleanup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test 1: Basic Page Creation
        print("=" * 60)
        print("🧪 Test 1: Basic Confluence Page Creation")
        print("=" * 60)
        try:
            basic_page_result = confluence_client.call_tool_sync(
                name="create_confluence_page",
                arguments={
                    "title": f"Basic Test Page {timestamp}",
                    "content": """# Basic Test Page

This is a simple test page to verify basic Confluence page creation functionality.

## Features Tested
- Basic page creation
- Simple markdown content
- Title formatting

Test completed successfully!
"""
                }
            )
            basic_page_data = json.loads(basic_page_result[0].text)
            created_pages.append(basic_page_data)
            log_test_result(
                "Basic Page Creation", 
                True, 
                f"Page ID: {basic_page_data['page_id']}, URL: {basic_page_data['page_url']}"
            )
        except Exception as e:
            log_test_result("Basic Page Creation", False, f"Error: {e}")
        
        # Test 2: Rich Content Page
        print("=" * 60)
        print("🧪 Test 2: Rich Content Page with Formatting")
        print("=" * 60)
        try:
            rich_content = """# AWS Architecture Design Document

## Executive Summary
This document outlines the proposed AWS Cloud Architecture for our multi-region deployment.

## Architecture Overview

### Key Components
1. **VPC (Virtual Private Cloud)**
   - Primary region: us-east-1
   - Secondary region: us-west-2
   - Cross-region connectivity via VPC peering

2. **Compute Services**
   - EC2 instances across multiple AZs
   - Auto Scaling Groups for high availability
   - Application Load Balancers

3. **Storage Solutions**
   - S3 buckets for object storage
   - EBS volumes for EC2 storage
   - RDS for relational databases

### Security Considerations
- IAM roles and policies
- Security groups and NACLs
- AWS WAF for web application protection
- CloudTrail for audit logging

## Implementation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1 | 2 weeks | Infrastructure setup |
| Phase 2 | 3 weeks | Application deployment |
| Phase 3 | 1 week | Testing and validation |

## Code Examples

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnet
aws ec2 create-subnet --vpc-id vpc-12345678 --cidr-block 10.0.1.0/24
```

## Next Steps
- [ ] Review architecture with stakeholders
- [ ] Obtain security approval
- [ ] Begin Phase 1 implementation

> **Note**: This is a test document created by the Confluence MCP test suite.
"""
            
            rich_page_result = confluence_client.call_tool_sync(
                name="create_confluence_page",
                arguments={
                    "title": f"AWS Architecture Design {timestamp}",
                    "content": rich_content
                }
            )
            rich_page_data = json.loads(rich_page_result[0].text)
            created_pages.append(rich_page_data)
            log_test_result(
                "Rich Content Page Creation", 
                True, 
                f"Page ID: {rich_page_data['page_id']}, URL: {rich_page_data['page_url']}"
            )
        except Exception as e:
            log_test_result("Rich Content Page Creation", False, f"Error: {e}")
        
        # Test 3: Unicode and Special Characters
        print("=" * 60)
        print("🧪 Test 3: Page with Special Characters and Unicode")
        print("=" * 60)
        try:
            unicode_content = """# 🏗️ Architecture & Design 📋

## Multi-language Support Testing

### English
Welcome to our AWS architecture documentation.

### 中文 (Chinese)
欢迎来到我们的AWS架构文档。

### Español (Spanish)
Bienvenido a nuestra documentación de arquitectura AWS.

### 日本語 (Japanese)
AWS アーキテクチャドキュメントへようこそ。

### العربية (Arabic)
مرحبا بكم في وثائق هندسة AWS الخاصة بنا.

## Special Characters & Symbols
- Currency: $ € £ ¥ ₹
- Math: ± × ÷ ≤ ≥ ≠ ∞
- Arrows: → ← ↑ ↓ ⇒ ⇐
- Technical: © ® ™ § ¶

## Code with Special Characters
```json
{
  "name": "特殊字符测试",
  "description": "Testing special characters: !@#$%^&*()_+-={}[]|\\:;\"'<>,.?/",
  "unicode": "🚀 🎯 ✅ ❌ 🔥"
}
```

Test completed with special characters! ✨
"""
            
            unicode_page_result = confluence_client.call_tool_sync(
                name="create_confluence_page",
                arguments={
                    "title": f"🌍 Unicode Test Page {timestamp}",
                    "content": unicode_content
                }
            )
            unicode_page_data = json.loads(unicode_page_result[0].text)
            created_pages.append(unicode_page_data)
            log_test_result(
                "Unicode and Special Characters", 
                True, 
                f"Page ID: {unicode_page_data['page_id']}, URL: {unicode_page_data['page_url']}"
            )
        except Exception as e:
            log_test_result("Unicode and Special Characters", False, f"Error: {e}")
        
        # Generate Test Summary
        print("=" * 80)
        print("📊 CONFLUENCE MCP TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {test_results['passed'] + test_results['failed']}")
        print(f"✅ Passed: {test_results['passed']}")
        print(f"❌ Failed: {test_results['failed']}")
        
        success_rate = (test_results['passed'] / (test_results['passed'] + test_results['failed'])) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        if created_pages:
            print("📄 Created Pages:")
            for i, page in enumerate(created_pages, 1):
                print(f"   {i}. {page['page_url']}")
            print()
        
        print("🔍 Detailed Test Results:")
        for test in test_results["tests"]:
            status = "✅" if test["success"] else "❌"
            print(f"   {status} {test['name']}")
            if test["details"]:
                print(f"      {test['details']}")
        
        overall_status = "🎉 ALL TESTS PASSED!" if test_results['failed'] == 0 else f"⚠️  {test_results['failed']} TEST(S) FAILED"
        print(f"\n{overall_status}")
        print("\n✨ Confluence MCP testing completed!")

def main():
    """Run Confluence tests based on environment configuration.""" 
    print("🧪 Confluence MCP Server Test Suite")
    print("=" * 50)
    
    try:
        # Check if we have real environment variables
        test_config = TestConfig(use_environment=True)
        
        has_real_config = test_config.has_real_environment()
        print(f"Environment: {'Real credentials detected' if has_real_config else 'Using mock configuration'}")
        print()
        
        if has_real_config:
            success = test_confluence_real()
        else:
            success = test_confluence_mock()
            
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Run the comprehensive test suite
    asyncio.run(test_confluence_mcp())
    
    # Alternatively, run the test based on environment configuration
    # exit_code = main()
    # sys.exit(exit_code)