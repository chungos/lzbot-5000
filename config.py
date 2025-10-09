"""
Configuration module for LZBot-5000 - AWS Landing Zone Designer
Handles environment variable loading for JIRA and Confluence integration with Pydantic validation.
"""

import os
from typing import Dict, Optional, Any
import logging
from pathlib import Path

# Try to import python-dotenv, fallback gracefully if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Try to import pydantic for modern validation
try:
    from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
    from pydantic_core import ValidationError as PydanticCoreValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Import custom exceptions
from lzbot.exceptions import ConfigurationError, ErrorHandler


class ConfigError(ConfigurationError):
    """Legacy exception for backward compatibility."""
    pass


if PYDANTIC_AVAILABLE:
    class JiraSettings(BaseModel):
        """JIRA configuration settings with validation."""
        model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)
        
        url: str = Field(..., description="JIRA instance URL", min_length=10)
        email: str = Field(..., description="JIRA user email", min_length=5)
        api_token: str = Field(..., description="JIRA API token", min_length=10)
        project_key: str = Field(..., description="JIRA project key", min_length=1)
        board_id: str = Field(default="1", description="JIRA board ID")
        
        @field_validator('url')
        @classmethod
        def validate_url(cls, v: str) -> str:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            return v.rstrip('/')
        
        @field_validator('email')
        @classmethod
        def validate_email(cls, v: str) -> str:
            if '@' not in v or '.' not in v:
                raise ValueError('Email must contain @ and .')
            return v.lower()
        
        @field_validator('api_token')
        @classmethod
        def validate_api_token(cls, v: str) -> str:
            if len(v) < 10:
                raise ValueError('API token must be at least 10 characters')
            return v

    class ConfluenceSettings(BaseModel):
        """Confluence configuration settings with validation."""
        model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)
        
        url: str = Field(..., description="Confluence instance URL", min_length=10)
        space_key: str = Field(..., description="Confluence space key", min_length=1)
        parent_page_id: Optional[str] = Field(default=None, description="Parent page ID for new pages")
        
        @field_validator('url')
        @classmethod
        def validate_url(cls, v: str) -> str:
            if not v.startswith(('http://', 'https://')):
                raise ValueError('URL must start with http:// or https://')
            return v.rstrip('/')

    class AWSSettings(BaseModel):
        """AWS configuration settings with validation."""
        model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)
        
        region: str = Field(default="ap-southeast-2", description="AWS region")
        profile: Optional[str] = Field(default=None, description="AWS profile name")

    class LZBotSettings(BaseModel):
        """Complete LZBot configuration with validation."""
        model_config = ConfigDict(
            str_strip_whitespace=True,
            validate_default=True,
            extra='forbid'
        )
        
        jira: JiraSettings
        confluence: ConfluenceSettings  
        aws: AWSSettings = Field(default_factory=AWSSettings)
        
        @classmethod
        def from_env(cls) -> 'LZBotSettings':
            """Create settings from environment variables."""
            _load_dotenv()
            
            try:
                return cls(
                    jira=JiraSettings(
                        url=os.getenv('JIRA_URL'),
                        email=os.getenv('JIRA_EMAIL'),
                        api_token=os.getenv('JIRA_API_TOKEN'),
                        project_key=os.getenv('JIRA_PROJECT_KEY'),
                        board_id=os.getenv('JIRA_BOARD_ID', '1')
                    ),
                    confluence=ConfluenceSettings(
                        url=os.getenv('CONFLUENCE_URL'),
                        space_key=os.getenv('CONFLUENCE_SPACE_KEY'),
                        parent_page_id=os.getenv('CONFLUENCE_PARENT_PAGE_ID')
                    ),
                    aws=AWSSettings(
                        region=os.getenv('AWS_REGION', 'ap-southeast-2'),
                        profile=os.getenv('AWS_PROFILE')
                    )
                )
            except (ValidationError, PydanticCoreValidationError) as e:
                error_msg = "Configuration validation failed:\n"
                if hasattr(e, 'errors'):
                    for error in e.errors():
                        field = '.'.join(str(x) for x in error['loc']) if error['loc'] else 'root'
                        error_msg += f"  - {field}: {error['msg']}\n"
                else:
                    error_msg += f"  - {str(e)}\n"
                raise ConfigurationError(error_msg) from e
        
        def to_env_dict(self) -> Dict[str, str]:
            """Convert settings to environment variables dictionary."""
            return {
                'JIRA_URL': self.jira.url,
                'JIRA_EMAIL': self.jira.email,
                'JIRA_API_TOKEN': self.jira.api_token,
                'JIRA_PROJECT_KEY': self.jira.project_key,
                'JIRA_BOARD_ID': self.jira.board_id,
                'CONFLUENCE_URL': self.confluence.url,
                'CONFLUENCE_SPACE_KEY': self.confluence.space_key,
                'CONFLUENCE_PARENT_PAGE_ID': self.confluence.parent_page_id or '',
                'AWS_REGION': self.aws.region,
                'AWS_PROFILE': self.aws.profile or ''
            }
        
        def get_jira_config(self) -> Dict[str, str]:
            """Get JIRA-specific configuration."""
            return {
                'JIRA_URL': self.jira.url,
                'JIRA_EMAIL': self.jira.email,
                'JIRA_API_TOKEN': self.jira.api_token,
                'JIRA_PROJECT_KEY': self.jira.project_key,
                'JIRA_BOARD_ID': self.jira.board_id
            }
        
        def get_confluence_config(self) -> Dict[str, str]:
            """Get Confluence-specific configuration."""
            config = {
                'CONFLUENCE_URL': self.confluence.url,
                'CONFLUENCE_SPACE_KEY': self.confluence.space_key
            }
            if self.confluence.parent_page_id:
                config['CONFLUENCE_PARENT_PAGE_ID'] = self.confluence.parent_page_id
            return config


def _load_dotenv():
    """Load environment variables from .env file if available."""
    env_file = Path(__file__).parent / '.env'
    
    if DOTENV_AVAILABLE:
        if env_file.exists():
            load_dotenv(env_file)
            logging.info(f"Loaded environment variables from {env_file}")
        else:
            logging.debug(f"No .env file found at {env_file}")
    else:
        # Manual .env file loading if python-dotenv is not available
        if env_file.exists():
            logging.info(f"Loading environment variables from {env_file} (manual)")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        else:
            logging.debug(f"No .env file found at {env_file}")


class Config:
    """Legacy configuration class for backward compatibility."""
    """Configuration class for managing environment variables."""
    
    # Required environment variables
    REQUIRED_VARS = [
        "JIRA_URL",
        "JIRA_EMAIL", 
        "JIRA_API_TOKEN",
        "JIRA_PROJECT_KEY",
        "CONFLUENCE_URL",
        "CONFLUENCE_SPACE_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    # Optional environment variables with defaults
    OPTIONAL_VARS = {
        "JIRA_BOARD_ID": "1",
        "CONFLUENCE_PARENT_PAGE_ID": None,
        "AWS_REGION": "ap-southeast-2",
        "AWS_SESSION_TOKEN": None  # Optional for temporary credentials
    }
    
    def __init__(self):
        """Initialize configuration by loading and validating environment variables."""
        self._config = {}
        self._load_dotenv()
        self._load_config()
        self._validate_config()
    
    def _load_dotenv(self):
        """Load environment variables from .env file if available."""
        env_file = Path(__file__).parent / '.env'
        
        if DOTENV_AVAILABLE:
            if env_file.exists():
                load_dotenv(env_file)
                print(f"📁 Loaded environment variables from {env_file}")
            else:
                print(f"📋 No .env file found at {env_file}")
        else:
            # Manual .env file loading if python-dotenv is not available
            if env_file.exists():
                print(f"📁 Loading environment variables from {env_file} (manual)")
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
            else:
                print(f"📋 No .env file found at {env_file}")
    
    def _load_config(self):
        """Load configuration from environment variables."""
        # Load required variables
        for var in self.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                raise ConfigError(f"Required environment variable '{var}' is not set")
            self._config[var] = value
        
        # Load optional variables with defaults
        for var, default in self.OPTIONAL_VARS.items():
            self._config[var] = os.getenv(var, default)
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate URLs
        if not self._config["JIRA_URL"].startswith(("http://", "https://")):
            raise ConfigError(f"JIRA_URL must start with http:// or https://")
        
        if not self._config["CONFLUENCE_URL"].startswith(("http://", "https://")):
            raise ConfigError(f"CONFLUENCE_URL must start with http:// or https://")
        
        # Validate email format (basic check)
        email = self._config["JIRA_EMAIL"]
        if "@" not in email or "." not in email:
            raise ConfigError(f"JIRA_EMAIL appears to be invalid: {email}")
        
        # Validate API token is not empty
        if len(self._config["JIRA_API_TOKEN"]) < 10:
            raise ConfigError("JIRA_API_TOKEN appears to be too short")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def get_jira_config(self) -> Dict[str, str]:
        """Get JIRA-specific configuration as a dictionary."""
        return {
            "JIRA_URL": self._config["JIRA_URL"],
            "JIRA_EMAIL": self._config["JIRA_EMAIL"],
            "JIRA_API_TOKEN": self._config["JIRA_API_TOKEN"],
            "JIRA_PROJECT_KEY": self._config["JIRA_PROJECT_KEY"],
            "JIRA_BOARD_ID": self._config["JIRA_BOARD_ID"]
        }
    
    def get_confluence_config(self) -> Dict[str, str]:
        """Get Confluence-specific configuration as a dictionary."""
        config = {
            "CONFLUENCE_URL": self._config["CONFLUENCE_URL"],
            "CONFLUENCE_SPACE_KEY": self._config["CONFLUENCE_SPACE_KEY"]
        }
        
        # Only add parent page ID if it's set
        if self._config["CONFLUENCE_PARENT_PAGE_ID"]:
            config["CONFLUENCE_PARENT_PAGE_ID"] = self._config["CONFLUENCE_PARENT_PAGE_ID"]
        
        return config
    
    def get_all_env_vars(self) -> Dict[str, str]:
        """Get all configuration as environment variables dict for MCP client."""
        env_vars = {}
        env_vars.update(self.get_jira_config())
        env_vars.update(self.get_confluence_config())
        return env_vars
    
    def print_config_summary(self, mask_sensitive: bool = True):
        """Print configuration summary for debugging."""
        print("🔧 Configuration Summary:")
        print("=" * 50)
        
        for key, value in self._config.items():
            if mask_sensitive and key in ["JIRA_API_TOKEN"]:
                # Mask API token for security
                masked_value = value[:8] + "*" * (len(value) - 12) + value[-4:] if len(value) > 12 else "*" * len(value)
                print(f"   {key}: {masked_value}")
            elif mask_sensitive and key in ["JIRA_EMAIL"]:
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


def load_config():
    """Load and return configuration instance using modern Pydantic validation when available."""
    try:
        if PYDANTIC_AVAILABLE:
            return LZBotSettings.from_env()
        else:
            return Config()
    except (ConfigError, ValidationError) as e:
        print(f"❌ Configuration Error: {e}")
        
        if PYDANTIC_AVAILABLE:
            print("\n📋 Required Environment Variables:")
            required_vars = [
                'JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY',
                'CONFLUENCE_URL', 'CONFLUENCE_SPACE_KEY'
            ]
            for var in required_vars:
                status = "✅" if os.getenv(var) else "❌"
                print(f"   {status} {var}")
            
            print("\n📋 Optional Environment Variables:")
            optional_vars = {
                'JIRA_BOARD_ID': '1',
                'CONFLUENCE_PARENT_PAGE_ID': 'None',
                'AWS_REGION': 'ap-southeast-2',
                'AWS_PROFILE': 'None'
            }
            for var, default in optional_vars.items():
                current_value = os.getenv(var, default)
                print(f"   📝 {var}: {current_value}")
        else:
            print("\n📋 Required Environment Variables:")
            for var in Config.REQUIRED_VARS:
                status = "✅" if os.getenv(var) else "❌"
                print(f"   {status} {var}")
            
            print("\n📋 Optional Environment Variables:")
            for var, default in Config.OPTIONAL_VARS.items():
                current_value = os.getenv(var, default)
                print(f"   📝 {var}: {current_value if current_value else 'Not set'}")
        
        print("\n💡 Example .env file:")
        print_example_env()
        raise


def validate_environment():
    """Validate environment and provide helpful error messages."""
    try:
        config = load_config()
        print("✅ Environment configuration is valid!")
        if hasattr(config, 'model_dump'):
            # Modern Pydantic config
            logging.info("Using Pydantic-based configuration validation")
        else:
            # Legacy config
            logging.info("Using legacy configuration validation")
        return config
    except (ConfigError, ValidationError):
        print("\n❌ Environment configuration is invalid!")
        return None


def print_example_env():
    """Print example environment configuration."""
    example_env = """
# JIRA Configuration
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="YOUR_PROJECT"
export JIRA_BOARD_ID="1"

# Confluence Configuration  
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="YOUR_SPACE"
export CONFLUENCE_PARENT_PAGE_ID="your-parent-page-id"

# AWS Configuration (optional)
export AWS_REGION="ap-southeast-2"
"""
    print(example_env)


def validate_environment():
    """Validate environment and provide helpful error messages."""
    try:
        config = load_config()
        print("✅ Environment configuration is valid!")
        return config
    except ConfigError:
        print("\n❌ Environment configuration is invalid!")
        return None


if __name__ == "__main__":
    # Test configuration when run directly
    print("🧪 Testing configuration...")
    config = validate_environment()
    if config:
        config.print_config_summary()