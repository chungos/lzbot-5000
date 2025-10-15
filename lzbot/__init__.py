"""
LZBot-5000: AWS Landing Zone Designer with JIRA/Confluence Integration

A modular, professional-grade tool for designing AWS Landing Zones
with automatic documentation and project management integration.
"""

__version__ = "1.0.0"
__author__ = "LZBot Development Team"

# Core modules
from .clients import ClientManager
from .agent import LZBotAgent
from .input_handler import InputHandler
from .file_handler import FileHandler
from .conversation import ConversationManager, ConversationState, ConversationMessage

__all__ = [
    "ClientManager",
    "LZBotAgent", 
    "InputHandler",
    "FileHandler",
    "ConversationManager",
    "ConversationState", 
    "ConversationMessage"
]