#!/usr/bin/env python3
"""
LZBot-5000: AWS Landing Zone Designer
Main application entry point

A professional, modular tool for designing AWS Landing Zones with 
automatic JIRA/Confluence integration and comprehensive documentation.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for local imports
sys.path.insert(0, str(Path(__file__).parent))

from lzbot import ClientManager, LZBotAgent, InputHandler, FileHandler
from lzbot.logging_config import setup_logging, get_logger
from lzbot.exceptions import LZBotError, ConfigurationError, ErrorHandler, MCPClientError
from config import load_config, ConfigError

# Setup structured logging
setup_logging(level="INFO", include_timestamp=True)
logger = get_logger(__name__)


class LZBotApplication:
    """Main application class for LZBot-5000."""
    
    def __init__(self):
        """Initialize the application components."""
        self.config = None
        self.input_handler = InputHandler()
        self.client_manager = None
        self.agent = None
        self.file_handler = None
    
    def initialize(self) -> bool:
        """
        Initialize application configuration and components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if help was requested
            if self.input_handler.should_show_help_and_exit():
                return False
            
            # Load configuration
            logger.info("Loading configuration...")
            self.config = load_config()
            print("✅ Configuration loaded successfully!")
            
            # Print config summary based on type
            if hasattr(self.config, 'model_dump'):
                # Modern Pydantic config
                print("🔧 Configuration Summary (Pydantic):")
                print("=" * 50)
                config_dict = self.config.to_env_dict()
                for key, value in config_dict.items():
                    if key in ["JIRA_API_TOKEN"]:
                        # Mask API token for security
                        masked_value = value[:8] + "*" * (len(value) - 12) + value[-4:] if len(value) > 12 else "*" * len(value)
                        print(f"   {key}: {masked_value}")
                    elif key in ["JIRA_EMAIL"]:
                        # Mask email partially
                        parts = value.split("@")
                        if len(parts) == 2:
                            masked_email = parts[0][:2] + "*" * (len(parts[0]) - 2) + "@" + parts[1]
                            print(f"   {key}: {masked_email}")
                        else:
                            print(f"   {key}: {value}")
                    else:
                        print(f"   {key}: {value}")
                print("=" * 50)
            else:
                # Legacy config
                self.config.print_config_summary()
            
            # Parse command line arguments
            args = self.input_handler.parse_arguments()
            
            # Initialize components
            logger.info("Initializing application components...")
            
            # Get environment variables based on config type
            if hasattr(self.config, 'to_env_dict'):
                # Modern Pydantic config
                env_vars = self.config.to_env_dict()
            else:
                # Legacy config
                env_vars = self.config.get_all_env_vars()
            
            self.client_manager = ClientManager(env_vars)
            self.agent = LZBotAgent(env_vars)
            self.file_handler = FileHandler(args.output_dir)
            
            logger.info("Application initialization complete")
            return True
            
        except ConfigError as e:
            print(f"❌ Configuration error: {e}")
            print("\n💡 Run 'python3 setup_env.py' to configure your environment")
            return False
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            print(f"❌ Initialization error: {e}")
            return False
    
    def run(self) -> int:
        """
        Run the main application.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Initialize application
            if not self.initialize():
                return 1
            
            # Get user query
            logger.info("Getting user query...")
            query = self.input_handler.get_query_input()
            self.input_handler.print_query_summary(query)
            
            # Process the architecture request
            logger.info("Processing architecture request...")
            result = self._process_architecture_request(query)
            
            if result:
                print("🎉 Architecture design completed successfully!")
                return 0
            else:
                print("❌ Architecture design failed")
                return 1
                
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user")
            logger.info("Application cancelled by user")
            return 1
            
        except (ConfigurationError, ConfigError) as e:
            error_msg = ErrorHandler.format_error_for_user(e) if isinstance(e, LZBotError) else f"❌ Configuration Error: {e}"
            print(error_msg)
            logger.error(f"Configuration error: {e}", exc_info=True)
            return 1
            
        except LZBotError as e:
            error_msg = ErrorHandler.format_error_for_user(e)
            print(error_msg)
            logger.error(f"LZBot error: {e}", exc_info=True)
            return 1
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return 1
    
    def _process_architecture_request(self, query: str) -> bool:
        """
        Process architecture request using AI agent and save results.
        
        Args:
            query: User's architecture requirements
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Get all available tools
            logger.info("Retrieving tools from MCP clients...")
            print("🔧 Initializing AI tools...")
            
            with self.client_manager:
                tools = self.client_manager.get_all_tools()
                
                # Process query with AI agent
                print("🤖 Sending query to AI agent...")
                print("⏳ This may take a few minutes for complex architectures...")
                
                agent_result = self.agent.process_query(query, tools)
                
                # Save results to files
                logger.info("Saving generated files...")
                print("💾 Saving generated documentation and diagrams...")
                
                file_results = self.file_handler.process_agent_result(query, agent_result)
                
                # Display summary
                summary = self.file_handler.get_output_summary(file_results)
                print(summary)
                
                return True
                
        except MCPClientError as e:
            error_msg = ErrorHandler.format_error_for_user(e)
            print(error_msg)
            logger.error(f"MCP client error: {e}", exc_info=True)
            return False
            
        except LZBotError as e:
            error_msg = ErrorHandler.format_error_for_user(e)
            print(error_msg)
            logger.error(f"LZBot error in architecture processing: {e}", exc_info=True)
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error processing architecture request: {e}", exc_info=True)
            print(f"❌ Unexpected error processing request: {e}")
            return False


def main() -> int:
    """
    Main entry point for LZBot-5000.
    
    Returns:
        Exit code
    """
    print("🚀 LZBot-5000: AWS Landing Zone Designer")
    print("=" * 50)
    
    app = LZBotApplication()
    return app.run()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)