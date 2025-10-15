"""
MCP Client Configuration System.

This module provides configuration loading, validation, and management
for MCP clients with timeout and retry options.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MCPClientConfig:
    """Configuration for an MCP client."""
    name: str
    command: str
    args: List[str]
    required: bool = False
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    def validate(self) -> None:
        """
        Validate the configuration parameters.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.name:
            raise ValueError("Client name cannot be empty")
        
        if not self.command:
            raise ValueError("Command cannot be empty")
        
        if not isinstance(self.args, list):
            raise ValueError("Args must be a list")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")
        
        if self.retry_delay < 0:
            raise ValueError("Retry delay cannot be negative")


class MCPConfigManager:
    """
    Manages MCP client configurations including loading and validation.
    """
    
    DEFAULT_CONFIGS = {
        "diagram": MCPClientConfig(
            name="diagram",
            command="uvx",
            args=["awslabs.aws-diagram-mcp-server@latest"],
            required=True,
            timeout=30
        ),
        "knowledge": MCPClientConfig(
            name="knowledge", 
            command="uvx",
            args=["awslabs.aws-documentation-mcp-server@latest"],
            required=False,
            timeout=45
        ),
        "pricing": MCPClientConfig(
            name="pricing",
            command="uvx", 
            args=["awslabs.aws-pricing-mcp-server@latest"],
            required=False,
            timeout=30
        )
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.config_file = config_file
        self._configs: Dict[str, MCPClientConfig] = {}
        
    def load_configurations(self) -> List[MCPClientConfig]:
        """
        Load MCP client configurations from file or use defaults.
        
        Returns:
            List of validated MCPClientConfig objects
            
        Raises:
            ValueError: If configuration validation fails
        """
        if self.config_file and Path(self.config_file).exists():
            try:
                configs = self._load_from_file(self.config_file)
                logger.info(f"Loaded configurations from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                logger.info("Using default configurations")
                configs = self._get_default_configs()
        else:
            logger.info("Using default MCP client configurations")
            configs = self._get_default_configs()
        
        # Validate all configurations
        for config in configs:
            config.validate()
            
        self._configs = {config.name: config for config in configs}
        return configs
    
    def _load_from_file(self, config_file: str) -> List[MCPClientConfig]:
        """
        Load configurations from JSON file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            List of MCPClientConfig objects
        """
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        configs = []
        for client_data in data.get('mcp_clients', []):
            config = MCPClientConfig(**client_data)
            configs.append(config)
            
        return configs
    
    def _get_default_configs(self) -> List[MCPClientConfig]:
        """
        Get default MCP client configurations.
        
        Returns:
            List of default MCPClientConfig objects
        """
        return list(self.DEFAULT_CONFIGS.values())
    
    def get_config(self, name: str) -> Optional[MCPClientConfig]:
        """
        Get configuration for a specific client.
        
        Args:
            name: Client name
            
        Returns:
            MCPClientConfig if found, None otherwise
        """
        return self._configs.get(name)
    
    def save_configurations(self, config_file: str) -> None:
        """
        Save current configurations to file.
        
        Args:
            config_file: Path to save configuration file
        """
        data = {
            'mcp_clients': [asdict(config) for config in self._configs.values()]
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Saved configurations to {config_file}")
    
    def update_config(self, name: str, **kwargs) -> None:
        """
        Update configuration for a specific client.
        
        Args:
            name: Client name
            **kwargs: Configuration parameters to update
        """
        if name not in self._configs:
            raise ValueError(f"Client {name} not found in configurations")
        
        config = self._configs[name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            else:
                raise ValueError(f"Invalid configuration parameter: {key}")
        
        # Validate updated configuration
        config.validate()
        logger.info(f"Updated configuration for {name}")
    
    def add_config(self, config: MCPClientConfig) -> None:
        """
        Add a new client configuration.
        
        Args:
            config: MCPClientConfig object to add
        """
        config.validate()
        self._configs[config.name] = config
        logger.info(f"Added configuration for {config.name}")
    
    def remove_config(self, name: str) -> None:
        """
        Remove a client configuration.
        
        Args:
            name: Client name to remove
        """
        if name in self._configs:
            del self._configs[name]
            logger.info(f"Removed configuration for {name}")
        else:
            logger.warning(f"Configuration {name} not found for removal")
    
    def list_configs(self) -> List[str]:
        """
        List all configured client names.
        
        Returns:
            List of client names
        """
        return list(self._configs.keys())