#!/usr/bin/env python3
"""
Integration test script for LZBot-5000
Quick validation of all major components after architectural updates.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from lzbot.logging_config import setup_logging, get_logger
from lzbot.exceptions import LZBotError, ConfigurationError
from config import load_config
from tests.test_config import TestConfig

def test_configuration_system():
    """Test the configuration system with both Pydantic and legacy support."""
    logger = get_logger("test.config")
    
    try:
        # Test loading configuration
        config = load_config()
        logger.info("✅ Configuration loading successful")
        
        # Test environment variables access
        if hasattr(config, 'to_env_dict'):
            env_vars = config.to_env_dict()
            logger.info("✅ Pydantic configuration system active")
        else:
            env_vars = config.get_all_env_vars()
            logger.info("✅ Legacy configuration system active")
        
        # Validate required keys
        required_keys = ['JIRA_URL', 'JIRA_EMAIL', 'CONFLUENCE_URL']
        for key in required_keys:
            if key not in env_vars:
                raise ConfigurationError(f"Missing required key: {key}")
        
        logger.info("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_logging_system():
    """Test the structured logging system."""
    logger = get_logger("test.logging")
    
    try:
        # Test different log levels
        logger.debug("Debug message test")
        logger.info("Info message test")
        logger.warning("Warning message test")
        
        logger.info("✅ Logging system functional")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


def test_exception_system():
    """Test the custom exception system."""
    logger = get_logger("test.exceptions")
    
    try:
        from lzbot.exceptions import MCPClientError, ErrorHandler
        
        # Test exception creation
        test_error = MCPClientError("Test error", client_type="test")
        
        # Test error formatting
        formatted = ErrorHandler.format_error_for_user(test_error)
        
        if "Test error" not in formatted:
            raise Exception("Error formatting failed")
        
        logger.info("✅ Exception system functional")
        return True
        
    except Exception as e:
        logger.error(f"❌ Exception test failed: {e}")
        return False


def test_imports():
    """Test that all major modules can be imported."""
    logger = get_logger("test.imports")
    
    try:
        # Test core module imports
        from lzbot import ClientManager, LZBotAgent, InputHandler, FileHandler
        logger.info("✅ Core modules import successful")
        
        # Test new modules
        from lzbot.logging_config import LZBotLogger
        from lzbot.exceptions import LZBotError
        logger.info("✅ New architecture modules import successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        return False


def test_test_framework():
    """Test the updated test framework."""
    logger = get_logger("test.framework")
    
    try:
        # Test configuration loading
        test_config = TestConfig(use_environment=False)
        env_dict = test_config.get_env_dict()
        
        if 'JIRA_URL' not in env_dict:
            raise Exception("Test configuration missing required keys")
        
        logger.info("✅ Test framework functional")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test framework test failed: {e}")
        return False


def main():
    """Run integration tests."""
    # Setup logging for tests
    setup_logging(level="INFO", include_timestamp=False)
    logger = get_logger("integration_test")
    
    print("🧪 LZBot-5000 Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration System", test_configuration_system),
        ("Logging System", test_logging_system),
        ("Exception System", test_exception_system),
        ("Module Imports", test_imports),
        ("Test Framework", test_test_framework),
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
        print("🎉 All integration tests passed!")
        logger.info("All integration tests passed successfully")
        return 0
    else:
        print("⚠️  Some tests failed - check logs for details")
        logger.warning(f"Integration tests failed: {passed}/{total} passed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)