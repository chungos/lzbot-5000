"""
AI Agent Module for LZBot-5000

Handles Bedrock model initialization and agent configuration for AWS Landing Zone design
with input/output validation for data integrity.
"""

import io
from contextlib import redirect_stdout
from strands.models import BedrockModel
from strands import Agent
from typing import Dict, Any, List, Optional, Tuple
from .logging_config import get_logger, log_function
from .validation import UserQuery, ArchitectureResult, safe_validate
from .exceptions import AgentError, ModelError, ValidationError
from .conversation import ConversationManager

logger = get_logger(__name__)


class LZBotAgent:
    """AI Agent for AWS Landing Zone design using Amazon Bedrock with conversational support."""
    
    # System prompt for the AI agent
    SYSTEM_PROMPT = """
You are an expert AWS Solutions Architect with deep knowledge of the AWS Well-Architected Framework.

Your primary role is to design robust, secure, and scalable AWS Landing Zones for new and existing cloud environments.

When a user requests a landing zone design, your process is as follows:

Requirement Gathering: Ask clarifying questions to understand the user's specific business needs,
compliance requirements (e.g., HIPAA, PCI DSS), technical constraints, and desired account structure.

IMPORTANT: When gathering requirements, ask 2-3 focused questions at a time to avoid overwhelming the user.
Focus on the most critical aspects first:
1. Business context and scale (company size, number of users, growth expectations)
2. Compliance and security requirements (regulatory needs, data sensitivity)
3. Technical constraints (existing infrastructure, budget constraints, timeline)

Only proceed to design phase when you have sufficient information to create a comprehensive architecture.

Well-Architected Design: Based on the gathered information, design a landing zone architecture that
strictly adheres to the five pillars of the Well-Architected Framework: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization.

Every design decision you make must be justified by one or more of these pillars.

Output Generation: Provide the design in a three-part output:

Textual Design: A detailed, step-by-step description of the architecture. This must cover account organization (AWS Organizations), networking (VPCs, Transit Gateway), 
security controls (Control Tower, SCPs), identity management (IAM), and logging/monitoring (CloudTrail, CloudWatch).

Diagrams: Generate a clear, professional diagram to visually represent the architecture.
The diagram should show the flow of resources, account relationships, and key services. Describe the layout using a format that can be easily understood and replicated.

Backlog: Create a backlog of stories to implement the design, with t-shirt sizing Large, Medium, Small, description and definition of done.
Split into 2-week sprints for implementation.

Tone & Interaction: Maintain a professional, knowledgeable, and helpful tone. Always explain the
rationale behind your design choices, explicitly referencing the relevant Well-Architected pillars.

You are a consultant, not just a generator. You will continue to iterate on the design based on user feedback.

Always provide clear, actionable advice with to create this infrastructure from digram. Default region is ap-southeast-2.

You MUST tell the customer the full file path of the diagram in the format "The diagram is saved at: <filepath>".

When generating diagrams, save them to the ./outputs directory with descriptive filenames.

IMPORTANT: 
- Do NOT use bulk_create_backlog - use individual tools only
- After creating Confluence page and generating diagram, ALWAYS upload the diagram as attachment
- Use the exact file path from generate_diagram output for upload_confluence_attachment
- If you need more information from the user, ask specific questions and wait for their response
- Only proceed with diagram generation and implementation when requirements are complete
"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LZBot agent with configuration.
        
        Args:
            config: Configuration dictionary containing AWS and other settings
        """
        self.config = config
        self._bedrock_model = None
        self._agent = None
        self.conversation_manager = ConversationManager()
        
    @property
    def bedrock_model(self) -> BedrockModel:
        """Get or create Bedrock model instance."""
        if self._bedrock_model is None:
            self._bedrock_model = self._create_bedrock_model()
        return self._bedrock_model
    
    def _create_bedrock_model(self) -> BedrockModel:
        """Create Amazon Bedrock model instance."""
        model_id = "apac.anthropic.claude-sonnet-4-20250514-v1:0"
        region = self.config.get("AWS_REGION", "ap-southeast-2")
        
        logger.info(f"Creating Bedrock model: {model_id} in region: {region}")
        
        return BedrockModel(
            model_id=model_id,
            region_name=region,
            max_tokens=4000,  # Limit response length to prevent token bloat
            temperature=0.1,  # Lower temperature for more focused responses
        )
    
    def create_agent(self, tools: List[Any]) -> Agent:
        """
        Create AI agent with tools and system prompt.
        
        Args:
            tools: List of tools available to the agent
            
        Returns:
            Configured Agent instance
        """
        logger.info(f"Creating agent with {len(tools)} tools")
        
        self._agent = Agent(
            tools=tools,
            model=self.bedrock_model,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        return self._agent
    
    def _call_agent_with_suppressed_output(self, agent: Agent, agent_input: str) -> Any:
        """
        Call the agent while suppressing its direct stdout output to prevent duplicates.
        
        Args:
            agent: The agent instance to call
            agent_input: Input for the agent
            
        Returns:
            AgentResult with native conversation state information (or mock result for tests)
        """
        # Suppress stdout during agent call to prevent duplicate output
        captured_output = io.StringIO()
        try:
            with redirect_stdout(captured_output):
                # Try the new async approach first
                try:
                    import asyncio
                    result = asyncio.run(agent.invoke_async(agent_input))
                    return result
                except (ValueError, TypeError, AttributeError) as e:
                    # Fallback for mocked agents or older Strands versions
                    logger.debug(f"Falling back to synchronous agent call: {e}")
                    result = agent(agent_input)
                    
                    # Return result as-is; _analyze_agent_result handles missing stop_reason
                    return result
        except Exception as e:
            # If there's an error, we might want to see what was captured
            captured = captured_output.getvalue()
            if captured.strip():
                logger.debug(f"Agent captured output during error: {captured[:200]}...")
            raise
    
    @log_function
    def process_query(self, query: str, tools: List[Any]) -> Any:
        """
        Process user query using AI agent with input validation and return full AgentResult.
        
        Args:
            query: User's query for AWS Landing Zone design
            tools: Available tools for the agent
            
        Returns:
            AgentResult object from Strands with native conversation state
            
        Raises:
            ValidationError: If query validation fails
            AgentError: If agent processing fails
            ModelError: If model interaction fails
        """
        logger.info("Processing query with AI agent")
        
        # Validate query input
        try:
            validated_query, errors = safe_validate({'description': query}, UserQuery)
            if errors:
                raise ValidationError(f"Query validation failed: {'; '.join(errors)}")
            logger.info("Query validation successful")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.warning(f"Query validation error, proceeding anyway: {str(e)}")
        
        # Add user message to conversation
        self.conversation_manager.add_user_message(query)
        
        agent = self.create_agent(tools)
        
        try:
            # Prepare input with conversation context if available
            agent_input = query
            if len(self.conversation_manager.state.messages) > 1:
                agent_input = self.conversation_manager.get_context_for_agent() + "\n" + query
            
            # Call agent with suppressed output and get full AgentResult
            agent_result = self._call_agent_with_suppressed_output(agent, agent_input)
            
            # Add assistant response to conversation
            result_str = str(agent_result)
            self.conversation_manager.add_assistant_message(result_str)
            
            logger.info("Successfully processed query with AI agent")
            
            # Validate agent result if it contains structured data
            self._validate_agent_result(agent_result)
            
            return agent_result  # Return full AgentResult instead of just string
            
        except Exception as e:
            logger.error(f"Error processing query with AI agent: {e}")
            if "model" in str(e).lower() or "bedrock" in str(e).lower():
                raise ModelError(f"Model processing failed: {str(e)}", model_name="claude-sonnet-4")
            else:
                raise AgentError(f"Agent processing failed: {str(e)}", agent_action="process_query")

    def process_conversation_response(self, user_response: str, tools: List[Any]) -> Any:
        """
        Process a conversational response from the user and return full AgentResult.
        
        Args:
            user_response: User's conversational response
            tools: Available tools for the agent
            
        Returns:
            AgentResult object from Strands with native conversation state
            
        Raises:
            ValidationError: If response validation fails
            AgentError: If agent processing fails
            ModelError: If model interaction fails
        """
        logger.info("Processing conversational response")
        
        # Basic validation for conversation responses
        if not user_response or not user_response.strip():
            raise ValidationError("User response cannot be empty")
        
        # Add user message to conversation
        self.conversation_manager.add_user_message(user_response)
        
        agent = self.create_agent(tools)
        
        try:
            # Always include conversation context for follow-up responses
            agent_input = self.conversation_manager.get_context_for_agent() + "\n" + user_response
            
            # Call agent with suppressed output and get full AgentResult
            agent_result = self._call_agent_with_suppressed_output(agent, agent_input)
            
            # Add assistant response to conversation
            result_str = str(agent_result)
            self.conversation_manager.add_assistant_message(result_str)
            
            logger.info("Successfully processed conversational response")
            
            return agent_result  # Return full AgentResult instead of just string
            
        except Exception as e:
            logger.error(f"Error processing conversational response: {e}")
            if "model" in str(e).lower() or "bedrock" in str(e).lower():
                raise ModelError(f"Model processing failed: {str(e)}", model_name="claude-sonnet-4")
            else:
                raise AgentError(f"Agent processing failed: {str(e)}", agent_action="process_conversation_response")
    
    def start_conversation(self, initial_query: str, tools: List[Any]) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Start a new conversation with the agent using native Strands conversation detection.
        
        Args:
            initial_query: User's initial architecture request
            tools: Available tools for the agent
            
        Returns:
            Tuple of (agent_response, needs_more_input, analysis_info)
        """
        logger.info("Starting new conversation with native Strands detection")
        self.conversation_manager.start_new_conversation()
        
        # Process query and get full AgentResult
        agent_result = self.process_query(initial_query, tools)
        
        # Use native analysis
        analysis = self._analyze_agent_result(agent_result)
        needs_more_input = self._should_continue_conversation_native(agent_result)
        
        # Extract response text
        response_str = str(agent_result)
        
        logger.info(f"Initial conversation analysis: needs_more_input={needs_more_input}, "
                   f"stop_reason={analysis.get('stop_reason', 'unknown')}")
        
        return response_str, needs_more_input, analysis
    
    def continue_conversation(self, user_response: str, tools: List[Any]) -> Tuple[str, bool, Dict[str, Any]]:
        """
        Continue an existing conversation with additional user input using native Strands detection.
        
        Args:
            user_response: User's response to agent questions
            tools: Available tools for the agent
            
        Returns:
            Tuple of (agent_response, needs_more_input, analysis_info)
        """
        logger.info("Continuing conversation with native Strands detection")
        
        if self.conversation_manager.state.is_complete:
            return "The design is already complete. Please start a new conversation for a different architecture.", False, {}
        
        # Process response and get full AgentResult
        agent_result = self.process_conversation_response(user_response, tools)
        
        # Use native analysis
        analysis = self._analyze_agent_result(agent_result)
        needs_more_input = self._should_continue_conversation_native(agent_result)
        
        # Extract response text
        response_str = str(agent_result)
        
        if not needs_more_input:
            self.conversation_manager.mark_requirements_gathered()
            logger.info("Requirements gathering complete, ready for implementation")
        
        logger.info(f"Conversation continuation analysis: needs_more_input={needs_more_input}, "
                   f"stop_reason={analysis.get('stop_reason', 'unknown')}")
        
        return response_str, needs_more_input, analysis
    
    def get_multi_question_guidance(self, agent_response: str) -> str:
        """
        Generate user guidance for multi-question scenarios.
        
        Args:
            agent_response: The agent's response containing multiple questions
            
        Returns:
            Formatted guidance string for the user
        """
        return self.conversation_manager.format_multi_question_prompt(agent_response)
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation state.
        
        Returns:
            Dictionary with conversation details
        """
        return self.conversation_manager.get_conversation_summary()
    
    def reset_conversation(self) -> None:
        """Reset the conversation state for a new session."""
        logger.info("Resetting conversation state")
        self.conversation_manager.start_new_conversation()
    
    def is_conversation_ready_for_implementation(self) -> bool:
        """
        Check if the conversation has gathered enough requirements for implementation.
        
        Returns:
            True if ready to proceed with implementation
        """
        return self.conversation_manager.is_ready_for_implementation()
    
    def _analyze_agent_result(self, agent_result) -> Dict[str, Any]:
        """
        Analyze AgentResult using native Strands capabilities.
        
        Args:
            agent_result: The AgentResult object from Strands
            
        Returns:
            Analysis dictionary with conversation state
        """
        # Check if agent_result has the expected structure
        if hasattr(agent_result, 'stop_reason') and hasattr(agent_result, 'message'):
            stop_reason = agent_result.stop_reason
            message_content = str(agent_result.message.get('content', '')) if hasattr(agent_result.message, 'get') else str(agent_result)
            
            logger.debug(f"Agent stop reason: {stop_reason}")
            
            # Use stop_reason for more accurate conversation detection
            is_waiting_for_input = stop_reason == 'end_turn'
            is_using_tools = stop_reason == 'tool_use'
            
            # Fallback to content analysis for additional context
            has_questions = '?' in message_content
            
            return {
                'stop_reason': stop_reason,
                'is_waiting_for_input': is_waiting_for_input,
                'is_using_tools': is_using_tools,
                'has_questions': has_questions,
                'needs_more_input': is_waiting_for_input and not is_using_tools,
                'message_content': message_content[:200] + '...' if len(message_content) > 200 else message_content
            }
        else:
            # Fallback to string analysis if AgentResult structure is different
            logger.warning("AgentResult doesn't have expected structure, falling back to content analysis")
            message_content = str(agent_result)
            has_questions = '?' in message_content
            
            return {
                'stop_reason': 'unknown',
                'is_waiting_for_input': has_questions,
                'is_using_tools': False,
                'has_questions': has_questions,
                'needs_more_input': has_questions,
                'message_content': message_content[:200] + '...' if len(message_content) > 200 else message_content
            }

    def _should_continue_conversation_native(self, agent_result) -> bool:
        """
        Determine if conversation should continue using native Strands capabilities.
        
        Args:
            agent_result: The AgentResult object from Strands
            
        Returns:
            True if the conversation should continue (agent is waiting for input)
        """
        analysis = self._analyze_agent_result(agent_result)
        
        # Log the decision process
        logger.info(f"Conversation analysis: stop_reason={analysis['stop_reason']}, "
                   f"waiting_for_input={analysis['is_waiting_for_input']}, "
                   f"using_tools={analysis['is_using_tools']}")
        
        return analysis['needs_more_input']
    
    def _validate_agent_result(self, result: Any) -> None:
        """
        Validate agent result for basic structure and content.
        
        Args:
            result: Agent result to validate
            
        Raises:
            ValidationError: If result validation fails
        """
        try:
            # Basic validation that result exists and is not empty
            if result is None:
                raise ValidationError("Agent result is None")
            
            result_str = str(result)
            if not result_str.strip():
                raise ValidationError("Agent result is empty")
            
            logger.debug(f"Agent result validation successful (length: {len(result_str)})")
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Agent result validation error: {str(e)}")

    def process_validated_query(self, validated_query: UserQuery, tools: List[Any]) -> ArchitectureResult:
        """
        Process a pre-validated UserQuery and return structured result.
        
        Args:
            validated_query: Pre-validated UserQuery object
            tools: Available tools for the agent
            
        Returns:
            Structured ArchitectureResult
        """
        # Process the query using the description
        agent_result = self.process_query(validated_query.description, tools)
        
        # Create structured result
        try:
            architecture_result = ArchitectureResult(
                query=validated_query,
                design_content=str(agent_result)
            )
            return architecture_result
        except Exception as e:
            raise ValidationError(f"Failed to create structured result: {str(e)}")
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_id": "apac.anthropic.claude-sonnet-4-20250514-v1:0",
            "region": self.config.get("AWS_REGION", "ap-southeast-2"),
            "provider": "Amazon Bedrock"
        }