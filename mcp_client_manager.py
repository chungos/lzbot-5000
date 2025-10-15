"""
MCP Client Manager for handling multiple MCP client connections.

This module provides the MCPClientManager class that manages multiple MCP clients
and aggregates their tools for use by the agent.
"""

from typing import Optional, List, Dict, Any
import logging
import time
from strands.tools.mcp import MCPClient
from mcp import StdioServerParameters, stdio_client
from mcp_config import MCPClientConfig, MCPConfigManager
from mcp_error_handling import MCPErrorHandler
from mcp_monitoring import MCPMonitor

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages multiple MCP client connections and aggregates their tools.
    
    This class handles initialization of multiple MCP clients, tool aggregation,
    and provides methods to check client availability with error handling and retry logic.
    """
    
    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        """
        Initialize the MCP Client Manager.
        
        Args:
            config_manager: Optional MCPConfigManager instance
        """
        self.diagram_client: Optional[MCPClient] = None
        self.knowledge_client: Optional[MCPClient] = None
        self.pricing_client: Optional[MCPClient] = None
        self.available_tools: List = []
        self._client_status: Dict[str, bool] = {}
        self._client_configs: Dict[str, MCPClientConfig] = {}
        self.config_manager = config_manager or MCPConfigManager()
        self.error_handler = MCPErrorHandler()
        self.monitor = MCPMonitor()
        self._active_clients: List[MCPClient] = []
    
    def __enter__(self):
        """Enter context manager - start all available clients."""
        self._active_clients = []
        for client_name, client in [
            ("diagram", self.diagram_client),
            ("knowledge", self.knowledge_client),
            ("pricing", self.pricing_client)
        ]:
            if client and self.is_client_available(client_name):
                try:
                    with self.monitor.track_operation("client_start", client_name):
                        client.__enter__()
                        self._active_clients.append(client)
                        self.monitor.record_connection_event(
                            client_name, "context_enter", True, "Client started successfully"
                        )
                except Exception as e:
                    logger.error(f"Failed to start {client_name} client: {e}")
                    self._client_status[client_name] = False
                    self.monitor.record_connection_event(
                        client_name, "context_enter", False, str(e)
                    )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - stop all active clients."""
        for client in self._active_clients:
            try:
                # Find client name for monitoring
                client_name = "unknown"
                for name, stored_client in [
                    ("diagram", self.diagram_client),
                    ("knowledge", self.knowledge_client),
                    ("pricing", self.pricing_client)
                ]:
                    if stored_client == client:
                        client_name = name
                        break
                
                with self.monitor.track_operation("client_stop", client_name):
                    client.__exit__(exc_type, exc_val, exc_tb)
                    self.monitor.record_connection_event(
                        client_name, "context_exit", True, "Client stopped successfully"
                    )
            except Exception as e:
                logger.error(f"Error stopping MCP client: {e}")
                self.monitor.record_connection_event(
                    client_name, "context_exit", False, str(e)
                )
        self._active_clients = []
        
    def initialize_clients(self, configs: Optional[List[MCPClientConfig]] = None) -> None:
        """
        Initialize MCP clients based on provided configurations or load from config manager.
        
        Args:
            configs: Optional list of MCPClientConfig objects. If None, loads from config manager.
        """
        if configs is None:
            configs = self.config_manager.load_configurations()
        
        for config in configs:
            self._client_configs[config.name] = config
            success = self._initialize_client_with_retry(config)
            
            if not success and config.required:
                raise RuntimeError(f"Failed to initialize required MCP client: {config.name}")
    
    def _initialize_client_with_retry(self, config: MCPClientConfig) -> bool:
        """
        Initialize a client with retry logic.
        
        Args:
            config: MCPClientConfig object
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(config.retry_attempts + 1):
            try:
                with self.monitor.track_operation("client_initialization", config.name, attempt=attempt):
                    client = self._create_client(config)
                    self._assign_client(config.name, client)
                    self._client_status[config.name] = True
                    
                    # Update health metrics
                    self.monitor.update_client_health(
                        config.name, True, tool_count=0, error_count=0
                    )
                    
                    # Record successful connection
                    self.monitor.record_connection_event(
                        config.name, "initialization", True, 
                        f"Initialized successfully on attempt {attempt + 1}"
                    )
                    
                    logger.info(f"Successfully initialized {config.name} MCP client on attempt {attempt + 1}")
                    return True
                
            except Exception as e:
                self._client_status[config.name] = False
                
                # Handle error through error handler
                mcp_error = self.error_handler.handle_client_error(config.name, e, attempt)
                
                # Update health metrics
                self.monitor.update_client_health(
                    config.name, False, error_count=attempt + 1, last_error=str(e)
                )
                
                # Record failed connection attempt
                self.monitor.record_connection_event(
                    config.name, "initialization", False, 
                    f"Attempt {attempt + 1} failed: {str(e)}"
                )
                
                if attempt < config.retry_attempts and self.error_handler.should_retry(config.name):
                    logger.info(f"Retrying in {config.retry_delay} seconds...")
                    time.sleep(config.retry_delay)
                else:
                    if config.required:
                        logger.error(f"Failed to initialize required MCP client {config.name} after {config.retry_attempts + 1} attempts")
                    else:
                        logger.warning(f"Failed to initialize optional MCP client {config.name} after {config.retry_attempts + 1} attempts")
                    break
        
        return False
    
    def _create_client(self, config: MCPClientConfig) -> MCPClient:
        """
        Create an MCP client from configuration.
        
        Args:
            config: MCPClientConfig object
            
        Returns:
            MCPClient instance
        """
        return MCPClient(
            lambda: stdio_client(
                StdioServerParameters(
                    command=config.command,
                    args=config.args
                )
            )
        )
    
    def _assign_client(self, name: str, client: MCPClient) -> None:
        """
        Assign client to appropriate instance variable based on name.
        
        Args:
            name: Client name (diagram, knowledge, pricing)
            client: MCPClient instance
        """
        if name == "diagram":
            self.diagram_client = client
        elif name == "knowledge":
            self.knowledge_client = client
        elif name == "pricing":
            self.pricing_client = client
        else:
            logger.warning(f"Unknown client name: {name}")
    
    def get_all_tools(self) -> List:
        """
        Aggregate tools from all available MCP clients.
        
        Returns:
            List of all available tools from connected clients
        """
        all_tools = []
        
        # Collect tools from each available client
        for client_name, client in [
            ("diagram", self.diagram_client),
            ("knowledge", self.knowledge_client),
            ("pricing", self.pricing_client)
        ]:
            if client and self.is_client_available(client_name):
                try:
                    with self.monitor.track_operation("list_tools", client_name):
                        # Use context manager to properly start the client session
                        with client:
                            tools = client.list_tools_sync()
                            all_tools.extend(tools)
                        
                        # Update health metrics with tool count
                        self.monitor.update_client_health(
                            client_name, True, tool_count=len(tools), error_count=0
                        )
                        
                        logger.info(f"Added {len(tools)} tools from {client_name} client")
                        
                except Exception as e:
                    self.error_handler.handle_client_error(client_name, e)
                    self._client_status[client_name] = False
                    
                    # Update health metrics with error
                    self.monitor.update_client_health(
                        client_name, False, error_count=1, last_error=str(e)
                    )
        
        self.available_tools = all_tools
        return all_tools
    
    def is_client_available(self, client_type: str) -> bool:
        """
        Check if a specific client type is available and connected.
        
        Args:
            client_type: Type of client (diagram, knowledge, pricing)
            
        Returns:
            True if client is available, False otherwise
        """
        return self._client_status.get(client_type, False)
    
    def get_available_clients(self) -> List[str]:
        """
        Get list of currently available client names.
        
        Returns:
            List of available client names
        """
        return [name for name, status in self._client_status.items() if status]
    
    def get_client_status(self) -> Dict[str, bool]:
        """
        Get status of all clients.
        
        Returns:
            Dictionary mapping client names to their availability status
        """
        return self._client_status.copy()    

    def retry_client_connection(self, client_name: str) -> bool:
        """
        Retry connection for a specific client.
        
        Args:
            client_name: Name of the client to retry
            
        Returns:
            True if successful, False otherwise
        """
        if client_name not in self._client_configs:
            logger.error(f"No configuration found for client: {client_name}")
            return False
        
        config = self._client_configs[client_name]
        logger.info(f"Retrying connection for {client_name} client")
        return self._initialize_client_with_retry(config)
    
    def get_connection_errors(self) -> Dict[str, str]:
        """
        Get connection error information for failed clients.
        
        Returns:
            Dictionary mapping client names to error descriptions
        """
        errors = {}
        for name, status in self._client_status.items():
            if not status:
                errors[name] = f"Client {name} is not available or failed to connect"
        return errors
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all clients.
        
        Returns:
            Dictionary with health status information
        """
        health_status = {
            "overall_status": "healthy",
            "clients": {},
            "available_tools_count": len(self.available_tools),
            "timestamp": time.time()
        }
        
        failed_clients = []
        
        for client_name in self._client_configs.keys():
            client_health = {
                "status": "healthy" if self.is_client_available(client_name) else "unhealthy",
                "required": self._client_configs[client_name].required
            }
            
            if not self.is_client_available(client_name):
                failed_clients.append(client_name)
                if self._client_configs[client_name].required:
                    health_status["overall_status"] = "critical"
                elif health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "degraded"
            
            health_status["clients"][client_name] = client_health
        
        health_status["failed_clients"] = failed_clients
        return health_status    
    
    def get_degradation_strategy(self) -> Dict[str, Any]:
        """
        Get the current graceful degradation strategy based on client availability.
        
        Returns:
            Dictionary describing the current degradation strategy
        """
        failed_clients = [name for name, status in self._client_status.items() if not status]
        return self.error_handler.get_degradation_strategy(failed_clients)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all MCP client errors.
        
        Returns:
            Dictionary with error summary information
        """
        return self.error_handler.get_error_summary()
    
    def get_performance_metrics(self, client_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring and analysis.
        
        Args:
            client_name: Optional client name to filter metrics
            
        Returns:
            Dictionary with performance metrics
        """
        from datetime import timedelta
        
        # Get metrics for different time windows
        metrics = {
            'last_hour': self.monitor.get_performance_summary(client_name, timedelta(hours=1)),
            'last_24_hours': self.monitor.get_performance_summary(client_name, timedelta(days=1)),
            'all_time': self.monitor.get_performance_summary(client_name)
        }
        
        return metrics
    
    def get_detailed_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report including monitoring data.
        
        Returns:
            Dictionary with detailed health information
        """
        # Get basic health check
        health = self.health_check()
        
        # Add monitoring data
        monitoring_report = self.monitor.get_client_health_report()
        performance_metrics = self.get_performance_metrics()
        
        # Combine all information
        detailed_report = {
            **health,
            'monitoring': monitoring_report,
            'performance': performance_metrics,
            'error_summary': self.get_error_summary()
        }
        
        return detailed_report
    
    def export_monitoring_data(self, filepath: str) -> None:
        """
        Export monitoring data for analysis.
        
        Args:
            filepath: Path to save monitoring data
        """
        self.monitor.export_metrics(filepath)
        logger.info(f"Monitoring data exported to {filepath}")
    
    def clear_old_metrics(self, older_than_hours: int = 24) -> None:
        """
        Clear old monitoring metrics to manage memory.
        
        Args:
            older_than_hours: Clear metrics older than this many hours
        """
        from datetime import timedelta
        self.monitor.clear_metrics(timedelta(hours=older_than_hours))
        logger.info(f"Cleared monitoring metrics older than {older_than_hours} hours")