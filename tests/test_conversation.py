"""
Test cases for conversational functionality in LZBot-5000

Tests the conversation state management and interactive dialogue features.
Note: ConversationAnalyzer tests removed as class was deprecated in favor of native Strands detection.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lzbot.conversation import ConversationState, ConversationMessage, ConversationManager
from lzbot.exceptions import ValidationError, AgentError, ModelError


class TestConversationState(unittest.TestCase):
    """Test conversation state management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.conversation_state = ConversationState()
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        self.conversation_state.add_message("user", "Hello")
        self.assertEqual(len(self.conversation_state.messages), 1)
        
        message = self.conversation_state.messages[0]
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello")
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_get_conversation_context(self):
        """Test getting conversation context."""
        # Empty conversation
        context = self.conversation_state.get_conversation_context()
        self.assertEqual(context, "")
        
        # With messages
        self.conversation_state.add_message("user", "Design an AWS architecture")
        self.conversation_state.add_message("assistant", "What's your company size?")
        
        context = self.conversation_state.get_conversation_context()
        self.assertIn("Previous conversation:", context)
        self.assertIn("Design an AWS architecture", context)
        self.assertIn("What's your company size?", context)
    
    def test_get_user_messages(self):
        """Test filtering user messages."""
        self.conversation_state.add_message("user", "Hello")
        self.conversation_state.add_message("assistant", "Hi there")
        self.conversation_state.add_message("user", "How are you?")
        
        user_messages = self.conversation_state.get_user_messages()
        self.assertEqual(len(user_messages), 2)
        self.assertEqual(user_messages[0].content, "Hello")
        self.assertEqual(user_messages[1].content, "How are you?")
    
    def test_get_assistant_messages(self):
        """Test filtering assistant messages."""
        self.conversation_state.add_message("user", "Hello")
        self.conversation_state.add_message("assistant", "Hi there")
        self.conversation_state.add_message("assistant", "How can I help?")
        
        assistant_messages = self.conversation_state.get_assistant_messages()
        self.assertEqual(len(assistant_messages), 2)
        self.assertEqual(assistant_messages[0].content, "Hi there")
        self.assertEqual(assistant_messages[1].content, "How can I help?")
    
    def test_get_last_message(self):
        """Test getting the last message."""
        with self.assertRaises(ValueError):
            self.conversation_state.get_last_message()
        
        self.conversation_state.add_message("user", "First message")
        self.conversation_state.add_message("assistant", "Second message")
        
        last_message = self.conversation_state.get_last_message()
        self.assertEqual(last_message.content, "Second message")
    
    def test_clear_messages(self):
        """Test clearing all messages."""
        self.conversation_state.add_message("user", "Hello")
        self.conversation_state.has_gathered_requirements = True
        self.conversation_state.is_complete = True
        
        self.conversation_state.clear_messages()
        
        self.assertEqual(len(self.conversation_state.messages), 0)
        self.assertFalse(self.conversation_state.has_gathered_requirements)
        self.assertFalse(self.conversation_state.is_complete)


class TestConversationMessage(unittest.TestCase):
    """Test individual conversation messages."""
    
    def test_message_creation(self):
        """Test creating a conversation message."""
        message = ConversationMessage("user", "Hello world")
        
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello world")
        self.assertIsInstance(message.timestamp, datetime)
    
    def test_message_string_representation(self):
        """Test message string representation."""
        message = ConversationMessage("assistant", "This is a response")
        
        str_repr = str(message)
        self.assertIn("Assistant:", str_repr)
        self.assertIn("This is a response", str_repr)
    
    def test_long_message_truncation(self):
        """Test long message truncation in string representation."""
        long_content = "A" * 150  # Longer than 100 characters
        message = ConversationMessage("user", long_content)
        
        str_repr = str(message)
        self.assertIn("...", str_repr)
        self.assertTrue(len(str_repr) < len(long_content) + 50)  # Should be truncated


class TestConversationManager(unittest.TestCase):
    """Test conversation management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ConversationManager()
    
    def test_start_new_conversation(self):
        """Test starting a new conversation."""
        # Add some initial state
        self.manager.add_user_message("Hello")
        self.manager.mark_requirements_gathered()
        
        # Start new conversation
        self.manager.start_new_conversation()
        
        self.assertEqual(len(self.manager.state.messages), 0)
        self.assertFalse(self.manager.state.has_gathered_requirements)
    
    def test_add_messages(self):
        """Test adding user and assistant messages."""
        self.manager.add_user_message("User message")
        self.manager.add_assistant_message("Assistant response")
        
        self.assertEqual(len(self.manager.state.messages), 2)
        self.assertEqual(self.manager.state.messages[0].role, "user")
        self.assertEqual(self.manager.state.messages[1].role, "assistant")
    
    def test_should_continue_conversation_deprecated(self):
        """Test deprecated should_continue_conversation method."""
        # This method is deprecated but kept for backward compatibility
        with patch('lzbot.conversation.logger') as mock_logger:
            result = self.manager.should_continue_conversation("What's your name?")
            mock_logger.warning.assert_called_once()
            self.assertTrue(result)  # Should detect question mark
    
    def test_mark_requirements_gathered(self):
        """Test marking requirements as gathered."""
        self.assertFalse(self.manager.state.has_gathered_requirements)
        
        self.manager.mark_requirements_gathered()
        
        self.assertTrue(self.manager.state.has_gathered_requirements)
    
    def test_is_ready_for_implementation(self):
        """Test checking if ready for implementation."""
        self.assertFalse(self.manager.is_ready_for_implementation())
        
        self.manager.mark_requirements_gathered()
        self.assertTrue(self.manager.is_ready_for_implementation())
    
    def test_get_conversation_summary(self):
        """Test getting conversation summary."""
        self.manager.add_user_message("Hello")
        self.manager.add_assistant_message("Hi, how can I help?")
        
        summary = self.manager.get_conversation_summary()
        
        self.assertEqual(summary["message_count"], 2)
        self.assertEqual(summary["user_messages"], 1)
        self.assertEqual(summary["assistant_messages"], 1)
        self.assertFalse(summary["has_gathered_requirements"])
        self.assertIsNotNone(summary["last_interaction"])
        self.assertIn("conversation_analysis", summary)
    
    def test_analyze_last_agent_response_deprecated(self):
        """Test deprecated analyze_last_agent_response method."""
        self.manager.add_assistant_message("What's your company size?")
        
        with patch('lzbot.conversation.logger') as mock_logger:
            result = self.manager.analyze_last_agent_response()
            mock_logger.warning.assert_called_once()
            self.assertTrue(result["has_questions"])
    
    def test_format_multi_question_prompt(self):
        """Test formatting multi-question prompts."""
        single_question = "What's your name?"
        multi_question = "What's your name? What's your company size? What's your budget?"
        
        single_prompt = self.manager.format_multi_question_prompt(single_question)
        multi_prompt = self.manager.format_multi_question_prompt(multi_question)
        
        self.assertEqual(single_prompt, "Please provide your response:")
        self.assertIn("multiple questions", multi_prompt)
    
    def test_get_context_for_agent(self):
        """Test getting context formatted for agent."""
        self.manager.add_user_message("Design AWS architecture")
        self.manager.add_assistant_message("What's your company size?")
        
        context = self.manager.get_context_for_agent()
        
        self.assertIn("Previous conversation:", context)
        self.assertIn("Design AWS architecture", context)
        self.assertIn("What's your company size?", context)


if __name__ == '__main__':
    unittest.main()