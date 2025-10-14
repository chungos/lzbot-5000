from strands.models import BedrockModel
from strands import Agent

import logging
import os
from datetime import datetime
import re
import shutil
from mcp_client_manager import MCPClientManager
from mcp_config import MCPConfigManager

logging.getLogger("strands").setLevel(logging.INFO)

# Enhanced logging configuration for comprehensive monitoring
def setup_enhanced_logging():
    """Set up comprehensive logging for MCP operations and monitoring."""
    import sys
    from datetime import datetime
    
    # Create logs directory if it doesn't exist
    os.makedirs("./logs", exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s | %(name)s | %(message)s'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler with simple format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # File handler with detailed format
    log_filename = f"./logs/mcp_operations_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Error file handler
    error_log_filename = f"./logs/mcp_errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_filename)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Set specific logger levels for detailed monitoring
    logging.getLogger("mcp_client_manager").setLevel(logging.DEBUG)
    logging.getLogger("mcp_error_handling").setLevel(logging.DEBUG)
    logging.getLogger("mcp_monitoring").setLevel(logging.DEBUG)
    logging.getLogger("output_processor").setLevel(logging.INFO)
    
    # Get logger for this module
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"Enhanced logging configured - logs saved to ./logs/")
    module_logger.info(f"Operations log: {log_filename}")
    module_logger.info(f"Error log: {error_log_filename}")

# Set up enhanced logging
setup_enhanced_logging()

logger = logging.getLogger(__name__)

bedrock_model = BedrockModel(
    model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="ap-southeast-2",
)

# Initialize MCP client manager
config_manager = MCPConfigManager()
client_manager = MCPClientManager(config_manager)


def extract_diagram_path(agent_result):
    """Extract diagram path from agent result."""
    result_str = str(agent_result)

    # Look for explicit diagram path
    for line in result_str.split("\n"):
        if "The diagram is saved at:" in line:
            return line.split("The diagram is saved at:")[1].strip()

    # Fallback: search for diagram file patterns
    diagram_pattern = r"([^\s]+\.(?:png|jpg|jpeg|svg|pdf))"
    matches = re.findall(diagram_pattern, result_str, re.IGNORECASE)
    return matches[0] if matches else None


def handle_diagram_file(original_path, target_dir):
    """Handle diagram file movement and return local path."""
    if not original_path:
        return None

    filename = os.path.basename(original_path)
    local_path = os.path.join(target_dir, filename)

    # If file already exists locally, use it
    if os.path.exists(local_path):
        print(f" Diagram already exists at: {local_path}")
        return local_path

    # Try to copy from original location
    if os.path.exists(original_path):
        try:
            shutil.copy2(original_path, local_path)
            print(f" Moved diagram from {original_path} to {local_path}")
            return local_path
        except Exception as e:
            print(f" Warning: Could not move diagram file: {e}")
            return original_path

    print(f" Warning: Diagram file not found at {original_path}")
    return None


def create_markdown_content(query, agent_result, diagram_path):
    """Create enhanced markdown content with cost estimates and documentation references."""
    try:
        from output_processor import OutputProcessor
        from enhanced_markdown_generator import create_enhanced_markdown_content
        
        # Process the agent result to extract enhanced information
        logger.info("Processing agent result for enhanced markdown generation")
        processor = OutputProcessor()
        processed_output = processor.process_agent_result(str(agent_result))
        
        # Override diagram path if provided (for backward compatibility)
        if diagram_path:
            processed_output.diagram_path = diagram_path
            logger.info(f"Using provided diagram path: {diagram_path}")
        
        # Generate enhanced markdown content
        logger.info("Generating enhanced markdown content with all extracted information")
        return create_enhanced_markdown_content(query, processed_output)
    except Exception as e:
        logger.warning(f"Error creating enhanced markdown content: {e}")
        # Fallback to basic markdown content
        degradation_strategy = client_manager.get_degradation_strategy()
        logger.info("Falling back to basic markdown content generation")
        return _create_basic_markdown_content(query, str(agent_result), degradation_strategy)

def _create_basic_markdown_content(query, agent_result, degradation_strategy):
    """Create basic markdown content when enhanced processing fails."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""# AWS Architecture Design

**Generated on:** {timestamp}
**Query:** {query}

## System Status
- **Mode:** {degradation_strategy['mode']}
- **Available Features:** {', '.join(degradation_strategy.get('available_features', ['basic text response']))}

"""
    
    # Add warnings if any
    if degradation_strategy.get('warnings'):
        content += "## Service Limitations\n"
        for warning in degradation_strategy['warnings']:
            content += f"- ⚠️ {warning}\n"
        content += "\n"
    
    # Add the agent result
    content += "## Architecture Design\n\n"
    content += str(agent_result)
    content += "\n\n---\n"
    content += f"*Generated in {degradation_strategy['mode']} mode due to service limitations*\n"
    
    return content


def _get_basic_system_prompt():
    """Get basic system prompt for fallback mode when no MCP tools are available."""
    return """
You are an expert AWS Solutions Architect with deep knowledge of the AWS Well-Architected Framework.

**IMPORTANT**: You are currently operating in basic mode due to service unavailability. 
You do not have access to diagram generation, real-time AWS documentation, or pricing tools.

Your role is to provide text-based architectural guidance based on your training knowledge:
- Design AWS Landing Zones using established best practices
- Reference AWS Well-Architected Framework principles
- Provide general cost considerations based on typical AWS pricing patterns
- Suggest implementation approaches using standard AWS services
"""

def _get_enhanced_system_prompt(degradation_strategy):
    """Get enhanced system prompt based on available services and degradation strategy."""
    base_prompt = """
You are an expert AWS Solutions Architect with deep knowledge of the AWS Well-Architected Framework"""
    
    # Add available capabilities
    capabilities = []
    available_features = degradation_strategy.get('available_features', [])
    
    if 'diagram_generation' in available_features:
        capabilities.append("1. **AWS Diagram Generation**: Create professional architecture diagrams")
    if 'documentation_access' in available_features:
        capabilities.append("2. **Real-time AWS Documentation**: Access current AWS service documentation, best practices, and limitations")
    if 'cost_estimation' in available_features:
        capabilities.append("3. **AWS Pricing Information**: Provide accurate cost estimates and optimization recommendations")
    
    if capabilities:
        base_prompt += f" and access to:\n\n{chr(10).join(capabilities)}\n\n"
    else:
        base_prompt += ".\n\n**IMPORTANT**: You are operating in degraded mode with limited tool access.\n\n"
    
    # Add warnings about unavailable services
    warnings = degradation_strategy.get('warnings', [])
    if warnings:
        base_prompt += "**Service Limitations**:\n"
        for warning in warnings:
            base_prompt += f"- {warning}\n"
        base_prompt += "\n"
    
    base_prompt += """Your primary role is to design robust, secure, scalable, and cost-effective AWS Landing Zones for new and existing cloud environments."""
    
    return base_prompt + SYSTEM_PROMPT_CONTINUATION

SYSTEM_PROMPT_CONTINUATION = """

## Enhanced Design Process

When a user requests a landing zone design, your enhanced process is as follows:

**Requirement Gathering**: Ask clarifying questions to understand the user's specific business needs,
compliance requirements (e.g., HIPAA, PCI DSS), technical constraints, desired account structure, and budget considerations.

**Knowledge-Informed Design**: 
- Use AWS Knowledge tools to verify current service capabilities, regional availability, and limitations (if available)
- Reference official AWS documentation for the most up-to-date best practices (if available)
- Validate service configurations against current AWS specifications (if available)
- Ensure compliance with the latest AWS security and operational guidelines

**Cost-Conscious Architecture**: 
- Use AWS Pricing tools to estimate costs for all recommended services (if available)
- Provide monthly cost estimates broken down by service category (if available)
- Include cost optimization strategies and alternative configurations
- Consider Reserved Instance and Savings Plan opportunities where applicable

**Well-Architected Design**: Design architecture that strictly adheres to the five pillars of the Well-Architected Framework: 
Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization.
Every design decision must be justified by one or more of these pillars and supported by current AWS documentation.

## Enhanced Output Generation

Provide the design in a comprehensive output format based on available capabilities:

**1. Textual Design**: A detailed, step-by-step description of the architecture covering:
- Account organization (AWS Organizations) with current service limits
- Networking (VPCs, Transit Gateway) with regional considerations
- Security controls (Control Tower, SCPs) based on current best practices
- Identity management (IAM) following latest security guidelines
- Logging/monitoring (CloudTrail, CloudWatch) with cost implications

**2. Cost Analysis** (if pricing tools available): 
- Detailed monthly cost estimates for all services
- Cost breakdown by service category and account
- Cost optimization recommendations with potential savings
- Comparison of alternative configurations where applicable

**3. Documentation References** (if knowledge tools available):
- Cite specific AWS documentation used in design decisions
- Reference relevant AWS Well-Architected Framework whitepapers
- Include links to AWS best practice guides and implementation resources

**4. Visual Diagrams** (if diagram tools available): Generate clear, professional diagrams to visually represent the architecture.
The diagram should show resource flow, account relationships, key services, and cost centers.

**5. Implementation Backlog**: Create a prioritized backlog of stories with:
- T-shirt sizing (Large, Medium, Small)
- Cost implications for each story (if pricing available)
- Definition of done including cost validation (if pricing available)
- 2-week sprint organization with budget tracking

## Guidelines for Tool Usage

**When using AWS Knowledge tools** (if available):
- Always verify service availability in the target region
- Check current service limits and quotas
- Reference the most recent best practice documentation
- Validate security and compliance requirements

**When using AWS Pricing tools** (if available):
- Provide estimates in the user's preferred currency (default: USD)
- Include both on-demand and reserved pricing where applicable
- Consider data transfer costs between regions and services
- Factor in operational costs (support, monitoring, backup)

**When generating diagrams** (if available):
- Include cost annotations for major service components
- Show data flow patterns that impact pricing
- Highlight cost optimization opportunities visually

## Professional Standards

Maintain a professional, knowledgeable, and helpful tone. Always:
- Explain rationale behind design choices with documentation references (when available)
- Provide cost justification for architectural decisions (when pricing available)
- Offer alternative approaches with cost-benefit analysis
- Include specific implementation guidance with current service capabilities (when available)
- Clearly communicate any service limitations affecting your recommendations

You are a consultant providing expert guidance. Continue to iterate on designs based on user feedback, 
always incorporating the latest AWS knowledge and accurate cost information when tools are available.

**Technical Requirements**:
- Default region: ap-southeast-2
- Always provide full file paths for generated diagrams: "The diagram is saved at: <filepath>" (when diagram tools available)
- Save diagrams to ./outputs directory with descriptive filenames (when diagram tools available)
- Include cost estimates in all architectural recommendations (when pricing tools available)
- Reference specific AWS documentation in design explanations (when knowledge tools available)
"""

# Initialize SYSTEM_PROMPT with default enhanced configuration
SYSTEM_PROMPT = _get_enhanced_system_prompt({'available_features': ['diagram_generation', 'documentation_access', 'cost_estimation'], 'warnings': []})

# Set up diagram output directory
diagram_dir = "./outputs"
os.makedirs(diagram_dir, exist_ok=True)

def validate_integration():
    """Validate that all components are properly integrated and working."""
    logger.info("Validating system integration...")
    
    validation_results = {
        'mcp_client_manager': False,
        'output_processor': False,
        'enhanced_markdown_generator': False,
        'agent_initialization': False,
        'tool_aggregation': False
    }
    
    try:
        # Test MCP Client Manager
        if client_manager and hasattr(client_manager, 'get_all_tools'):
            validation_results['mcp_client_manager'] = True
            logger.info("✅ MCP Client Manager: OK")
        else:
            logger.error("❌ MCP Client Manager: Failed")
        
        # Test Output Processor
        try:
            from output_processor import OutputProcessor
            processor = OutputProcessor()
            if hasattr(processor, 'process_agent_result'):
                validation_results['output_processor'] = True
                logger.info("✅ Output Processor: OK")
            else:
                logger.error("❌ Output Processor: Missing required methods")
        except ImportError as e:
            logger.error(f"❌ Output Processor: Import failed - {e}")
        
        # Test Enhanced Markdown Generator
        try:
            from enhanced_markdown_generator import create_enhanced_markdown_content
            validation_results['enhanced_markdown_generator'] = True
            logger.info("✅ Enhanced Markdown Generator: OK")
        except ImportError as e:
            logger.error(f"❌ Enhanced Markdown Generator: Import failed - {e}")
        
        # Test tool aggregation
        try:
            all_tools = client_manager.get_all_tools()
            validation_results['tool_aggregation'] = True
            logger.info(f"✅ Tool Aggregation: OK ({len(all_tools)} tools available)")
        except Exception as e:
            logger.error(f"❌ Tool Aggregation: Failed - {e}")
        
    except Exception as e:
        logger.error(f"Integration validation failed: {e}")
    
    # Report validation summary
    passed = sum(validation_results.values())
    total = len(validation_results)
    logger.info(f"Integration validation: {passed}/{total} components validated successfully")
    
    if passed == total:
        logger.info("🎉 All components integrated successfully!")
    else:
        logger.warning(f"⚠️ {total - passed} components failed validation - system may run in degraded mode")
    
    return validation_results

def initialize_agent():
    """Initialize agent with all available MCP clients and enhanced system prompt."""
    try:
        # Validate integration before proceeding
        validation_results = validate_integration()
        
        # Initialize all MCP clients
        logger.info("Initializing MCP clients...")
        client_manager.initialize_clients()
        
        # Get all available tools
        all_tools = client_manager.get_all_tools()
        
        # Log client status and capabilities
        available_clients = client_manager.get_available_clients()
        logger.info(f"Available MCP clients: {available_clients}")
        logger.info(f"Total tools available: {len(all_tools)}")
        
        # Log specific tool categories for debugging
        tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in all_tools]
        logger.info(f"Available tools: {tool_names}")
        
        # Implement graceful degradation logic
        health = client_manager.health_check()
        degradation_strategy = client_manager.get_degradation_strategy()
        
        # Log degradation status and warnings
        if health["overall_status"] != "healthy":
            logger.warning(f"System running in degraded mode: {health['overall_status']}")
            for client, status in health["clients"].items():
                if status["status"] != "healthy":
                    logger.warning(f"  {client}: {status['status']} - {status.get('error', 'Unknown error')}")
            
            # Log degradation strategy
            logger.info(f"Degradation mode: {degradation_strategy['mode']}")
            logger.info(f"Available features: {degradation_strategy['available_features']}")
            
            # Display user warnings
            for warning in degradation_strategy['warnings']:
                logger.warning(f"User warning: {warning}")
        
        # Enhanced validation with graceful degradation
        if len(all_tools) == 0:
            # Check if we can provide basic functionality
            if degradation_strategy['mode'] == 'basic':
                logger.warning("No MCP tools available - falling back to basic agent functionality")
                # Create agent without tools for basic text responses
                agent = Agent(tools=[], model=bedrock_model, system_prompt=_get_basic_system_prompt())
                logger.info("Agent initialized in basic mode (no MCP tools)")
                validation_results['agent_initialization'] = True
                return agent
            else:
                raise RuntimeError("No MCP tools available - cannot initialize agent")
        
        # Create agent with enhanced system prompt and available tools
        logger.info("Creating agent with enhanced system prompt...")
        enhanced_prompt = _get_enhanced_system_prompt(degradation_strategy)
        agent = Agent(tools=all_tools, model=bedrock_model, system_prompt=enhanced_prompt)
        
        # Log successful initialization with capability summary
        capabilities = []
        if "aws-diag" in available_clients:
            capabilities.append("diagram generation")
        if "aws-knowledge" in available_clients:
            capabilities.append("AWS documentation access")
        if "aws-pricing" in available_clients:
            capabilities.append("cost estimation")
        
        logger.info(f"Agent initialized successfully with capabilities: {', '.join(capabilities) if capabilities else 'basic functionality only'}")
        
        # Log any fallback actions that will be taken
        for action in degradation_strategy.get('fallback_actions', []):
            logger.info(f"Fallback action: {action}")
        
        validation_results['agent_initialization'] = True
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        
        # Provide specific guidance based on the error
        if "No MCP tools available" in str(e):
            logger.error("Ensure at least one MCP server is properly configured and running")
        elif "connection" in str(e).lower():
            logger.error("Check MCP server connections and network connectivity")
        else:
            logger.error("Check MCP server configurations and system requirements")
        
        raise RuntimeError(f"Agent initialization failed: {e}") from e

# Initialize the agent with error handling
try:
    agent = initialize_agent()
except RuntimeError as e:
    logger.error(f"Critical error during agent initialization: {e}")
    logger.error("Please check MCP server configurations and try again")
    raise

def run_design_query():
    """Run the main design query and generate documentation with graceful degradation."""
    query = (
        "Design a real-world AWS cloudWAN network across Melbourne and Sydney "
        "regions that must have centralised packet inspection, decentralised egress, centralied ingress"
        "that will host web applications which serves thousands of users with low latency, strong security controls, and predictable costs."
        "Networks are to be split via CloudWAN into network segments for secure, standard workloads"
    )

    print(f"Sending query to agent: {query}\n")

    try:
        # Verify agent is properly initialized before execution
        if not agent:
            raise RuntimeError("Agent not properly initialized")
        
        # Get current system status and degradation strategy
        health = client_manager.health_check()
        degradation_strategy = client_manager.get_degradation_strategy()
        available_clients = client_manager.get_available_clients()
        
        logger.info(f"Executing query with clients: {available_clients}")
        logger.info(f"System mode: {degradation_strategy['mode']}")
        
        # Display user warnings about service limitations
        for warning in degradation_strategy.get('warnings', []):
            print(f"⚠️  {warning}")
        
        # Use the client manager context to ensure all MCP clients are properly managed
        with client_manager:
            logger.info("Sending query to agent with available capabilities...")
            
            # Track the overall query execution performance
            with client_manager.monitor.track_operation("agent_query_execution", "main", query_length=len(query)):
                agent_result = agent(query)

            # Process output based on available services
            original_diagram_path = None
            local_diagram_path = None
            
            # Only attempt diagram processing if diagram service is available
            if 'diagram_generation' in degradation_strategy.get('available_features', []):
                original_diagram_path = extract_diagram_path(agent_result)
                local_diagram_path = handle_diagram_file(original_diagram_path, diagram_dir)
            else:
                print("📝 Diagram generation unavailable - providing text-based design only")

            # Generate markdown documentation with graceful degradation
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            markdown_filename = f"aws_design_{timestamp}.md"
            markdown_path = os.path.join(diagram_dir, markdown_filename)

            try:
                # Generate enhanced markdown content using integrated components
                logger.info("Creating enhanced markdown documentation with all available information")
                markdown_content = create_markdown_content(query, agent_result, local_diagram_path)
                
                # Add comprehensive service status information to markdown
                markdown_content += f"\n\n## Service Status and Integration Report\n"
                markdown_content += f"- **System Mode**: {degradation_strategy['mode']}\n"
                markdown_content += f"- **Available Features**: {', '.join(degradation_strategy.get('available_features', ['basic text response']))}\n"
                markdown_content += f"- **Active MCP Clients**: {', '.join(available_clients) if available_clients else 'None'}\n"
                
                # Add detailed client status
                client_status = client_manager.get_client_status()
                markdown_content += f"\n### MCP Client Status\n"
                for client_name, status in client_status.items():
                    status_icon = "✅" if status else "❌"
                    markdown_content += f"- {status_icon} **{client_name.title()}**: {'Connected' if status else 'Disconnected'}\n"
                
                if degradation_strategy.get('warnings'):
                    markdown_content += f"\n### Service Limitations\n"
                    for warning in degradation_strategy['warnings']:
                        markdown_content += f"- ⚠️ {warning}\n"
                
                # Add integration validation
                markdown_content += f"\n### Integration Validation\n"
                all_tools = client_manager.get_all_tools()
                markdown_content += f"- **Total Tools Available**: {len(all_tools)}\n"
                markdown_content += f"- **Enhanced Processing**: {'✅ Active' if len(all_tools) > 0 else '❌ Unavailable'}\n"
                markdown_content += f"- **Output Processing**: ✅ Active\n"
                
                markdown_content += f"\n**Documentation saved at:** `{markdown_path}`\n"
                
            except Exception as e:
                logger.warning(f"Error creating enhanced markdown content: {e}")
                # Fallback to basic markdown content with error details
                logger.info("Using fallback markdown generation due to processing error")
                markdown_content = _create_basic_markdown_content(query, str(agent_result), degradation_strategy)
                markdown_content += f"\n\n### Processing Error\n"
                markdown_content += f"- ⚠️ Enhanced processing failed: {str(e)}\n"
                markdown_content += f"- Using basic markdown generation as fallback\n"

            # Save markdown file
            try:
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                print(f"\n{'=' * 60}")
                print(f"Design documentation saved successfully!")
                print(f"Markdown file: {markdown_path}")
                if local_diagram_path:
                    print(f"Diagram file: {local_diagram_path}")
                
                # Display capability summary with degradation info
                capabilities_used = []
                if "aws-diag" in available_clients:
                    capabilities_used.append("✓ Diagram generation")
                else:
                    capabilities_used.append("✗ Diagram generation (unavailable)")
                    
                if "aws-knowledge" in available_clients:
                    capabilities_used.append("✓ AWS documentation")
                else:
                    capabilities_used.append("✗ AWS documentation (unavailable)")
                    
                if "aws-pricing" in available_clients:
                    capabilities_used.append("✓ Cost estimation")
                else:
                    capabilities_used.append("✗ Cost estimation (unavailable)")
                
                print(f"Service status: {', '.join(capabilities_used)}")
                
                # Display system health
                if health["overall_status"] == "healthy":
                    print("🟢 All services operational")
                elif health["overall_status"] == "degraded":
                    print("🟡 Running in degraded mode - some services unavailable")
                else:
                    print("🔴 Critical services unavailable - limited functionality")
                
                # Display performance summary
                performance_metrics = client_manager.get_performance_metrics()
                if performance_metrics['last_hour']['total_operations'] > 0:
                    last_hour = performance_metrics['last_hour']
                    print(f"📊 Performance (last hour): {last_hour['total_operations']} operations, "
                          f"{last_hour['success_rate']:.1f}% success rate, "
                          f"{last_hour['average_duration']:.2f}s avg duration")
                
                print(f"{'=' * 60}")

            except Exception as e:
                logger.error(f"Error saving markdown file: {e}")
                print(f"Agent result: {agent_result}")
            
    except Exception as e:
        logger.error(f"Error during design query execution: {e}")
        
        # Enhanced error handling with graceful degradation
        health = client_manager.health_check()
        error_summary = client_manager.get_error_summary()
        
        if health["overall_status"] != "healthy":
            logger.error("MCP client health issues detected:")
            for client, status in health["clients"].items():
                if status["status"] != "healthy":
                    logger.error(f"  {client}: {status['status']}")
            
            # Display error summary
            if error_summary["total_errors"] > 0:
                logger.error(f"Total errors encountered: {error_summary['total_errors']}")
                logger.error(f"Clients affected: {error_summary['clients_affected']}")
                for error_type, count in error_summary.get('error_types', {}).items():
                    logger.error(f"  {error_type}: {count} occurrences")
            
            # Attempt recovery or suggest fallback
            available_clients = client_manager.get_available_clients()
            if available_clients:
                logger.info(f"Attempting to continue with available services: {available_clients}")
                # Could implement retry logic here
            else:
                logger.error("No MCP services available - system cannot provide enhanced functionality")
                print("💡 Suggestion: Check MCP server configurations and restart services")
        
        raise

# Run the design query
if __name__ == "__main__":
    run_design_query()


def export_monitoring_report():
    """Export comprehensive monitoring report for analysis."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export monitoring data
        monitoring_file = f"./logs/monitoring_data_{timestamp}.json"
        client_manager.export_monitoring_data(monitoring_file)
        
        # Export detailed health report
        health_report = client_manager.get_detailed_health_report()
        health_file = f"./logs/health_report_{timestamp}.json"
        
        import json
        with open(health_file, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        
        logger.info(f"Monitoring reports exported:")
        logger.info(f"  Monitoring data: {monitoring_file}")
        logger.info(f"  Health report: {health_file}")
        
        return monitoring_file, health_file
        
    except Exception as e:
        logger.error(f"Failed to export monitoring reports: {e}")
        return None, None

def cleanup_old_logs():
    """Clean up old log files and monitoring data."""
    try:
        # Clear old metrics (older than 24 hours)
        client_manager.clear_old_metrics(24)
        
        # Clean up old log files (older than 7 days)
        import glob
        from pathlib import Path
        
        log_files = glob.glob("./logs/*.log")
        current_time = time.time()
        
        for log_file in log_files:
            file_age = current_time - os.path.getmtime(log_file)
            if file_age > (7 * 24 * 3600):  # 7 days in seconds
                try:
                    os.remove(log_file)
                    logger.info(f"Removed old log file: {log_file}")
                except Exception as e:
                    logger.warning(f"Could not remove old log file {log_file}: {e}")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def main():
    """Main entry point for AWS landing zone designer."""
    print("AWS Landing Zone Designer with Enhanced MCP Integration")
    print("=" * 60)
    
    try:
        # Clean up old logs at startup
        cleanup_old_logs()
        
        # Display available clients
        available_clients = client_manager.get_available_clients()
        print(f"Available MCP clients: {', '.join(available_clients) if available_clients else 'None'}")
        
        # Display initial health status
        health = client_manager.health_check()
        print(f"System health: {health['overall_status']}")
        
        # Run the design query
        run_design_query()
        
        # Export monitoring report after execution
        monitoring_file, health_file = export_monitoring_report()
        if monitoring_file and health_file:
            print(f"\n📊 Monitoring reports saved:")
            print(f"   {monitoring_file}")
            print(f"   {health_file}")
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        
        # Export error report for debugging
        try:
            error_report = client_manager.get_detailed_health_report()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = f"./logs/error_report_{timestamp}.json"
            
            import json
            with open(error_file, 'w') as f:
                json.dump(error_report, f, indent=2, default=str)
            
            print(f"🚨 Error report saved to: {error_file}")
            
        except Exception as export_error:
            logger.error(f"Failed to export error report: {export_error}")
        
        raise
