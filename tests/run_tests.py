#!/usr/bin/env python3
"""
Comprehensive test runner for LZBot-5000
Provides organized test execution with multiple modes and reporting.
"""

import os
import sys
import asyncio
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_config import TestConfig, get_test_mode, check_environment_availability

class TestRunner:
    """Comprehensive test runner for LZBot-5000."""
    
    def __init__(self):
        self.test_config = TestConfig()
        self.test_files = {
            'jira': ['test_jira_mcp.py', 'test_jira_simple.py'],
            'confluence': [
                'test_confluence_mcp.py', 
                'test_confluence_simple.py',
                'test_confluence_integration.py',
                'test_confluence_edge_cases.py',
                'test_confluence_attachment.py'
            ],
            'config': ['test_config.py']
        }
        self.results = {}
    
    def print_banner(self):
        """Print test runner banner."""
        print("🧪 LZBot-5000 Test Runner")
        print("=" * 50)
        print(f"Test Mode: {get_test_mode()}")
        print(f"Environment: {'Available' if check_environment_availability() else 'Mock'}")
        print()
    
    async def run_test_file(self, test_file: str) -> Dict:
        """Run a single test file and return results."""
        test_path = Path(__file__).parent / test_file
        
        if not test_path.exists():
            return {
                'file': test_file,
                'status': 'error',
                'message': f'Test file not found: {test_path}',
                'passed': 0,
                'failed': 0,
                'duration': 0
            }
        
        print(f"🔍 Running {test_file}...")
        start_time = time.time()
        
        try:
            # Import and run the test module
            spec = __import__(f'tests.{test_file[:-3]}', fromlist=['main'])
            
            # Look for different possible function names
            test_function = None
            for func_name in ['main', f'test_{test_file[5:-3]}', 'run_tests']:
                if hasattr(spec, func_name):
                    test_function = getattr(spec, func_name)
                    break
            
            if test_function:
                if asyncio.iscoroutinefunction(test_function):
                    await test_function()
                else:
                    test_function()
                    
                duration = time.time() - start_time
                return {
                    'file': test_file,
                    'status': 'completed',
                    'message': 'Test completed successfully',
                    'passed': 1,  # We'll update this if we can get actual counts
                    'failed': 0,
                    'duration': duration
                }
            else:
                # Try to run the file directly as a script
                import subprocess
                result = subprocess.run([
                    sys.executable, str(test_path)
                ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
                
                duration = time.time() - start_time
                if result.returncode == 0:
                    return {
                        'file': test_file,
                        'status': 'completed',
                        'message': 'Test completed successfully',
                        'passed': 1,
                        'failed': 0,
                        'duration': duration
                    }
                else:
                    return {
                        'file': test_file,
                        'status': 'error',
                        'message': f'Script failed: {result.stderr}',
                        'passed': 0,
                        'failed': 1,
                        'duration': duration
                    }
        
        except Exception as e:
            return {
                'file': test_file,
                'status': 'error',
                'message': str(e),
                'passed': 0,
                'failed': 1,
                'duration': time.time() - start_time
            }
    
    async def run_test_category(self, category: str) -> List[Dict]:
        """Run all tests in a category."""
        if category not in self.test_files:
            print(f"❌ Unknown test category: {category}")
            return []
        
        print(f"\n📂 Running {category.upper()} tests...")
        print("-" * 30)
        
        results = []
        for test_file in self.test_files[category]:
            result = await self.run_test_file(test_file)
            results.append(result)
            
            # Print immediate result
            status_icon = "✅" if result['status'] == 'completed' else "❌"
            print(f"{status_icon} {test_file}: {result['message']} ({result['duration']:.2f}s)")
        
        return results
    
    async def run_all_tests(self) -> Dict:
        """Run all tests in all categories."""
        print("\n🔄 Running ALL tests...")
        print("=" * 30)
        
        all_results = {}
        for category in self.test_files.keys():
            category_results = await self.run_test_category(category)
            all_results[category] = category_results
        
        return all_results
    
    def print_summary(self, results: Dict):
        """Print test results summary."""
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        total_passed = 0
        total_failed = 0
        total_duration = 0
        
        for category, category_results in results.items():
            category_passed = sum(r['passed'] for r in category_results)
            category_failed = sum(r['failed'] for r in category_results)
            category_duration = sum(r['duration'] for r in category_results)
            
            total_passed += category_passed
            total_failed += category_failed
            total_duration += category_duration
            
            success_rate = (category_passed / (category_passed + category_failed) * 100) if (category_passed + category_failed) > 0 else 0
            
            print(f"\n📂 {category.upper()}")
            print(f"   Tests: {len(category_results)}")
            print(f"   Passed: {category_passed}")
            print(f"   Failed: {category_failed}")
            print(f"   Success Rate: {success_rate:.1f}%")
            print(f"   Duration: {category_duration:.2f}s")
            
            # Show failed tests
            failed_tests = [r for r in category_results if r['status'] == 'error']
            if failed_tests:
                print(f"   Failed Tests:")
                for test in failed_tests:
                    print(f"     ❌ {test['file']}: {test['message']}")
        
        # Overall summary
        total_tests = total_passed + total_failed
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_failed}")
        print(f"   Success Rate: {overall_success_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.2f}s")
        
        # Final status
        if total_failed == 0:
            print(f"\n🎉 All tests passed! ✅")
        else:
            print(f"\n⚠️  {total_failed} test(s) failed ❌")
    
    def print_help(self):
        """Print help information."""
        print("🧪 LZBot-5000 Test Runner Help")
        print("=" * 50)
        print()
        print("Usage: python3 tests/run_tests.py [category]")
        print()
        print("Categories:")
        for category, files in self.test_files.items():
            print(f"  {category:<12} - {', '.join(files)}")
        print(f"  all         - Run all test categories")
        print()
        print("Examples:")
        print("  python3 tests/run_tests.py jira          # Run only JIRA tests")
        print("  python3 tests/run_tests.py confluence    # Run only Confluence tests")
        print("  python3 tests/run_tests.py all           # Run all tests")
        print("  python3 tests/run_tests.py               # Interactive mode")
        print()
        print("Environment:")
        print("  Set TEST_MODE=real to use real API connections")
        print("  Set TEST_MODE=mock to use mock connections (default)")
        print("  Configure credentials in .env file")

async def main():
    """Main test runner function."""
    runner = TestRunner()
    runner.print_banner()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        
        if category in ['help', '--help', '-h']:
            runner.print_help()
            return
        
        if category == 'all':
            results = await runner.run_all_tests()
        elif category in runner.test_files:
            results = {category: await runner.run_test_category(category)}
        else:
            print(f"❌ Unknown category: {category}")
            runner.print_help()
            return
    else:
        # Interactive mode
        print("📋 Available test categories:")
        categories = list(runner.test_files.keys()) + ['all']
        for i, category in enumerate(categories, 1):
            files = runner.test_files.get(category, ['All test categories'])
            print(f"  {i}. {category:<12} - {', '.join(files) if category != 'all' else 'All test categories'}")
        
        print("\nSelect a category to run:")
        choice = input(f"Choice [1-{len(categories)}] or 'help': ").strip()
        
        if choice.lower() in ['help', 'h']:
            runner.print_help()
            return
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(categories):
                category = categories[choice_idx]
                if category == 'all':
                    results = await runner.run_all_tests()
                else:
                    results = {category: await runner.run_test_category(category)}
            else:
                print("❌ Invalid choice")
                return
        except ValueError:
            print("❌ Invalid choice")
            return
    
    # Print summary
    runner.print_summary(results)

if __name__ == "__main__":
    asyncio.run(main())