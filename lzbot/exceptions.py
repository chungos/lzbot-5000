"""
Custom exception types for LZBot-5000
Provides specific exception classes for different error scenarios with proper context.
"""

from typing import Optional, Dict, Any


class LZBotError(Exception):
    """Base exception class for all LZBot-5000 errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class ConfigurationError(LZBotError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, missing_vars: Optional[list] = None, context: Optional[Dict[str, Any]] = None):
        self.missing_vars = missing_vars or []
        if missing_vars:
            message += f" Missing variables: {', '.join(missing_vars)}"
        super().__init__(message, context)


class MCPClientError(LZBotError):
    """Raised when MCP client operations fail."""
    
    def __init__(self, message: str, client_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.client_type = client_type
        context = context or {}
        if client_type:
            context['client_type'] = client_type
        super().__init__(message, context)


class MCPConnectionError(MCPClientError):
    """Raised when MCP client connection fails."""
    pass


class MCPToolError(MCPClientError):
    """Raised when MCP tool execution fails."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, client_type: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.tool_name = tool_name
        context = context or {}
        if tool_name:
            context['tool_name'] = tool_name
        super().__init__(message, client_type, context)


class AgentError(LZBotError):
    """Raised when AI agent operations fail."""
    
    def __init__(self, message: str, agent_action: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.agent_action = agent_action
        context = context or {}
        if agent_action:
            context['agent_action'] = agent_action
        super().__init__(message, context)


class ModelError(AgentError):
    """Raised when AI model operations fail."""
    
    def __init__(self, message: str, model_name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.model_name = model_name
        context = context or {}
        if model_name:
            context['model_name'] = model_name
        super().__init__(message, context=context)


class FileOperationError(LZBotError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.operation = operation
        context = context or {}
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        super().__init__(message, context)


class ValidationError(LZBotError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[Any] = None, context: Optional[Dict[str, Any]] = None):
        self.field_name = field_name
        self.field_value = field_value
        context = context or {}
        if field_name:
            context['field_name'] = field_name
        if field_value:
            context['field_value'] = str(field_value)
        super().__init__(message, context)


class JiraIntegrationError(LZBotError):
    """Raised when JIRA integration operations fail."""
    
    def __init__(self, message: str, jira_operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.jira_operation = jira_operation
        context = context or {}
        if jira_operation:
            context['jira_operation'] = jira_operation
        super().__init__(message, context)


class ConfluenceIntegrationError(LZBotError):
    """Raised when Confluence integration operations fail."""
    
    def __init__(self, message: str, confluence_operation: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.confluence_operation = confluence_operation
        context = context or {}
        if confluence_operation:
            context['confluence_operation'] = confluence_operation
        super().__init__(message, context)


class AWSIntegrationError(LZBotError):
    """Raised when AWS integration operations fail."""
    
    def __init__(self, message: str, aws_service: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        self.aws_service = aws_service
        context = context or {}
        if aws_service:
            context['aws_service'] = aws_service
        super().__init__(message, context)


# Exception handling utilities
class ErrorHandler:
    """Centralized error handling utilities."""
    
    @staticmethod
    def handle_mcp_error(error: Exception, client_type: str, operation: str) -> MCPClientError:
        """Convert generic exceptions to specific MCP errors."""
        if isinstance(error, MCPClientError):
            return error
        
        if "connection" in str(error).lower() or "timeout" in str(error).lower():
            return MCPConnectionError(
                f"Failed to connect to {client_type} MCP server during {operation}",
                client_type=client_type,
                context={'original_error': str(error)}
            )
        
        return MCPClientError(
            f"MCP {client_type} operation failed: {operation}",
            client_type=client_type,
            context={'original_error': str(error)}
        )
    
    @staticmethod
    def handle_file_error(error: Exception, file_path: str, operation: str) -> FileOperationError:
        """Convert generic file exceptions to FileOperationError."""
        if isinstance(error, FileOperationError):
            return error
        
        return FileOperationError(
            f"File {operation} failed for {file_path}: {str(error)}",
            file_path=file_path,
            operation=operation,
            context={'original_error': str(error)}
        )
    
    @staticmethod
    def handle_validation_error(error: Exception, field_name: str = None) -> ValidationError:
        """Convert generic validation exceptions to ValidationError."""
        if isinstance(error, ValidationError):
            return error
        
        return ValidationError(
            f"Validation failed: {str(error)}",
            field_name=field_name,
            context={'original_error': str(error)}
        )
    
    @staticmethod
    def format_error_for_user(error: LZBotError) -> str:
        """Format error message for end-user display."""
        user_message = f"❌ {error.message}"
        
        # Add helpful context for specific error types
        if isinstance(error, ConfigurationError):
            if error.missing_vars:
                user_message += f"\n💡 Please set the following environment variables: {', '.join(error.missing_vars)}"
        
        elif isinstance(error, MCPConnectionError):
            user_message += "\n💡 Check your internet connection and ensure MCP servers are accessible"
        
        elif isinstance(error, FileOperationError):
            user_message += f"\n💡 Check file permissions and disk space for: {error.file_path}"
        
        elif isinstance(error, ValidationError):
            user_message += f"\n💡 Please check the format of: {error.field_name}"
        
        return user_message


def handle_exception(func):
    """Decorator to handle exceptions and convert them to appropriate LZBot exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LZBotError:
            # Re-raise LZBot exceptions as-is
            raise
        except Exception as e:
            # Convert generic exceptions to LZBotError
            raise LZBotError(
                f"Unexpected error in {func.__name__}: {str(e)}",
                context={'function': func.__name__, 'original_error': str(e)}
            ) from e
    
    return wrapper