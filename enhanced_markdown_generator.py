"""
Enhanced markdown documentation generator for AWS architecture designs.

This module provides functionality to generate comprehensive markdown documentation
that includes cost estimates, AWS documentation references, and best practices.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from output_processor import ProcessedOutput

logger = logging.getLogger(__name__)


class EnhancedMarkdownGenerator:
    """
    Generates enhanced markdown documentation for AWS architecture designs.
    
    This class creates comprehensive documentation that includes:
    - Architecture diagrams
    - Cost estimates and optimization suggestions
    - AWS documentation references
    - Best practices and recommendations
    - Warnings and important notes
    """
    
    def __init__(self):
        """Initialize the EnhancedMarkdownGenerator."""
        pass

    def create_enhanced_markdown_content(
        self, 
        query: str, 
        processed_output: ProcessedOutput,
        include_timestamp: bool = True
    ) -> str:
        """
        Create enhanced markdown content with cost estimates and documentation references.
        
        Args:
            query: Original user query
            processed_output: Processed agent output with extracted information
            include_timestamp: Whether to include generation timestamp
            
        Returns:
            str: Enhanced markdown content
        """
        logger.info("Generating enhanced markdown documentation")
        
        content = self._create_header(query, include_timestamp)
        content += self._create_diagram_section(processed_output.diagram_path)
        content += self._create_cost_section(processed_output.cost_estimates)
        content += self._create_design_details_section(processed_output.original_result)
        content += self._create_best_practices_section(processed_output.best_practices)
        content += self._create_documentation_section(processed_output.documentation_references)
        content += self._create_warnings_section(processed_output.warnings)
        content += self._create_next_steps_section(processed_output.cost_estimates)
        
        logger.info("Enhanced markdown documentation generated successfully")
        return content

    def _create_header(self, query: str, include_timestamp: bool) -> str:
        """Create the document header section."""
        content = "# AWS CloudWAN Architecture Design\n\n"
        
        if include_timestamp:
            content += f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        content += f"**Query:** {query}\n\n"
        return content

    def _create_diagram_section(self, diagram_path: Optional[str]) -> str:
        """Create the architecture diagram section."""
        content = "## Architecture Diagram\n\n"
        
        if diagram_path:
            filename = os.path.basename(diagram_path)
            content += f"![AWS CloudWAN Architecture]({filename})\n\n"
            content += f"**Diagram Location:** `{diagram_path}`\n\n"
        else:
            content += "*Diagram generation failed or file not found*\n\n"
        
        return content

    def _create_cost_section(self, cost_estimates: Optional[dict]) -> str:
        """Create the cost estimates section."""
        if not cost_estimates:
            return ""
        
        content = "## Cost Estimates\n\n"
        
        # Monthly cost summary
        if 'total_estimated_monthly' in cost_estimates:
            total = cost_estimates['total_estimated_monthly']
            content += f"**Estimated Monthly Cost:** ${total:,.2f}\n\n"
            
            if 'min_monthly' in cost_estimates and 'max_monthly' in cost_estimates:
                min_cost = cost_estimates['min_monthly']
                max_cost = cost_estimates['max_monthly']
                if min_cost != max_cost:
                    content += f"**Cost Range:** ${min_cost:,.2f} - ${max_cost:,.2f} per month\n\n"
        
        # Raw cost information
        if 'raw_costs' in cost_estimates:
            content += "### Cost Breakdown\n\n"
            for cost in cost_estimates['raw_costs']:
                content += f"- {cost}\n"
            content += "\n"
        
        # Cost optimization suggestions
        if 'optimization_suggestions' in cost_estimates:
            content += "### Cost Optimization Recommendations\n\n"
            for suggestion in cost_estimates['optimization_suggestions']:
                content += f"- {suggestion}\n"
            content += "\n"
        
        content += "---\n\n"
        return content

    def _create_design_details_section(self, original_result: str) -> str:
        """Create the design details section."""
        content = "## Design Details and Implementation Guide\n\n"
        content += f"{original_result}\n\n"
        content += "---\n\n"
        return content

    def _create_best_practices_section(self, best_practices: list) -> str:
        """Create the best practices section."""
        if not best_practices:
            return ""
        
        content = "## AWS Best Practices and Recommendations\n\n"
        content += "This design incorporates the following AWS best practices:\n\n"
        
        for practice in best_practices:
            content += f"- {practice}\n"
        
        content += "\n---\n\n"
        return content

    def _create_documentation_section(self, doc_references: list) -> str:
        """Create the AWS documentation references section."""
        if not doc_references:
            return ""
        
        content = "## AWS Documentation References\n\n"
        content += "For additional information and implementation details, refer to:\n\n"
        
        for ref in doc_references:
            if ref.startswith('http'):
                content += f"- [{ref}]({ref})\n"
            else:
                content += f"- {ref}\n"
        
        content += "\n---\n\n"
        return content

    def _create_warnings_section(self, warnings: list) -> str:
        """Create the warnings and important notes section."""
        if not warnings:
            return ""
        
        content = "## Important Notes and Considerations\n\n"
        
        for warning in warnings:
            content += f"⚠️ **{warning}**\n\n"
        
        content += "---\n\n"
        return content

    def _create_next_steps_section(self, cost_estimates: Optional[dict]) -> str:
        """Create the next steps section."""
        content = "## Next Steps\n\n"
        
        steps = [
            "Review the architecture design above",
            "Validate the design meets your specific requirements"
        ]
        
        if cost_estimates:
            steps.append("Review cost estimates and optimization recommendations")
        
        steps.extend([
            "Use the implementation guide to deploy the infrastructure",
            "Test connectivity and security controls",
            "Monitor performance and costs"
        ])
        
        for i, step in enumerate(steps, 1):
            content += f"{i}. {step}\n"
        
        return content


def create_enhanced_markdown_content(query: str, processed_output: ProcessedOutput) -> str:
    """
    Convenience function to create enhanced markdown content.
    
    This function provides backward compatibility with the existing codebase
    while using the new enhanced markdown generation capabilities.
    
    Args:
        query: Original user query
        processed_output: Processed agent output
        
    Returns:
        str: Enhanced markdown content
    """
    generator = EnhancedMarkdownGenerator()
    return generator.create_enhanced_markdown_content(query, processed_output)


# Backward compatibility function
def create_markdown_content(query: str, agent_result: str, diagram_path: Optional[str]) -> str:
    """
    Legacy function for backward compatibility.
    
    This function maintains compatibility with existing code while providing
    basic enhanced functionality.
    
    Args:
        query: Original user query
        agent_result: Raw agent result
        diagram_path: Path to generated diagram
        
    Returns:
        str: Basic enhanced markdown content
    """
    # Import here to avoid circular imports
    from output_processor import OutputProcessor, ProcessedOutput
    
    # Create a basic ProcessedOutput for backward compatibility
    processed_output = ProcessedOutput(
        original_result=agent_result,
        diagram_path=diagram_path,
        cost_estimates=None,
        documentation_references=[],
        best_practices=[],
        warnings=[]
    )
    
    generator = EnhancedMarkdownGenerator()
    return generator.create_enhanced_markdown_content(query, processed_output)