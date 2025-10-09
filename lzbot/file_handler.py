"""
File Handler Module for LZBot-5000

Handles file operations including diagram management, markdown generation, and file organization.
"""

import os
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .logging_config import get_logger, log_function

logger = get_logger(__name__)


class FileHandler:
    """Handles file operations for LZBot-5000."""
    
    def __init__(self, output_dir: str = "./outputs"):
        """
        Initialize file handler with output directory.
        
        Args:
            output_dir: Directory for saving generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"File handler initialized with output directory: {self.output_dir}")
    
    def extract_diagram_path(self, agent_result: Any) -> Optional[str]:
        """
        Extract diagram path from agent result.
        
        Args:
            agent_result: Result from AI agent containing potential diagram path
            
        Returns:
            Path to diagram file if found, None otherwise
        """
        result_str = str(agent_result)
        
        # Look for explicit diagram path
        for line in result_str.split("\n"):
            if "The diagram is saved at:" in line:
                path = line.split("The diagram is saved at:")[1].strip()
                logger.info(f"Found explicit diagram path: {path}")
                return path
        
        # Fallback: search for diagram file patterns
        diagram_pattern = r"([^\s]+\.(?:png|jpg|jpeg|svg|pdf))"
        matches = re.findall(diagram_pattern, result_str, re.IGNORECASE)
        
        if matches:
            path = matches[0]
            logger.info(f"Found diagram path via pattern matching: {path}")
            return path
        
        logger.warning("No diagram path found in agent result")
        return None
    
    def handle_diagram_file(self, original_path: Optional[str]) -> Optional[str]:
        """
        Handle diagram file movement and return local path.
        
        Args:
            original_path: Original path to diagram file
            
        Returns:
            Local path to diagram file if successful, None otherwise
        """
        if not original_path:
            logger.warning("No original diagram path provided")
            return None
        
        filename = os.path.basename(original_path)
        local_path = self.output_dir / filename
        
        # If file already exists locally, use it
        if local_path.exists():
            logger.info(f"Diagram already exists at: {local_path}")
            return str(local_path)
        
        # Try to copy from original location
        if os.path.exists(original_path):
            try:
                shutil.copy2(original_path, local_path)
                logger.info(f"Moved diagram from {original_path} to {local_path}")
                return str(local_path)
            except Exception as e:
                logger.error(f"Could not move diagram file: {e}")
                return original_path
        
        logger.warning(f"Diagram file not found at {original_path}")
        return None
    
    def create_markdown_content(
        self, 
        query: str, 
        agent_result: Any, 
        diagram_path: Optional[str] = None
    ) -> str:
        """
        Create markdown content with architecture design and optional diagram.
        
        Args:
            query: Original user query
            agent_result: AI agent response
            diagram_path: Path to diagram file (optional)
            
        Returns:
            Formatted markdown content
        """
        content = f"""# AWS CloudWAN Architecture Design

**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Query:** {query}

## Architecture Diagram
"""
        
        if diagram_path:
            filename = os.path.basename(diagram_path)
            content += f"![AWS CloudWAN Architecture]({filename})\n\n"
            content += f"**Diagram Location:** `{diagram_path}`\n\n"
            logger.info(f"Added diagram reference to markdown: {filename}")
        else:
            content += "*Diagram generation failed or file not found*\n\n"
            logger.warning("No diagram available for markdown content")
        
        content += f"""## Design Details and Implementation Guide

{agent_result}

---

## Next Steps

1. Review the architecture design above
2. Validate the design meets your specific requirements
3. Use the implementation guide to deploy the infrastructure
4. Test connectivity and security controls
5. Monitor performance and costs
"""
        
        return content
    
    def save_markdown_file(self, content: str, filename: Optional[str] = None) -> str:
        """
        Save markdown content to file.
        
        Args:
            content: Markdown content to save
            filename: Optional filename, auto-generated if not provided
            
        Returns:
            Path to saved markdown file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aws_design_{timestamp}.md"
        
        markdown_path = self.output_dir / filename
        
        try:
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"Markdown file saved: {markdown_path}")
            return str(markdown_path)
            
        except Exception as e:
            logger.error(f"Error saving markdown file: {e}")
            raise
    
    def process_agent_result(
        self, 
        query: str, 
        agent_result: Any, 
        custom_filename: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Process agent result and save all generated files.
        
        Args:
            query: Original user query
            agent_result: AI agent response
            custom_filename: Optional custom filename for markdown
            
        Returns:
            Dictionary with paths to generated files
        """
        logger.info("Processing agent result and saving files")
        
        # Handle diagram
        original_diagram_path = self.extract_diagram_path(agent_result)
        local_diagram_path = self.handle_diagram_file(original_diagram_path)
        
        # Generate and save markdown
        markdown_content = self.create_markdown_content(query, agent_result, local_diagram_path)
        
        # Add file location info to markdown
        if custom_filename:
            markdown_path = self.save_markdown_file(markdown_content, custom_filename)
        else:
            markdown_path = self.save_markdown_file(markdown_content)
        
        # Update markdown with its own path
        updated_content = markdown_content + f"\n**Documentation saved at:** `{markdown_path}`\n"
        
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        
        result = {
            "markdown_path": markdown_path,
            "diagram_path": local_diagram_path,
            "output_dir": str(self.output_dir)
        }
        
        logger.info(f"File processing complete: {result}")
        return result
    
    def get_output_summary(self, file_paths: Dict[str, Optional[str]]) -> str:
        """
        Generate a summary of output files.
        
        Args:
            file_paths: Dictionary of file paths from process_agent_result
            
        Returns:
            Formatted summary string
        """
        summary = f"\n{'=' * 60}\n"
        summary += "✅ Design documentation saved successfully!\n"
        summary += f"📄 Markdown file: {file_paths['markdown_path']}\n"
        
        if file_paths['diagram_path']:
            summary += f"🖼️  Diagram file: {file_paths['diagram_path']}\n"
        
        summary += f"📁 Output directory: {file_paths['output_dir']}\n"
        summary += f"{'=' * 60}"
        
        return summary