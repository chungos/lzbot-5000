"""
Conversation Management Module for LZBot-5000

This module provides conversation state management and flow control.
Now uses native Strands conversation detection capabilities.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # "user" or "assistant" 
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.role.title()}: {self.content[:100]}{'...' if len(self.content) > 100 else ''}"


class ConversationState:
    """Manages the state of a conversation session."""
    
    def __init__(self):
        """Initialize conversation state."""
        self.messages: List[ConversationMessage] = []
        self.has_gathered_requirements: bool = False
        self.is_complete: bool = False
        self.gathered_info: Dict[str, Any] = {}
        logger.debug("ConversationState initialized")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        message = ConversationMessage(role=role, content=content)
        self.messages.append(message)
        logger.debug(f"Added {role} message to conversation (total: {len(self.messages)})")
    
    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Get conversation context for the agent."""
        if not self.messages:
            return ""
        
        context_parts = ["Previous conversation:"]
        recent_messages = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        
        for msg in recent_messages:
            context_parts.append(str(msg))
        
        return "\n".join(context_parts) + "\n\nPlease continue the conversation:"
    
    def get_user_messages(self) -> List[ConversationMessage]:
        """Get all user messages from the conversation."""
        return [msg for msg in self.messages if msg.role == "user"]
    
    def get_assistant_messages(self) -> List[ConversationMessage]:
        """Get all assistant messages from the conversation."""
        return [msg for msg in self.messages if msg.role == "assistant"]
    
    def get_last_message(self) -> ConversationMessage:
        """Get the last message in the conversation."""
        if not self.messages:
            raise ValueError("No messages in conversation")
        return self.messages[-1]
    
    def clear_messages(self) -> None:
        """Clear all conversation messages."""
        logger.info("Clearing conversation messages")
        self.messages.clear()
        self.has_gathered_requirements = False
        self.is_complete = False
        self.gathered_info.clear()


class ConversationManager:
    """High-level manager for conversation flow and state using native Strands detection."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self.state = ConversationState()
        logger.info("ConversationManager initialized with native Strands detection")
    
    def start_new_conversation(self) -> None:
        """Start a new conversation by resetting state."""
        logger.info("Starting new conversation")
        self.state = ConversationState()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self.state.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self.state.add_message("assistant", content)
    
    def should_continue_conversation(self, agent_response: str) -> bool:
        """
        DEPRECATED: Use native Strands conversation detection instead.
        This method is kept for backward compatibility but should not be used.
        """
        logger.warning("should_continue_conversation is deprecated. Use native Strands detection.")
        # Fallback: basic question mark detection
        return '?' in agent_response if agent_response else False
    
    def mark_requirements_gathered(self) -> None:
        """Mark that sufficient requirements have been gathered."""
        logger.info("Marking requirements as gathered")
        self.state.has_gathered_requirements = True
    
    def is_ready_for_implementation(self) -> bool:
        """Check if conversation is ready for implementation."""
        return self.state.has_gathered_requirements or self.state.is_complete
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation state."""
        last_agent_message = None
        for msg in reversed(self.state.messages):
            if msg.role == "assistant":
                last_agent_message = msg.content
                break
        
        # Simplified analysis without the complex analyzer
        basic_analysis = {
            "has_questions": '?' in (last_agent_message or ''),
            "response_length": len(last_agent_message) if last_agent_message else 0,
            "note": "Using simplified analysis - complex ConversationAnalyzer removed"
        }
        
        return {
            "message_count": len(self.state.messages),
            "user_messages": len(self.state.get_user_messages()),
            "assistant_messages": len(self.state.get_assistant_messages()),
            "has_gathered_requirements": self.state.has_gathered_requirements,
            "is_complete": self.state.is_complete,
            "last_interaction": self.state.messages[-1].timestamp if self.state.messages else None,
            "is_ready_for_implementation": self.is_ready_for_implementation(),
            "conversation_analysis": basic_analysis
        }
    
    def analyze_last_agent_response(self) -> Dict[str, Any]:
        """
        DEPRECATED: Use native Strands conversation detection instead.
        """
        logger.warning("analyze_last_agent_response is deprecated. Use native Strands detection.")
        
        last_agent_message = None
        for msg in reversed(self.state.messages):
            if msg.role == "assistant":
                last_agent_message = msg.content
                break
        
        if not last_agent_message:
            return {"error": "No agent messages found in conversation"}
        
        # Basic fallback analysis
        return {
            "has_questions": '?' in last_agent_message,
            "response_length": len(last_agent_message),
            "note": "Simplified analysis - use native Strands detection for accurate results"
        }
    
    def format_multi_question_prompt(self, agent_response: str) -> str:
        """
        Simplified prompt for multi-question scenarios.
        
        Args:
            agent_response: The agent's response containing multiple questions
            
        Returns:
            Simple formatted prompt
        """
        # Simple check for multiple questions
        question_count = agent_response.count('?') if agent_response else 0
        
        if question_count <= 1:
            return "Please provide your response:"
        
        # Simple, clean prompt without complex analysis
        return "The agent has asked multiple questions. Please provide a comprehensive response addressing all the questions above."
    
    def get_context_for_agent(self, max_messages: int = 10) -> str:
        """Get conversation context formatted for the agent."""
        return self.state.get_conversation_context(max_messages)