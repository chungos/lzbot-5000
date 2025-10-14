"""
Monitoring and performance tracking for MCP client operations.

This module provides comprehensive monitoring capabilities for MCP client
connections, tool execution performance, and system health metrics.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from threading import Lock
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a performance metric for MCP operations."""
    operation: str
    client_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientHealthMetric:
    """Represents health metrics for an MCP client."""
    client_name: str
    timestamp: datetime
    is_connected: bool
    response_time: Optional[float] = None
    tool_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class MCPMonitor:
    """
    Comprehensive monitoring system for MCP client operations.
    
    Tracks performance metrics, connection health, and provides
    detailed logging and reporting capabilities.
    """
    
    def __init__(self, max_metrics_history: int = 1000):
        """
        Initialize the MCP monitor.
        
        Args:
            max_metrics_history: Maximum number of performance metrics to retain
        """
        self.max_metrics_history = max_metrics_history
        self.performance_metrics: List[PerformanceMetric] = []
        self.client_health: Dict[str, ClientHealthMetric] = {}
        self.connection_events: List[Dict[str, Any]] = []
        self._lock = Lock()
        
        # Performance thresholds (in seconds)
        self.slow_operation_threshold = 5.0
        self.very_slow_operation_threshold = 10.0
        
        logger.info("MCP Monitor initialized")
    
    @contextmanager
    def track_operation(self, operation: str, client_name: str, **metadata):
        """
        Context manager to track the performance of an MCP operation.
        
        Args:
            operation: Name of the operation being tracked
            client_name: Name of the MCP client
            **metadata: Additional metadata to store with the metric
        """
        metric = PerformanceMetric(
            operation=operation,
            client_name=client_name,
            start_time=time.time(),
            metadata=metadata
        )
        
        try:
            logger.debug(f"Starting {operation} for {client_name}")
            yield metric
            
            # Mark as successful
            metric.success = True
            
        except Exception as e:
            # Mark as failed and capture error
            metric.success = False
            metric.error_message = str(e)
            logger.error(f"Operation {operation} failed for {client_name}: {e}")
            raise
            
        finally:
            # Calculate duration and store metric
            metric.end_time = time.time()
            metric.duration = metric.end_time - metric.start_time
            
            self._store_performance_metric(metric)
            self._log_performance_metric(metric)
    
    def _store_performance_metric(self, metric: PerformanceMetric) -> None:
        """Store a performance metric with thread safety."""
        with self._lock:
            self.performance_metrics.append(metric)
            
            # Maintain maximum history size
            if len(self.performance_metrics) > self.max_metrics_history:
                self.performance_metrics = self.performance_metrics[-self.max_metrics_history:]
    
    def _log_performance_metric(self, metric: PerformanceMetric) -> None:
        """Log performance metric with appropriate level based on performance."""
        duration = metric.duration or 0
        
        if not metric.success:
            logger.error(
                f"MCP Operation Failed - {metric.client_name}.{metric.operation}: "
                f"{metric.error_message} (duration: {duration:.2f}s)"
            )
        elif duration > self.very_slow_operation_threshold:
            logger.warning(
                f"Very Slow MCP Operation - {metric.client_name}.{metric.operation}: "
                f"{duration:.2f}s (threshold: {self.very_slow_operation_threshold}s)"
            )
        elif duration > self.slow_operation_threshold:
            logger.warning(
                f"Slow MCP Operation - {metric.client_name}.{metric.operation}: "
                f"{duration:.2f}s (threshold: {self.slow_operation_threshold}s)"
            )
        else:
            logger.debug(
                f"MCP Operation Completed - {metric.client_name}.{metric.operation}: "
                f"{duration:.2f}s"
            )
    
    def record_connection_event(self, client_name: str, event_type: str, 
                              success: bool, details: Optional[str] = None) -> None:
        """
        Record a connection event for monitoring.
        
        Args:
            client_name: Name of the MCP client
            event_type: Type of event (connect, disconnect, retry, etc.)
            success: Whether the event was successful
            details: Additional details about the event
        """
        event = {
            'timestamp': datetime.now(),
            'client_name': client_name,
            'event_type': event_type,
            'success': success,
            'details': details
        }
        
        with self._lock:
            self.connection_events.append(event)
            
            # Maintain reasonable history size
            if len(self.connection_events) > 500:
                self.connection_events = self.connection_events[-500:]
        
        # Log the event
        level = logging.INFO if success else logging.ERROR
        logger.log(level, f"MCP Connection Event - {client_name}: {event_type} "
                         f"({'success' if success else 'failed'})"
                         f"{f' - {details}' if details else ''}")
    
    def update_client_health(self, client_name: str, is_connected: bool,
                           response_time: Optional[float] = None,
                           tool_count: int = 0, error_count: int = 0,
                           last_error: Optional[str] = None) -> None:
        """
        Update health metrics for a specific client.
        
        Args:
            client_name: Name of the MCP client
            is_connected: Whether the client is currently connected
            response_time: Recent response time in seconds
            tool_count: Number of available tools
            error_count: Number of recent errors
            last_error: Most recent error message
        """
        health_metric = ClientHealthMetric(
            client_name=client_name,
            timestamp=datetime.now(),
            is_connected=is_connected,
            response_time=response_time,
            tool_count=tool_count,
            error_count=error_count,
            last_error=last_error
        )
        
        with self._lock:
            self.client_health[client_name] = health_metric
        
        # Log health status changes
        if is_connected:
            logger.info(f"Client Health Update - {client_name}: Connected "
                       f"(tools: {tool_count}, response: {response_time:.2f}s)"
                       if response_time else f"(tools: {tool_count})")
        else:
            logger.warning(f"Client Health Update - {client_name}: Disconnected "
                          f"(errors: {error_count})"
                          f"{f' - {last_error}' if last_error else ''}")
    
    def get_performance_summary(self, client_name: Optional[str] = None,
                              time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get performance summary for monitoring and reporting.
        
        Args:
            client_name: Optional client name to filter by
            time_window: Optional time window to filter metrics
            
        Returns:
            Dictionary with performance summary statistics
        """
        with self._lock:
            metrics = self.performance_metrics.copy()
        
        # Filter by client name if specified
        if client_name:
            metrics = [m for m in metrics if m.client_name == client_name]
        
        # Filter by time window if specified
        if time_window:
            cutoff_time = time.time() - time_window.total_seconds()
            metrics = [m for m in metrics if m.start_time >= cutoff_time]
        
        if not metrics:
            return {
                'total_operations': 0,
                'success_rate': 0.0,
                'average_duration': 0.0,
                'slow_operations': 0,
                'failed_operations': 0
            }
        
        # Calculate statistics
        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]
        durations = [m.duration for m in successful_metrics if m.duration is not None]
        
        slow_operations = len([d for d in durations if d > self.slow_operation_threshold])
        
        summary = {
            'total_operations': len(metrics),
            'successful_operations': len(successful_metrics),
            'failed_operations': len(failed_metrics),
            'success_rate': len(successful_metrics) / len(metrics) * 100,
            'average_duration': sum(durations) / len(durations) if durations else 0.0,
            'min_duration': min(durations) if durations else 0.0,
            'max_duration': max(durations) if durations else 0.0,
            'slow_operations': slow_operations,
            'slow_operation_rate': slow_operations / len(durations) * 100 if durations else 0.0,
            'time_window': str(time_window) if time_window else 'all_time'
        }
        
        return summary
    
    def get_client_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for all clients.
        
        Returns:
            Dictionary with health information for all clients
        """
        with self._lock:
            health_data = self.client_health.copy()
            recent_events = self.connection_events[-50:]  # Last 50 events
        
        report = {
            'timestamp': datetime.now(),
            'clients': {},
            'overall_status': 'healthy',
            'recent_events': recent_events
        }
        
        unhealthy_clients = 0
        
        for client_name, health in health_data.items():
            client_report = {
                'is_connected': health.is_connected,
                'last_update': health.timestamp,
                'response_time': health.response_time,
                'tool_count': health.tool_count,
                'error_count': health.error_count,
                'last_error': health.last_error,
                'status': 'healthy' if health.is_connected and health.error_count == 0 else 'unhealthy'
            }
            
            if client_report['status'] == 'unhealthy':
                unhealthy_clients += 1
            
            report['clients'][client_name] = client_report
        
        # Determine overall status
        if unhealthy_clients == 0:
            report['overall_status'] = 'healthy'
        elif unhealthy_clients < len(health_data):
            report['overall_status'] = 'degraded'
        else:
            report['overall_status'] = 'critical'
        
        return report
    
    def export_metrics(self, filepath: str, format: str = 'json') -> None:
        """
        Export monitoring data to file for analysis.
        
        Args:
            filepath: Path to save the exported data
            format: Export format ('json' or 'csv')
        """
        with self._lock:
            data = {
                'performance_metrics': [
                    {
                        'operation': m.operation,
                        'client_name': m.client_name,
                        'start_time': m.start_time,
                        'duration': m.duration,
                        'success': m.success,
                        'error_message': m.error_message,
                        'metadata': m.metadata
                    }
                    for m in self.performance_metrics
                ],
                'client_health': {
                    name: {
                        'client_name': health.client_name,
                        'timestamp': health.timestamp.isoformat(),
                        'is_connected': health.is_connected,
                        'response_time': health.response_time,
                        'tool_count': health.tool_count,
                        'error_count': health.error_count,
                        'last_error': health.last_error
                    }
                    for name, health in self.client_health.items()
                },
                'connection_events': [
                    {
                        'timestamp': event['timestamp'].isoformat(),
                        'client_name': event['client_name'],
                        'event_type': event['event_type'],
                        'success': event['success'],
                        'details': event['details']
                    }
                    for event in self.connection_events
                ]
            }
        
        if format.lower() == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Monitoring data exported to {filepath}")
    
    def clear_metrics(self, older_than: Optional[timedelta] = None) -> None:
        """
        Clear old metrics to manage memory usage.
        
        Args:
            older_than: Optional timedelta to clear metrics older than this period
        """
        with self._lock:
            if older_than:
                cutoff_time = time.time() - older_than.total_seconds()
                self.performance_metrics = [
                    m for m in self.performance_metrics 
                    if m.start_time >= cutoff_time
                ]
                
                cutoff_datetime = datetime.now() - older_than
                self.connection_events = [
                    e for e in self.connection_events
                    if e['timestamp'] >= cutoff_datetime
                ]
            else:
                self.performance_metrics.clear()
                self.connection_events.clear()
        
        logger.info(f"Cleared monitoring metrics older than {older_than}")