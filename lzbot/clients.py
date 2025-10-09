"""
MCP Client Manager for LZBot-5000

Handles MCP (Model Context Protocol) client connections for AWS tools
and JIRA/Confluence integration with enhanced error handling and logging.
"""

import asyncio
import subprocess
import signal
import json
import os
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from .logging_config import get_logger, log_function, LZBotLogger
from .exceptions import MCPClientError, MCPConnectionError, MCPToolError, ErrorHandler, handle_exception

logger = get_logger(__name__)

from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters, stdio_client
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ClientManager:
    """Manages MCP clients for AWS and JIRA/Confluence services."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the client manager with configuration.
        
        Args:
            config: Configuration dictionary containing environment variables
        """
        self.config = config
        self._aws_client = None
        self._jira_confluence_client = None
        self._clients_started = False
        
    @log_function
    def _create_aws_client(self) -> MCPClient:
        """Create AWS diagram MCP client."""
        logger.info("Creating AWS diagram MCP client...")
        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx", 
                    args=["--with", "jschema-to-python", "awslabs.aws-diagram-mcp-server@latest"]
                )
            )
        )
    
    @log_function
    def _create_jira_confluence_client(self) -> MCPClient:
        """Create JIRA/Confluence MCP client using the new modular server."""
        logger.info("Creating JIRA/Confluence MCP client with new modular architecture...")
        
        # Ensure config is a dictionary and map environment variables for new server
        env_dict = self._prepare_env_for_new_server()
            
        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command="uvx",
                    args=["--from", "git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git", "jira-confluence-mcp"],
                    env=env_dict
                )
            )
        )
    
    @log_function
    def _prepare_env_for_new_server(self) -> Dict[str, str]:
        """Prepare environment variables for the new modular MCP server."""
        # Start with existing config
        env_dict = self.config
        if hasattr(self.config, 'get_env_dict'):
            env_dict = self.config.get_env_dict()
        elif not isinstance(self.config, dict):
            # Convert to dict if it's not already
            env_dict = dict(self.config) if hasattr(self.config, '__iter__') else {}
        
        # Map old environment variable names to new ones if needed
        env_mapping = {
            'JIRA_URL': 'JIRA_SERVER_URL',
            'JIRA_EMAIL': 'JIRA_USERNAME', 
            'JIRA_API_TOKEN': 'JIRA_TOKEN',
            'CONFLUENCE_URL': 'CONFLUENCE_SERVER_URL',
            'CONFLUENCE_EMAIL': 'CONFLUENCE_USERNAME',
            'CONFLUENCE_API_TOKEN': 'CONFLUENCE_TOKEN',
            'CONFLUENCE_SPACE_KEY': 'CONFLUENCE_SPACE_KEY'
        }
        
        # Apply mapping and ensure all required variables are present
        mapped_env = {}
        for old_key, new_key in env_mapping.items():
            if old_key in env_dict:
                mapped_env[new_key] = env_dict[old_key]
                # Keep old key for backward compatibility
                mapped_env[old_key] = env_dict[old_key]
        
        # Add any additional environment variables that weren't mapped
        for key, value in env_dict.items():
            if key not in env_mapping and value is not None:
                mapped_env[key] = str(value)
        
        logger.debug(f"Prepared environment for new MCP server with {len(mapped_env)} variables")
        return mapped_env
    
    def __enter__(self):
        """Context manager entry - start all MCP clients."""
        try:
            logger.info("Starting MCP clients...")
            
            # Create and start AWS client with jschema-to-python dependency
            self._aws_client = self._create_aws_client()
            self._aws_client.__enter__()
            logger.info("AWS MCP client started")
            
            # Create and start JIRA/Confluence client  
            self._jira_confluence_client = self._create_jira_confluence_client()
            self._jira_confluence_client.__enter__()
            logger.info("JIRA/Confluence MCP client started")
            
            self._clients_started = True
            logger.info("All MCP clients started successfully")
            return self
            
        except Exception as e:
            logger.error(f"Error starting MCP clients: {e}")
            # Clean up any clients that were started
            self.__exit__(None, None, None)
            raise
            return self
            
        except Exception as e:
            logger.error(f"Error starting MCP clients: {e}")
            # Clean up any clients that were started
            self.__exit__(None, None, None)
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup clients."""
        self._clients_started = False
        
        if self._aws_client:
            try:
                self._aws_client.__exit__(exc_type, exc_val, exc_tb)
                logger.info("AWS MCP client stopped")
            except Exception as e:
                logger.error(f"Error closing AWS client: {e}")
            finally:
                self._aws_client = None
                
        if self._jira_confluence_client:
            try:
                self._jira_confluence_client.__exit__(exc_type, exc_val, exc_tb)
                logger.info("JIRA/Confluence MCP client stopped")
            except Exception as e:
                logger.error(f"Error closing JIRA/Confluence client: {e}")
            finally:
                self._jira_confluence_client = None
        
        logger.info("All MCP clients stopped")
    
    def get_all_tools(self) -> List[Any]:
        """
        Get all tools from both AWS and JIRA/Confluence clients.
        
        Returns:
            List of all available tools from both clients
            
        Raises:
            RuntimeError: If clients are not started
        """
        if not self._clients_started:
            raise RuntimeError("MCP clients are not started. Use within context manager.")

        try:
            logger.info("Retrieving tools from all MCP clients...")
            
            aws_tools = []
            jira_tools = []
            
            # Get AWS tools
            if self._aws_client:
                try:
                    aws_tools_result = self._aws_client.list_tools_sync()
                    aws_tools = list(aws_tools_result) if aws_tools_result else []
                    logger.info(f"Retrieved {len(aws_tools)} AWS tools")
                except Exception as e:
                    logger.warning(f"Could not retrieve AWS tools: {e}")
                    aws_tools = []
            
            # Get JIRA/Confluence tools with enhanced filtering for new server
            if self._jira_confluence_client:
                try:
                    jira_tools_result = self._jira_confluence_client.list_tools_sync()
                    all_jira_tools = list(jira_tools_result) if jira_tools_result else []
                    
                    # Enhanced filtering for new modular server
                    # Include analytics tools from plugins if available
                    excluded_tools = ['bulk_create_backlog']  # Still exclude this complex tool
                    preferred_tools = [
                        'create_epic', 'create_sprint', 'create_story',
                        'create_confluence_page', 'upload_attachment', 'link_jira_to_confluence',
                        'get_project_stats', 'get_user_activity', 'generate_burndown'  # New plugin tools
                    ]
                    
                    # First, include all preferred tools that are available
                    jira_tools = [tool for tool in all_jira_tools 
                                if getattr(tool, 'name', getattr(tool, 'tool_name', '')) in preferred_tools]
                    
                    # Then add any other tools not in excluded list
                    for tool in all_jira_tools:
                        tool_name = getattr(tool, 'name', getattr(tool, 'tool_name', ''))
                        if (tool_name not in excluded_tools and 
                            tool_name not in preferred_tools and 
                            tool not in jira_tools):
                            jira_tools.append(tool)
                    
                    logger.info(f"Retrieved {len(jira_tools)} JIRA/Confluence tools from new modular server "
                              f"(filtered {len(all_jira_tools) - len(jira_tools)} complex tools)")
                    
                    # Log available tool names for debugging
                    tool_names = [getattr(tool, 'name', getattr(tool, 'tool_name', 'unknown')) for tool in jira_tools]
                    logger.debug(f"Available JIRA tools: {tool_names}")
                    
                except Exception as e:
                    logger.warning(f"Could not retrieve JIRA/Confluence tools: {e}")
                    logger.debug(f"JIRA client error details: {e}", exc_info=True)
                    jira_tools = []
            
            all_tools = aws_tools + jira_tools
            logger.info(f"Total tools available: {len(all_tools)} (AWS: {len(aws_tools)}, JIRA: {len(jira_tools)})")
            
            if not all_tools:
                logger.warning("No tools retrieved from any MCP clients - this may indicate connection issues")
            
            return all_tools
            
        except Exception as e:
            logger.error(f"Error retrieving tools from MCP clients: {e}")
            logger.debug("Full error details:", exc_info=True)
            raise

    @property
    def aws_client(self) -> MCPClient:
        """Get AWS client (only available when context is active)."""
        if not self._clients_started or not self._aws_client:
            raise RuntimeError("AWS client not available. Use within context manager.")
        return self._aws_client
    
    @property 
    def jira_confluence_client(self) -> MCPClient:
        """Get JIRA/Confluence client (only available when context is active)."""
        if not self._clients_started or not self._jira_confluence_client:
            raise RuntimeError("JIRA/Confluence client not available. Use within context manager.")
        return self._jira_confluence_client