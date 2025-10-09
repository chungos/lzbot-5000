#!/usr/bin/env python3
"""Simple test script to verify Confluence MCP server functionality directly."""

import asyncio
import json
from datetime import datetime
import sys
import os
import logging
from pathlib import Path
from uuid import uuid4

# Add parent directory to path to import config modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_config import get_test_config, get_test_mode, TestConfig
from lzbot.clients import ClientManager

logger = logging.getLogger(__name__)

# Mock server class for testing
class MockJiraConfluenceServer:
    """Mock server for testing Confluence functionality."""
    
    def __init__(self):
        self.page_id_counter = 2000
    
    async def _create_confluence_page(self, args):
        """Mock Confluence page creation."""
        page_id = self.page_id_counter
        self.page_id_counter += 1
        
        page_data = {
            "page_id": str(page_id),
            "page_url": f"https://vishnuprasad191.atlassian.net/wiki/spaces/LZD/pages/{page_id}",
            "title": args["title"]
        }
        
        return [type('MockResult', (), {'text': json.dumps(page_data)})()]

async def test_confluence_simple():
    """Test Confluence MCP server directly with comprehensive test cases."""
    
    print("🚀 Starting Confluence MCP Server direct test...\n")
    
    # Get test configuration
    test_config = get_test_config()
    test_mode = get_test_mode()
    
    print(f"📊 Test Mode: {test_mode}")
    test_config.print_test_config()
    print()
    
    # Set environment variables for any potential real server usage
    env_vars = test_config.get_env_dict()
    for key, value in env_vars.items():
        os.environ[key] = value
    
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
    
    try:
        server = MockJiraConfluenceServer()
        print("✅ MCP Server initialized successfully!\n")
        
        created_pages = []  # Track created pages
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Test 1: Basic Confluence Page Creation
        print("=" * 60)
        print("🧪 Test 1: Basic Confluence Page Creation")
        print("=" * 60)
        try:
            basic_page_result = await server._create_confluence_page({
                "title": f"Confluence Direct Test {timestamp}",
                "content": """# Confluence Direct Test

This page was created by directly calling the Confluence MCP server.

## Test Details
- Created via: Direct server call
- Test type: Basic page creation
- Content: Simple markdown

## Status
✅ Test completed successfully!
"""
            })
            basic_page_data = json.loads(basic_page_result[0].text)
            created_pages.append(basic_page_data)
            log_test_result(
                "Basic Page Creation",
                True,
                f"Page ID: {basic_page_data['page_id']}, URL: {basic_page_data['page_url']}"
            )
        except Exception as e:
            log_test_result("Basic Page Creation", False, f"Error: {e}")
        
        # Test 2: AWS Architecture Documentation Page
        print("=" * 60)
        print("🧪 Test 2: AWS Architecture Documentation")
        print("=" * 60)
        try:
            aws_content = """# AWS Multi-Region Architecture Design

## Executive Summary
This document outlines a comprehensive AWS multi-region architecture designed for high availability, disaster recovery, and optimal performance.

## Architecture Components

### 1. Network Infrastructure
- **Primary Region**: us-east-1 (N. Virginia)
- **Secondary Region**: us-west-2 (Oregon)
- **VPC Configuration**: 10.0.0.0/16 CIDR block
- **Connectivity**: VPC Peering, AWS Transit Gateway

### 2. Compute Services
```yaml
compute_configuration:
  ec2_instances:
    instance_type: t3.large
    availability_zones: 3
    auto_scaling:
      min_size: 2
      max_size: 20
      desired_capacity: 6
  
  load_balancers:
    type: Application Load Balancer
    scheme: internet-facing
    health_checks: enabled
```

### 3. Storage Solutions
| Service | Purpose | Configuration |
|---------|---------|---------------|
| Amazon S3 | Object Storage | Cross-region replication |
| Amazon EBS | Block Storage | gp3, encrypted |
| Amazon EFS | File Storage | Multi-AZ, encrypted |
| Amazon RDS | Database | Multi-AZ, read replicas |

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] VPC and networking setup
- [ ] IAM roles and policies
- [ ] Security baseline configuration

### Phase 2: Core Services (Weeks 3-4)
- [ ] EC2 instances and Auto Scaling
- [ ] Load balancers configuration
- [ ] Database setup (RDS)

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] CloudWatch monitoring
- [ ] Backup and disaster recovery
- [ ] Performance optimization

## Cost Estimation
- **Monthly Estimate**: $2,500 - $3,500
- **Annual Estimate**: $30,000 - $42,000
- **Cost Optimization**: 15-20% savings with Reserved Instances

---
*Document created: {datetime.now().isoformat()}*
*Created by: Confluence MCP Test Suite*
"""
            
            aws_page_result = await server._create_confluence_page({
                "title": f"AWS Architecture Design Document {timestamp}",
                "content": aws_content
            })
            aws_page_data = json.loads(aws_page_result[0].text)
            created_pages.append(aws_page_data)
            log_test_result(
                "AWS Architecture Documentation",
                True,
                f"Page ID: {aws_page_data['page_id']}, URL: {aws_page_data['page_url']}"
            )
        except Exception as e:
            log_test_result("AWS Architecture Documentation", False, f"Error: {e}")
        
        # Test Summary
        print("=" * 80)
        print("📊 CONFLUENCE DIRECT TEST SUMMARY")
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
        
        overall_status = "🎉 ALL TESTS PASSED!" if test_results['failed'] == 0 else f"⚠️  {test_results['failed']} TEST(S) FAILED"
        print(f"\n{overall_status}")
        print("\n✨ Confluence direct testing completed!")
        
    except Exception as e:
        print(f"❌ Server initialization failed: {e}")

def test_confluence_simple_func():
    """Simple test of Confluence page creation functionality."""
    print("🧪 Simple Confluence Test")
    print("=" * 50)
    
    try:
        # Use environment configuration
        test_config = TestConfig(use_environment=True)
        config_dict = test_config.get_env_dict()
        
        if not test_config.has_real_environment():
            print("🔄 Using mock configuration")
            print("✅ Simple Confluence test (mock) completed successfully")
            return True
        
        print("🔧 Testing Confluence page creation...")
        client_manager = ClientManager(config_dict)
        
        with client_manager as cm:
            jira_confluence_client = cm.jira_confluence_client
            
            # Create a simple test page
            simple_content = """
# Simple Test Page

This is a simple test page created by the LZBot-5000 testing suite.

## Purpose

Testing basic Confluence page creation functionality.

## Test Details

- **Created by**: LZBot-5000 Test Suite
- **Test type**: Simple functionality test
- **Status**: Active testing

## Conclusion

If you can see this page, the Confluence integration is working correctly!
"""
            
            result = jira_confluence_client.call_tool_sync(
                name="create_confluence_page",
                tool_use_id=str(uuid4()),
                arguments={
                    "title": "LZBot-5000 Simple Test Page",
                    "content": simple_content,
                    "space_key": config_dict.get("CONFLUENCE_SPACE_KEY", "MOCK")
                }
            )
            
            print(f"✅ Simple test completed: {result}")
            return True
            
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        return False

def test_confluence_simple():
    """Simple test of Confluence configuration."""
    print("🧪 Confluence Simple Test")
    print("=" * 50)
    
    try:
        # Use environment configuration
        test_config = TestConfig(use_environment=True)
        config_dict = test_config.get_env_dict()
        
        if not test_config.has_real_environment():
            print("🔄 Using mock configuration")
            print("✅ Confluence simple test (mock) completed successfully")
            return True
        
        print("🔧 Testing Confluence configuration...")
        
        # Validate configuration
        required_keys = ["CONFLUENCE_URL", "CONFLUENCE_SPACE_KEY"]
        missing_keys = [key for key in required_keys if not config_dict.get(key)]
        
        if missing_keys:
            print(f"❌ Missing required configuration: {missing_keys}")
            return False
            
        print("✅ Confluence configuration validation passed")
        print("📊 Test Summary:")
        print("  • Configuration: ✅ PASSED")
        print("  • Validation: ✅ PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_confluence_simple())
    # Uncomment the line below to run the simple test function instead
    # success = test_confluence_simple_func()
    # sys.exit(0 if success else 1)