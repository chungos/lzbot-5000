#!/usr/bin/env python3
"""
Test script for input/output validation system
Validates that Pydantic models work correctly for user inputs and API responses.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lzbot.logging_config import setup_logging, get_logger
from lzbot.validation import *
from lzbot.exceptions import ValidationError


def test_user_query_validation():
    """Test UserQuery validation."""
    logger = get_logger("test.validation.user_query")
    
    # Test valid query
    try:
        valid_data = {
            'description': 'Design a multi-region AWS architecture with high availability and disaster recovery capabilities',
            'complexity': 'moderate',
            'preferred_region': 'ap-southeast-2',
            'requirements': ['HA', 'DR', 'Multi-region'],
            'compliance_requirements': ['SOX', 'gdpr']
        }
        
        query = UserQuery.model_validate(valid_data)
        logger.info(f"✅ Valid query created: {query.description[:50]}...")
        
        # Test too short description
        try:
            UserQuery.model_validate({'description': 'Too short'})
            logger.error("❌ Should have failed on short description")
            return False
        except Exception:
            logger.info("✅ Correctly rejected short description")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UserQuery validation test failed: {e}")
        return False


def test_jira_issue_validation():
    """Test JiraIssueRequest validation."""
    logger = get_logger("test.validation.jira")
    
    try:
        valid_data = {
            'summary': 'AWS Landing Zone Implementation',
            'description': 'Implement AWS Landing Zone with multi-account setup and security controls',
            'labels': ['aws', 'landing-zone', 'security']
        }
        
        issue = JiraIssueRequest.model_validate(valid_data)
        logger.info(f"✅ Valid JIRA issue created: {issue.summary}")
        
        # Test label cleaning
        dirty_data = {
            'summary': 'Test Issue',
            'description': 'Test description with enough content',
            'labels': ['valid-label', 'invalid label!', 'another_valid-label']
        }
        
        clean_issue = JiraIssueRequest.model_validate(dirty_data)
        expected_labels = ['valid-label', 'invalidlabel', 'another_valid-label']  # Updated expectation
        if clean_issue.labels == expected_labels:
            logger.info("✅ Labels cleaned correctly")
        else:
            logger.error(f"❌ Label cleaning failed: expected {expected_labels}, got {clean_issue.labels}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ JIRA validation test failed: {e}")
        return False


def test_confluence_page_validation():
    """Test ConfluencePageRequest validation."""
    logger = get_logger("test.validation.confluence")
    
    try:
        valid_data = {
            'title': 'AWS Architecture Documentation',
            'content': 'This page contains detailed AWS architecture documentation with diagrams and implementation notes.',
            'labels': ['aws', 'architecture', 'documentation']
        }
        
        page = ConfluencePageRequest.model_validate(valid_data)
        logger.info(f"✅ Valid Confluence page created: {page.title}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Confluence validation test failed: {e}")
        return False


def test_diagram_request_validation():
    """Test DiagramRequest validation."""
    logger = get_logger("test.validation.diagram")
    
    try:
        valid_data = {
            'title': 'Multi-Region AWS Architecture',
            'description': 'Diagram showing multi-region AWS setup with VPC peering and cross-region replication',
            'format': 'png'
        }
        
        diagram = DiagramRequest.model_validate(valid_data)
        logger.info(f"✅ Valid diagram request created: {diagram.title}")
        
        # Test invalid format
        try:
            DiagramRequest.model_validate({
                'title': 'Test Diagram',
                'description': 'Test description with sufficient content',
                'format': 'invalid'
            })
            logger.error("❌ Should have failed on invalid format")
            return False
        except Exception:
            logger.info("✅ Correctly rejected invalid format")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Diagram validation test failed: {e}")
        return False


def test_architecture_result_validation():
    """Test ArchitectureResult validation."""
    logger = get_logger("test.validation.result")
    
    try:
        # Create a valid UserQuery first
        query_data = {
            'description': 'Design a secure, scalable AWS architecture with multi-region capability'
        }
        user_query = UserQuery.model_validate(query_data)
        
        valid_data = {
            'query': user_query,
            'design_content': 'This is a comprehensive AWS architecture design with multiple availability zones, ' +
                             'cross-region replication, security groups, and monitoring capabilities. The architecture ' +
                             'includes VPC setup with public and private subnets, subnet configuration across multiple AZs, ' +
                             'routing tables for traffic management, and comprehensive security controls including NACLs and security groups. ' +
                             'Implementation follows AWS Well-Architected Framework principles for security, reliability, ' +
                             'performance efficiency, cost optimization, and operational excellence. The design incorporates ' +
                             'best practices for high availability, disaster recovery, and scalability requirements.'
        }
        
        result = ArchitectureResult.model_validate(valid_data)
        logger.info(f"✅ Valid architecture result created with {len(result.design_content)} characters")
        
        # Test too short content
        try:
            ArchitectureResult.model_validate({
                'query': user_query,
                'design_content': 'Too short'
            })
            logger.error("❌ Should have failed on short content")
            return False
        except Exception:
            logger.info("✅ Correctly rejected short content")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Architecture result validation test failed: {e}")
        return False


def test_safe_validation():
    """Test safe validation utility function."""
    logger = get_logger("test.validation.safe")
    
    try:
        # Test successful validation
        valid_data = {'description': 'Valid architecture description with sufficient length'}
        result, errors = safe_validate(valid_data, UserQuery)
        
        if result is None or errors is not None:
            logger.error("❌ Safe validation failed on valid data")
            return False
        
        logger.info("✅ Safe validation succeeded on valid data")
        
        # Test failed validation
        invalid_data = {'description': 'Short'}
        result, errors = safe_validate(invalid_data, UserQuery)
        
        if result is not None or errors is None:
            logger.error("❌ Safe validation should have failed on invalid data")
            return False
        
        logger.info(f"✅ Safe validation correctly failed with {len(errors)} errors")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Safe validation test failed: {e}")
        return False


def test_validation_utilities():
    """Test validation utility functions."""
    logger = get_logger("test.validation.utilities")
    
    try:
        # Test validate_architecture_query
        query = validate_architecture_query("Design a comprehensive AWS multi-region architecture")
        if not isinstance(query, UserQuery):
            logger.error("❌ validate_architecture_query failed")
            return False
        
        logger.info("✅ validate_architecture_query succeeded")
        
        # Test format_validation_errors
        errors = ["Field 'description': too short", "Field 'format': invalid value"]
        formatted = format_validation_errors(errors)
        
        if "❌ Validation Errors:" not in formatted:
            logger.error("❌ format_validation_errors failed")
            return False
        
        logger.info("✅ format_validation_errors succeeded")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation utilities test failed: {e}")
        return False


def main():
    """Run validation tests."""
    # Setup logging for tests
    setup_logging(level="INFO", include_timestamp=False)
    logger = get_logger("validation_test")
    
    print("🧪 LZBot-5000 Validation Test Suite")
    print("=" * 50)
    
    tests = [
        ("UserQuery Validation", test_user_query_validation),
        ("JIRA Issue Validation", test_jira_issue_validation),
        ("Confluence Page Validation", test_confluence_page_validation),
        ("Diagram Request Validation", test_diagram_request_validation),
        ("Architecture Result Validation", test_architecture_result_validation),
        ("Safe Validation", test_safe_validation),
        ("Validation Utilities", test_validation_utilities),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"   ❌ FAIL: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed!")
        logger.info("All validation tests passed successfully")
        return 0
    else:
        print("⚠️  Some tests failed - check logs for details")
        logger.warning(f"Validation tests failed: {passed}/{total} passed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)