"""
Error handling utilities for MCP client connections.

This module provides utilities for handling MCP client connection failures,
logging errors, and implementing graceful degradation strategies.
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPErrorType(Enum):
    """Types of MCP errors."""
    CONNECTION_TIMEOUT = "connection_timeout"
    SERVER_UNAVAILABLE = "server_unavailable"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    CONFIGURATION_ERROR = "configuration_error"
    AUTHENTICATION_ERROR = "authentication_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MCPError:
    """Represents an MCP error with context."""
    error_type: MCPErrorType
    client_name: str
    message: str
    timestamp: datetime
    retry_count: int = 0
    is_recoverable: bool = True


class MCPErrorHandler:
    """
    Handles MCP client errors and implements graceful degradation strategies.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_history: List[MCPError] = []
        self.client_error_counts: Dict[str, int] = {}
        
    def handle_client_error(self, client_name: str, error: Exception, retry_count: int = 0) -> MCPError:
        """
        Handle and categorize a client error.
        
        Args:
            client_name: Name of the client that failed
            error: The exception that occurred
            retry_count: Number of retry attempts made
            
        Returns:
            MCPError object with categorized error information
        """
        error_type = self._categorize_error(error)
        
        mcp_error = MCPError(
            error_type=error_type,
            client_name=client_name,
            message=str(error),
            timestamp=datetime.now(),
            retry_count=retry_count,
            is_recoverable=self._is_recoverable_error(error_type)
        )
        
        self.error_history.append(mcp_error)
        self.client_error_counts[client_name] = self.client_error_counts.get(client_name, 0) + 1
        
        self._log_error(mcp_error)
        return mcp_error
    
    def _categorize_error(self, error: Exception) -> MCPErrorType:
        """
        Categorize an error based on its type and message.
        
        Args:
            error: The exception to categorize
            
        Returns:
            MCPErrorType enum value
        """
        error_str = str(error).lower()
        
        if "timeout" in error_str or "timed out" in error_str:
            return MCPErrorType.CONNECTION_TIMEOUT
        elif "connection" in error_str or "refused" in error_str:
            return MCPErrorType.SERVER_UNAVAILABLE
        elif "auth" in error_str or "permission" in error_str:
            return MCPErrorType.AUTHENTICATION_ERROR
        elif "config" in error_str or "invalid" in error_str:
            return MCPErrorType.CONFIGURATION_ERROR
        elif "tool" in error_str or "execution" in error_str:
            return MCPErrorType.TOOL_EXECUTION_ERROR
        else:
            return MCPErrorType.UNKNOWN_ERROR
    
    def _is_recoverable_error(self, error_type: MCPErrorType) -> bool:
        """
        Determine if an error type is recoverable.
        
        Args:
            error_type: The type of error
            
        Returns:
            True if the error is potentially recoverable
        """
        recoverable_errors = {
            MCPErrorType.CONNECTION_TIMEOUT,
            MCPErrorType.SERVER_UNAVAILABLE,
            MCPErrorType.TOOL_EXECUTION_ERROR,
            MCPErrorType.UNKNOWN_ERROR
        }
        return error_type in recoverable_errors
    
    def _log_error(self, mcp_error: MCPError) -> None:
        """
        Log an MCP error with appropriate level.
        
        Args:
            mcp_error: The error to log
        """
        log_message = (
            f"MCP Client Error - {mcp_error.client_name}: "
            f"{mcp_error.error_type.value} - {mcp_error.message}"
        )
        
        if mcp_error.retry_count > 0:
            log_message += f" (retry {mcp_error.retry_count})"
        
        if mcp_error.error_type in [MCPErrorType.CONFIGURATION_ERROR, MCPErrorType.AUTHENTICATION_ERROR]:
            logger.error(log_message)
        elif mcp_error.error_type == MCPErrorType.SERVER_UNAVAILABLE:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def should_retry(self, client_name: str, max_retries: int = 3) -> bool:
        """
        Determine if a client should be retried based on error history.
        
        Args:
            client_name: Name of the client
            max_retries: Maximum number of retries allowed
            
        Returns:
            True if retry should be attempted
        """
        error_count = self.client_error_counts.get(client_name, 0)
        
        # Don't retry if we've exceeded max retries
        if error_count >= max_retries:
            return False
        
        # Check recent errors for this client
        recent_errors = [
            error for error in self.error_history[-10:]  # Last 10 errors
            if error.client_name == client_name
        ]
        
        # Don't retry if recent errors are non-recoverable
        if recent_errors and not recent_errors[-1].is_recoverable:
            return False
        
        return True
    
    def get_degradation_strategy(self, failed_clients: List[str]) -> Dict[str, Any]:
        """
        Get graceful degradation strategy based on failed clients.
        
        Args:
            failed_clients: List of client names that have failed
            
        Returns:
            Dictionary describing the degradation strategy
        """
        strategy = {
            "mode": "full",
            "available_features": [],
            "warnings": [],
            "fallback_actions": []
        }
        
        if "diagram" in failed_clients:
            if "knowledge" in failed_clients and "pricing" in failed_clients:
                strategy["mode"] = "basic"
                strategy["warnings"].append("All MCP services unavailable - basic agent response only")
                strategy["fallback_actions"].append("Provide text-based architectural guidance")
            elif "knowledge" in failed_clients:
                strategy["mode"] = "diagram_pricing"
                strategy["available_features"] = ["diagram_generation", "cost_estimation"]
                strategy["warnings"].append("Knowledge service unavailable - limited best practices")
            elif "pricing" in failed_clients:
                strategy["mode"] = "diagram_knowledge"
                strategy["available_features"] = ["diagram_generation", "documentation_access"]
                strategy["warnings"].append("Pricing service unavailable - no cost estimates")
            else:
                strategy["mode"] = "knowledge_pricing"
                strategy["available_features"] = ["documentation_access", "cost_estimation"]
                strategy["warnings"].append("Diagram service unavailable - text-based designs only")
        else:
            # Diagram service is available
            if "knowledge" in failed_clients and "pricing" in failed_clients:
                strategy["mode"] = "diagram_only"
                strategy["available_features"] = ["diagram_generation"]
                strategy["warnings"].append("Knowledge and pricing services unavailable")
            elif "knowledge" in failed_clients:
                strategy["mode"] = "diagram_pricing"
                strategy["available_features"] = ["diagram_generation", "cost_estimation"]
                strategy["warnings"].append("Knowledge service unavailable")
            elif "pricing" in failed_clients:
                strategy["mode"] = "diagram_knowledge"
                strategy["available_features"] = ["diagram_generation", "documentation_access"]
                strategy["warnings"].append("Pricing service unavailable")
            else:
                strategy["mode"] = "full"
                strategy["available_features"] = ["diagram_generation", "documentation_access", "cost_estimation"]
        
        return strategy
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors encountered.
        
        Returns:
            Dictionary with error summary information
        """
        if not self.error_history:
            return {"total_errors": 0, "clients_affected": 0}
        
        error_types = {}
        clients_affected = set()
        
        for error in self.error_history:
            error_types[error.error_type.value] = error_types.get(error.error_type.value, 0) + 1
            clients_affected.add(error.client_name)
        
        return {
            "total_errors": len(self.error_history),
            "clients_affected": len(clients_affected),
            "error_types": error_types,
            "client_error_counts": self.client_error_counts.copy(),
            "most_recent_error": self.error_history[-1].timestamp if self.error_history else None
        }
    
    def clear_error_history(self, client_name: Optional[str] = None) -> None:
        """
        Clear error history for a specific client or all clients.
        
        Args:
            client_name: Optional client name to clear errors for. If None, clears all.
        """
        if client_name:
            self.error_history = [error for error in self.error_history if error.client_name != client_name]
            self.client_error_counts.pop(client_name, None)
            logger.info(f"Cleared error history for {client_name}")
        else:
            self.error_history.clear()
            self.client_error_counts.clear()
            logger.info("Cleared all error history")