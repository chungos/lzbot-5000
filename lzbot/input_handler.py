"""
Input Handler Module for LZBot-5000

Handles command-line argument parsing and various input methods for user queries
with Pydantic validation for input data integrity.
"""

import argparse
import sys
from typing import Optional
from pathlib import Path
from .logging_config import get_logger, log_function
from .validation import UserQuery, validate_architecture_query, safe_validate, format_validation_errors
from .exceptions import ValidationError, ErrorHandler

logger = get_logger(__name__)


class InputHandler:
    """Handles input parsing and processing for LZBot-5000."""
    
    def __init__(self):
        """Initialize the input handler."""
        self.parser = self._create_parser()
        self.args = None
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create command-line argument parser.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            description="AWS Landing Zone Designer with JIRA/Confluence Integration",
            epilog="""
Examples:
  python3 main.py                                    # Interactive mode with conversation
  python3 main.py -q "Design a multi-region setup"  # Direct query
  python3 main.py -f requirements.txt               # Read from file
  python3 main.py --interactive                     # Force full conversational mode
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        input_group = parser.add_mutually_exclusive_group()
        input_group.add_argument(
            '-q', '--query',
            help='Architecture requirements query as a string'
        )
        input_group.add_argument(
            '-f', '--file',
            help='Path to file containing architecture requirements'
        )
        
        parser.add_argument(
            '--output-dir',
            default='./outputs',
            help='Directory to save generated diagrams and documentation (default: ./outputs)'
        )
        
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Enable full interactive mode with conversational requirement gathering'
        )
        
        parser.add_argument(
            '--skip-config-check',
            action='store_true',
            help='Skip configuration validation (for help and testing)'
        )
        
        return parser
    
    def parse_arguments(self, args: Optional[list] = None) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Args:
            args: Optional list of arguments, uses sys.argv if None
            
        Returns:
            Parsed arguments namespace
        """
        self.args = self.parser.parse_args(args)
        logger.info(f"Parsed arguments: {vars(self.args)}")
        return self.args
    
    def should_show_help_and_exit(self, args: Optional[list] = None) -> bool:
        """
        Check if help was requested and handle it.
        
        Args:
            args: Optional list of arguments to check
            
        Returns:
            True if help was shown and program should exit
        """
        check_args = args or sys.argv[1:]
        
        if len(check_args) > 0 and ('--help' in check_args or '-h' in check_args):
            self.parser.print_help()
            return True
        
        return False
    
    @log_function
    def get_query_input(self, args: Optional[argparse.Namespace] = None) -> str:
        """
        Get query input from command line arguments, file, or interactive input.
        
        Args:
            args: Parsed arguments, uses self.args if None
            
        Returns:
            User query string
            
        Raises:
            ValidationError: If query validation fails
            SystemExit: If invalid input or user cancellation
        """
        if args is None:
            args = self.args
        
        if args is None:
            raise ValueError("Arguments must be parsed before getting query input")
        
        # Get raw query first
        raw_query = None
        
        # Option 1: Query provided via command line argument
        if args.query:
            logger.info("Using query from command line argument")
            print("📝 Using query from command line argument")
            raw_query = args.query
        
        # Option 2: Query from file
        elif args.file:
            logger.info(f"Reading query from file: {args.file}")
            raw_query = self._read_query_from_file(args.file)
        
        # Option 3: Interactive input
        else:
            logger.info("Using interactive input mode")
            raw_query = self._get_interactive_input()
        
        # Validate the query
        return self._validate_and_enhance_query(raw_query)
    
    @log_function
    def _validate_and_enhance_query(self, raw_query: str) -> str:
        """
        Validate and enhance user query using Pydantic models.
        
        Args:
            raw_query: Raw user input
            
        Returns:
            Validated and potentially enhanced query
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Basic validation
            validated_query, errors = safe_validate(
                {'description': raw_query}, 
                UserQuery
            )
            
            if errors:
                error_msg = format_validation_errors(errors)
                print(error_msg)
                raise ValidationError(f"Query validation failed: {'; '.join(errors)}")
            
            logger.info("Query validation successful")
            return validated_query.description
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Query validation error: {str(e)}")
    
    def print_conversation_guidance(self) -> None:
        """Print guidance for users on how to engage in conversation with the agent."""
        print("\n" + "="*70)
        print("💡 CONVERSATIONAL MODE GUIDANCE")
        print("="*70)
        print("The AI agent will ask clarifying questions to better understand your needs.")
        print("This helps create a more accurate and tailored AWS architecture design.")
        print()
        print("Tips for effective conversation:")
        print("• Be specific about your business requirements and constraints")
        print("• Mention any compliance requirements (HIPAA, PCI DSS, SOC 2, etc.)")
        print("• Share information about your team size and technical expertise")
        print("• Specify budget constraints or cost optimization priorities")
        print("• Mention any existing AWS infrastructure or migration needs")
        print()
        print("You can:")
        print("• Answer the agent's questions in detail")
        print("• Ask for clarification if you don't understand a question")
        print("• Type 'proceed' to continue with current information if you prefer")
        print("• Use Ctrl+C to cancel the conversation at any time")
        print("="*70)
    
    def get_validated_query_object(self, args: Optional[argparse.Namespace] = None, **kwargs) -> UserQuery:
        """
        Get a fully validated UserQuery object with additional parameters.
        
        Args:
            args: Parsed arguments
            **kwargs: Additional query parameters (complexity, region, etc.)
            
        Returns:
            Validated UserQuery object
        """
        raw_query = self.get_query_input(args)
        
        # Build query data with any additional parameters
        query_data = {'description': raw_query, **kwargs}
        
        try:
            return validate_architecture_query(raw_query, **kwargs)
        except Exception as e:
            raise ValidationError(f"Failed to create validated query object: {str(e)}")
    
    def _read_query_from_file(self, file_path: str) -> str:
        """
        Read query from specified file.
        
        Args:
            file_path: Path to file containing query
            
        Returns:
            Query content from file
            
        Raises:
            SystemExit: If file not found or other errors
        """
        try:
            print(f"📁 Reading query from file: {file_path}")
            
            file_obj = Path(file_path)
            if not file_obj.exists():
                print(f"❌ Error: File not found: {file_path}")
                sys.exit(1)
            
            query = file_obj.read_text(encoding='utf-8').strip()
            
            if not query:
                print("❌ Error: File is empty")
                sys.exit(1)
            
            logger.info(f"Successfully read query from file: {len(query)} characters")
            return query
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            logger.error(f"Error reading file {file_path}: {e}")
            sys.exit(1)
    
    def _get_interactive_input(self) -> str:
        """
        Get query input interactively from user.
        
        Returns:
            User-provided query string
            
        Raises:
            SystemExit: If no input provided or user cancellation
        """
        print("🤖 AWS Landing Zone Designer")
        print("=" * 50)
        print("Please describe your AWS architecture requirements:")
        print("(You can provide multiple lines, press Ctrl+D or Ctrl+Z when finished)")
        print()
        
        lines = []
        try:
            while True:
                try:
                    line = input("> " if not lines else "  ")
                    lines.append(line)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\n\n❌ Operation cancelled by user")
                    logger.info("Interactive input cancelled by user")
                    sys.exit(0)
        except Exception as e:
            print(f"❌ Error getting input: {e}")
            logger.error(f"Error during interactive input: {e}")
            sys.exit(1)
        
        query = "\n".join(lines).strip()
        if not query:
            print("❌ Error: No query provided")
            logger.error("No query provided in interactive mode")
            sys.exit(1)
        
        logger.info(f"Collected interactive query: {len(query)} characters")
        return query
    
    def print_query_summary(self, query: str) -> None:
        """
        Print a summary of the query for user confirmation.
        
        Args:
            query: User query to summarize
        """
        print(f"\n🚀 Processing architecture request...")
        print(f"📝 Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        if self.args and self.args.output_dir:
            print(f"📁 Output directory: {self.args.output_dir}")
        print()
    
    def get_output_directory(self) -> str:
        """
        Get the output directory from arguments.
        
        Returns:
            Output directory path
        """
        if self.args and self.args.output_dir:
            return self.args.output_dir
        return "./outputs"