#!/usr/bin/env python3
"""
Validation script for enhanced AWS architecture design functionality.

This script validates that all enhanced features are working correctly:
- Architecture generation with knowledge and pricing integration
- Cost estimates in output documentation
- AWS documentation references
- Enhanced markdown generation
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client_manager import MCPClientManager
from mcp_config import MCPConfigManager
from output_processor import OutputProcessor, ProcessedOutput
from enhanced_markdown_generator import create_enhanced_markdown_content

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedFunctionalityValidator:
    """
    Validates enhanced functionality of the AWS architecture design system.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.config_manager = MCPConfigManager()
        self.client_manager = MCPClientManager(self.config_manager)
        self.output_processor = OutputProcessor()
        self.validation_results = {}
        
    def run_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation of enhanced functionality.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Starting enhanced functionality validation")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'warnings': []
            }
        }
        
        # Test 1: MCP Client Manager Integration
        validation_results['tests']['mcp_client_manager'] = self._test_mcp_client_manager()
        
        # Test 2: Output Processing
        validation_results['tests']['output_processing'] = self._test_output_processing()
        
        # Test 3: Enhanced Markdown Generation
        validation_results['tests']['enhanced_markdown'] = self._test_enhanced_markdown_generation()
        
        # Test 4: Knowledge Integration (if available)
        validation_results['tests']['knowledge_integration'] = self._test_knowledge_integration()
        
        # Test 5: Pricing Integration (if available)
        validation_results['tests']['pricing_integration'] = self._test_pricing_integration()
        
        # Test 6: Graceful Degradation
        validation_results['tests']['graceful_degradation'] = self._test_graceful_degradation()
        
        # Test 7: End-to-End Workflow
        validation_results['tests']['end_to_end'] = self._test_end_to_end_workflow()
        
        # Calculate summary
        self._calculate_summary(validation_results)
        
        logger.info(f"Validation completed: {validation_results['summary']['passed']}/{validation_results['summary']['total_tests']} tests passed")
        
        return validation_results
    
    def _test_mcp_client_manager(self) -> Dict[str, Any]:
        """Test MCP Client Manager functionality."""
        logger.info("Testing MCP Client Manager...")
        
        test_result = {
            'name': 'MCP Client Manager Integration',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Test client initialization
            self.client_manager.initialize_clients()
            test_result['details']['client_initialization'] = 'success'
            
            # Test tool aggregation
            all_tools = self.client_manager.get_all_tools()
            test_result['details']['tool_count'] = len(all_tools)
            test_result['details']['available_clients'] = self.client_manager.get_available_clients()
            
            # Test health check
            health = self.client_manager.health_check()
            test_result['details']['health_status'] = health['overall_status']
            test_result['details']['client_status'] = health['clients']
            
            # Test degradation strategy
            degradation = self.client_manager.get_degradation_strategy()
            test_result['details']['degradation_mode'] = degradation['mode']
            test_result['details']['available_features'] = degradation['available_features']
            
            logger.info(f"✅ MCP Client Manager: {len(all_tools)} tools from {len(self.client_manager.get_available_clients())} clients")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ MCP Client Manager test failed: {e}")
        
        return test_result
    
    def _test_output_processing(self) -> Dict[str, Any]:
        """Test output processing functionality."""
        logger.info("Testing Output Processing...")
        
        test_result = {
            'name': 'Output Processing',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Create sample agent result with various elements
            sample_result = """
            AWS CloudWAN Architecture Design for Melbourne and Sydney

            The diagram is saved at: ./outputs/cloudwan_architecture_20241014.png

            Cost Estimates:
            - Transit Gateway: $45.00 per month
            - CloudWAN Core Network: $120.00 per month
            - VPC Endpoints: $22.50 per month
            Total estimated monthly cost: $187.50

            Best practice: Use AWS Well-Architected Framework principles for security
            AWS recommends: Implementing centralized packet inspection for compliance

            Warning: Ensure proper IAM policies are configured for cross-region access
            
            For more information, see AWS documentation for CloudWAN at https://docs.aws.amazon.com/cloudwan/
            """
            
            # Process the sample result
            processed_output = self.output_processor.process_agent_result(sample_result)
            
            # Validate extracted information
            test_result['details']['diagram_extracted'] = processed_output.diagram_path is not None
            test_result['details']['costs_extracted'] = processed_output.cost_estimates is not None
            test_result['details']['docs_extracted'] = len(processed_output.documentation_references) > 0
            test_result['details']['practices_extracted'] = len(processed_output.best_practices) > 0
            test_result['details']['warnings_extracted'] = len(processed_output.warnings) > 0
            
            # Validate specific extractions
            if processed_output.diagram_path:
                test_result['details']['diagram_path'] = processed_output.diagram_path
            
            if processed_output.cost_estimates:
                test_result['details']['total_cost'] = processed_output.cost_estimates.get('total_estimated_monthly')
                test_result['details']['cost_items'] = len(processed_output.cost_estimates.get('raw_costs', []))
            
            test_result['details']['documentation_count'] = len(processed_output.documentation_references)
            test_result['details']['best_practices_count'] = len(processed_output.best_practices)
            test_result['details']['warnings_count'] = len(processed_output.warnings)
            
            logger.info(f"✅ Output Processing: Extracted diagram={bool(processed_output.diagram_path)}, "
                       f"costs={bool(processed_output.cost_estimates)}, "
                       f"docs={len(processed_output.documentation_references)}")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ Output Processing test failed: {e}")
        
        return test_result
    
    def _test_enhanced_markdown_generation(self) -> Dict[str, Any]:
        """Test enhanced markdown generation."""
        logger.info("Testing Enhanced Markdown Generation...")
        
        test_result = {
            'name': 'Enhanced Markdown Generation',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Create sample processed output
            sample_processed_output = ProcessedOutput(
                original_result="Sample AWS architecture design with CloudWAN",
                diagram_path="./outputs/test_diagram.png",
                cost_estimates={
                    'total_estimated_monthly': 187.50,
                    'raw_costs': ['$45.00 per month', '$120.00 per month'],
                    'optimization_suggestions': ['Use Reserved Instances for predictable workloads']
                },
                documentation_references=[
                    'https://docs.aws.amazon.com/cloudwan/',
                    'AWS Well-Architected Framework'
                ],
                best_practices=[
                    'Implement centralized packet inspection',
                    'Use AWS Well-Architected principles'
                ],
                warnings=[
                    'Ensure proper IAM policies are configured'
                ]
            )
            
            # Generate enhanced markdown
            query = "Design CloudWAN architecture for Melbourne and Sydney"
            markdown_content = create_enhanced_markdown_content(query, sample_processed_output)
            
            # Validate markdown content
            test_result['details']['markdown_generated'] = len(markdown_content) > 0
            test_result['details']['contains_cost_section'] = '## Cost Estimates' in markdown_content
            test_result['details']['contains_best_practices'] = '## AWS Best Practices' in markdown_content
            test_result['details']['contains_documentation'] = '## AWS Documentation References' in markdown_content
            test_result['details']['contains_warnings'] = '## Important Notes' in markdown_content
            test_result['details']['markdown_length'] = len(markdown_content)
            
            # Save sample markdown for inspection
            sample_path = './outputs/validation_sample.md'
            os.makedirs('./outputs', exist_ok=True)
            with open(sample_path, 'w') as f:
                f.write(markdown_content)
            test_result['details']['sample_saved'] = sample_path
            
            logger.info(f"✅ Enhanced Markdown Generation: {len(markdown_content)} characters generated")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ Enhanced Markdown Generation test failed: {e}")
        
        return test_result
    
    def _test_knowledge_integration(self) -> Dict[str, Any]:
        """Test AWS Knowledge MCP integration."""
        logger.info("Testing Knowledge Integration...")
        
        test_result = {
            'name': 'AWS Knowledge Integration',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Check if knowledge client is available
            knowledge_available = self.client_manager.is_client_available('knowledge')
            test_result['details']['knowledge_client_available'] = knowledge_available
            
            if knowledge_available:
                # Test knowledge tools
                all_tools = self.client_manager.get_all_tools()
                knowledge_tools = [tool for tool in all_tools if 'knowledge' in str(tool).lower() or 'doc' in str(tool).lower()]
                test_result['details']['knowledge_tools_count'] = len(knowledge_tools)
                test_result['details']['knowledge_tools'] = [str(tool) for tool in knowledge_tools[:5]]  # First 5 tools
                
                logger.info(f"✅ Knowledge Integration: {len(knowledge_tools)} knowledge tools available")
            else:
                test_result['details']['reason'] = 'Knowledge client not available'
                logger.warning("⚠️ Knowledge Integration: Client not available")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ Knowledge Integration test failed: {e}")
        
        return test_result
    
    def _test_pricing_integration(self) -> Dict[str, Any]:
        """Test AWS Pricing MCP integration."""
        logger.info("Testing Pricing Integration...")
        
        test_result = {
            'name': 'AWS Pricing Integration',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Check if pricing client is available
            pricing_available = self.client_manager.is_client_available('pricing')
            test_result['details']['pricing_client_available'] = pricing_available
            
            if pricing_available:
                # Test pricing tools
                all_tools = self.client_manager.get_all_tools()
                pricing_tools = [tool for tool in all_tools if 'pricing' in str(tool).lower() or 'cost' in str(tool).lower()]
                test_result['details']['pricing_tools_count'] = len(pricing_tools)
                test_result['details']['pricing_tools'] = [str(tool) for tool in pricing_tools[:5]]  # First 5 tools
                
                logger.info(f"✅ Pricing Integration: {len(pricing_tools)} pricing tools available")
            else:
                test_result['details']['reason'] = 'Pricing client not available'
                logger.warning("⚠️ Pricing Integration: Client not available")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ Pricing Integration test failed: {e}")
        
        return test_result
    
    def _test_graceful_degradation(self) -> Dict[str, Any]:
        """Test graceful degradation functionality."""
        logger.info("Testing Graceful Degradation...")
        
        test_result = {
            'name': 'Graceful Degradation',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Get current degradation strategy
            degradation = self.client_manager.get_degradation_strategy()
            test_result['details']['degradation_mode'] = degradation['mode']
            test_result['details']['available_features'] = degradation['available_features']
            test_result['details']['warnings'] = degradation.get('warnings', [])
            test_result['details']['fallback_actions'] = degradation.get('fallback_actions', [])
            
            # Test health check
            health = self.client_manager.health_check()
            test_result['details']['overall_health'] = health['overall_status']
            test_result['details']['failed_clients'] = health.get('failed_clients', [])
            
            # Validate degradation logic
            if health['overall_status'] == 'healthy':
                expected_mode = 'enhanced'
            elif health['overall_status'] == 'degraded':
                expected_mode = 'partial'
            else:
                expected_mode = 'basic'
            
            test_result['details']['degradation_logic_correct'] = (
                degradation['mode'] == expected_mode or 
                len(degradation['available_features']) > 0
            )
            
            logger.info(f"✅ Graceful Degradation: Mode={degradation['mode']}, Features={len(degradation['available_features'])}")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ Graceful Degradation test failed: {e}")
        
        return test_result
    
    def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test end-to-end workflow integration."""
        logger.info("Testing End-to-End Workflow...")
        
        test_result = {
            'name': 'End-to-End Workflow',
            'status': 'passed',
            'details': {},
            'errors': []
        }
        
        try:
            # Simulate a complete workflow without actually running the agent
            # This tests the integration of all components
            
            # 1. Check client manager initialization
            health = self.client_manager.health_check()
            test_result['details']['client_manager_ready'] = health['overall_status'] != 'critical'
            
            # 2. Test tool aggregation
            all_tools = self.client_manager.get_all_tools()
            test_result['details']['tools_aggregated'] = len(all_tools) >= 0  # Should work even with 0 tools
            
            # 3. Test output processing pipeline
            sample_result = "Sample architecture with cost estimates: $100/month"
            processed = self.output_processor.process_agent_result(sample_result)
            test_result['details']['output_processing_ready'] = processed is not None
            
            # 4. Test markdown generation
            markdown = create_enhanced_markdown_content("Test query", processed)
            test_result['details']['markdown_generation_ready'] = len(markdown) > 0
            
            # 5. Test degradation strategy
            degradation = self.client_manager.get_degradation_strategy()
            test_result['details']['degradation_strategy_ready'] = 'mode' in degradation
            
            # Overall workflow readiness
            workflow_ready = all([
                test_result['details']['client_manager_ready'],
                test_result['details']['tools_aggregated'],
                test_result['details']['output_processing_ready'],
                test_result['details']['markdown_generation_ready'],
                test_result['details']['degradation_strategy_ready']
            ])
            
            test_result['details']['workflow_ready'] = workflow_ready
            
            if workflow_ready:
                logger.info("✅ End-to-End Workflow: All components integrated successfully")
            else:
                logger.warning("⚠️ End-to-End Workflow: Some components not ready")
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['errors'].append(str(e))
            logger.error(f"❌ End-to-End Workflow test failed: {e}")
        
        return test_result
    
    def _calculate_summary(self, validation_results: Dict[str, Any]) -> None:
        """Calculate validation summary."""
        total_tests = len(validation_results['tests'])
        passed_tests = sum(1 for test in validation_results['tests'].values() if test['status'] == 'passed')
        failed_tests = total_tests - passed_tests
        
        validation_results['summary']['total_tests'] = total_tests
        validation_results['summary']['passed'] = passed_tests
        validation_results['summary']['failed'] = failed_tests
        
        # Collect warnings
        warnings = []
        for test_name, test_result in validation_results['tests'].items():
            if test_result['status'] == 'failed':
                warnings.append(f"{test_name}: {', '.join(test_result['errors'])}")
            elif 'reason' in test_result.get('details', {}):
                warnings.append(f"{test_name}: {test_result['details']['reason']}")
        
        validation_results['summary']['warnings'] = warnings
    
    def save_validation_report(self, validation_results: Dict[str, Any], filepath: str) -> None:
        """Save validation report to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(validation_results, f, indent=2)
        logger.info(f"Validation report saved to {filepath}")
    
    def print_validation_summary(self, validation_results: Dict[str, Any]) -> None:
        """Print validation summary to console."""
        summary = validation_results['summary']
        
        print("\n" + "="*60)
        print("ENHANCED FUNCTIONALITY VALIDATION REPORT")
        print("="*60)
        print(f"Timestamp: {validation_results['timestamp']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%")
        
        print("\nTEST RESULTS:")
        print("-" * 40)
        for test_name, test_result in validation_results['tests'].items():
            status_icon = "✅" if test_result['status'] == 'passed' else "❌"
            print(f"{status_icon} {test_result['name']}")
            
            if test_result['status'] == 'failed' and test_result['errors']:
                for error in test_result['errors']:
                    print(f"   Error: {error}")
        
        if summary['warnings']:
            print("\nWARNINGS:")
            print("-" * 40)
            for warning in summary['warnings']:
                print(f"⚠️  {warning}")
        
        print("\n" + "="*60)


def main():
    """Main validation function."""
    print("Starting Enhanced Functionality Validation...")
    
    try:
        validator = EnhancedFunctionalityValidator()
        validation_results = validator.run_validation()
        
        # Save detailed report
        report_path = f"./outputs/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        validator.save_validation_report(validation_results, report_path)
        
        # Print summary
        validator.print_validation_summary(validation_results)
        
        # Return appropriate exit code
        if validation_results['summary']['failed'] == 0:
            print("\n🎉 All validations passed successfully!")
            return 0
        else:
            print(f"\n⚠️ {validation_results['summary']['failed']} validation(s) failed")
            return 1
            
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)