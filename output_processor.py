"""
Output processing module for enhanced AWS architecture design results.

This module provides functionality to parse agent results and extract structured
information including cost estimates, documentation references, and best practices.
"""

import re
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ProcessedOutput:
    """Structured representation of processed agent output."""
    original_result: str
    diagram_path: Optional[str]
    cost_estimates: Optional[Dict[str, Any]]
    documentation_references: List[str]
    best_practices: List[str]
    warnings: List[str]


class OutputProcessor:
    """
    Processes agent results to extract and organize different types of outputs.
    
    This class parses agent responses to identify:
    - Diagram file paths
    - Cost estimates and pricing information
    - AWS documentation references
    - Best practices and recommendations
    - Warnings and important notes
    """
    
    def __init__(self):
        """Initialize the OutputProcessor."""
        self.cost_patterns = [
            r'\$[\d,]+\.?\d*\s*(?:per\s+month|monthly|/month)',
            r'(?:cost|price|pricing):\s*\$[\d,]+\.?\d*',
            r'estimated\s+(?:cost|price):\s*\$[\d,]+\.?\d*',
            r'monthly\s+cost:\s*\$[\d,]+\.?\d*'
        ]
        
        self.doc_patterns = [
            r'https://docs\.aws\.amazon\.com/[^\s\)]+',
            r'AWS\s+(?:documentation|docs?)\s+(?:for|on)\s+[\w\s]+',
            r'(?:see|refer\s+to|check)\s+AWS\s+[\w\s]+\s+documentation'
        ]
        
        self.best_practice_patterns = [
            r'(?:best\s+practice|recommendation):\s*([^\n]+)',
            r'(?:AWS\s+recommends?|it\s+is\s+recommended):\s*([^\n]+)',
            r'(?:follow|implement|use)\s+AWS\s+Well-Architected\s+([^\n]+)'
        ]
        
        self.warning_patterns = [
            r'(?:warning|caution|note|important):\s*([^\n]+)',
            r'(?:be\s+aware|consider|ensure)\s+that\s+([^\n]+)',
            r'(?:limitation|constraint):\s*([^\n]+)'
        ]

    def process_agent_result(self, result: str) -> ProcessedOutput:
        """
        Process agent result and extract structured information.
        
        Args:
            result: Raw agent result string
            
        Returns:
            ProcessedOutput: Structured output with extracted information
        """
        logger.info("Processing agent result for enhanced output extraction")
        
        try:
            # Extract diagram path
            diagram_path = self._extract_diagram_path(result)
            
            # Extract cost estimates
            cost_estimates = self._extract_cost_estimates(result)
            
            # Extract documentation references
            doc_references = self._extract_documentation_references(result)
            
            # Extract best practices
            best_practices = self._extract_best_practices(result)
            
            # Extract warnings
            warnings = self._extract_warnings(result)
            
            processed_output = ProcessedOutput(
                original_result=result,
                diagram_path=diagram_path,
                cost_estimates=cost_estimates,
                documentation_references=doc_references,
                best_practices=best_practices,
                warnings=warnings
            )
            
            logger.info(f"Successfully processed output: diagram={bool(diagram_path)}, "
                       f"costs={bool(cost_estimates)}, docs={len(doc_references)}, "
                       f"practices={len(best_practices)}, warnings={len(warnings)}")
            
            return processed_output
            
        except Exception as e:
            logger.error(f"Error processing agent result: {e}")
            # Return basic processed output on error
            return ProcessedOutput(
                original_result=result,
                diagram_path=None,
                cost_estimates=None,
                documentation_references=[],
                best_practices=[],
                warnings=[f"Error processing output: {str(e)}"]
            )

    def _extract_diagram_path(self, result: str) -> Optional[str]:
        """Extract diagram path from agent result."""
        # Look for explicit diagram path
        for line in result.split("\n"):
            if "The diagram is saved at:" in line:
                return line.split("The diagram is saved at:")[1].strip()
        
        # Fallback: search for diagram file patterns
        diagram_pattern = r"([^\s]+\.(?:png|jpg|jpeg|svg|pdf))"
        matches = re.findall(diagram_pattern, result, re.IGNORECASE)
        return matches[0] if matches else None

    def _extract_cost_estimates(self, result: str) -> Optional[Dict[str, Any]]:
        """Extract cost estimates and pricing information from result."""
        cost_info = {}
        
        # Extract monetary amounts
        costs_found = []
        for pattern in self.cost_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            costs_found.extend(matches)
        
        if costs_found:
            cost_info['raw_costs'] = costs_found
            
            # Try to extract structured cost information
            monthly_costs = []
            for cost in costs_found:
                # Extract numeric value
                numeric_match = re.search(r'\$?([\d,]+\.?\d*)', cost)
                if numeric_match:
                    try:
                        value = float(numeric_match.group(1).replace(',', ''))
                        monthly_costs.append(value)
                    except ValueError:
                        continue
            
            if monthly_costs:
                # Remove duplicates while preserving order
                unique_costs = []
                seen_costs = set()
                for cost in monthly_costs:
                    if cost not in seen_costs:
                        unique_costs.append(cost)
                        seen_costs.add(cost)
                
                cost_info['monthly_estimates'] = unique_costs
                cost_info['total_estimated_monthly'] = sum(unique_costs)
                cost_info['min_monthly'] = min(unique_costs)
                cost_info['max_monthly'] = max(unique_costs)
        
        # Look for cost optimization suggestions
        optimization_patterns = [
            r'(?:cost\s+optimization|optimize\s+costs?):\s*([^\n]+)',
            r'(?:to\s+reduce\s+costs?|cost\s+savings?):\s*([^\n]+)',
            r'(?:cheaper\s+alternative|lower\s+cost):\s*([^\n]+)'
        ]
        
        optimizations = []
        for pattern in optimization_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            optimizations.extend(matches)
        
        # Also look for bullet points under cost optimization sections
        cost_opt_section_pattern = r'(?:cost\s+optimization|optimization\s+recommendations?)[^\n]*\n((?:\s*[-*]\s*[^\n]+\n?)+)'
        section_matches = re.findall(cost_opt_section_pattern, result, re.IGNORECASE | re.MULTILINE)
        for section in section_matches:
            # Extract individual bullet points
            bullet_points = re.findall(r'[-*]\s*([^\n]+)', section)
            optimizations.extend(bullet_points)
        
        if optimizations:
            cost_info['optimization_suggestions'] = optimizations
        
        return cost_info if cost_info else None

    def _extract_documentation_references(self, result: str) -> List[str]:
        """Extract AWS documentation references from result."""
        references = []
        
        # Extract direct documentation URLs
        url_matches = re.findall(self.doc_patterns[0], result)
        references.extend(url_matches)
        
        # Extract documentation mentions
        for pattern in self.doc_patterns[1:]:
            matches = re.findall(pattern, result, re.IGNORECASE)
            references.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_references = []
        for ref in references:
            if ref not in seen:
                seen.add(ref)
                unique_references.append(ref)
        
        return unique_references

    def _extract_best_practices(self, result: str) -> List[str]:
        """Extract best practices and recommendations from result."""
        practices = []
        
        for pattern in self.best_practice_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            practices.extend(matches)
        
        # Look for Well-Architected Framework references
        wa_pattern = r'(?:well-architected|security\s+pillar|reliability\s+pillar|performance\s+pillar|cost\s+optimization\s+pillar|operational\s+excellence):\s*([^\n]+)'
        wa_matches = re.findall(wa_pattern, result, re.IGNORECASE)
        practices.extend(wa_matches)
        
        # Clean up and deduplicate
        cleaned_practices = []
        for practice in practices:
            cleaned = practice.strip()
            if cleaned and cleaned not in cleaned_practices:
                cleaned_practices.append(cleaned)
        
        return cleaned_practices

    def _extract_warnings(self, result: str) -> List[str]:
        """Extract warnings and important notes from result."""
        warnings = []
        
        for pattern in self.warning_patterns:
            matches = re.findall(pattern, result, re.IGNORECASE)
            warnings.extend(matches)
        
        # Clean up and deduplicate
        cleaned_warnings = []
        for warning in warnings:
            cleaned = warning.strip()
            if cleaned and cleaned not in cleaned_warnings:
                cleaned_warnings.append(cleaned)
        
        return cleaned_warnings