"""
AI Agent Module for LZBot-5000

Handles Bedrock model initialization and agent configuration for AWS Landing Zone design
with input/output validation for data integrity.
"""

from strands.models import BedrockModel
from strands import Agent
from typing import Dict, Any, List
from .logging_config import get_logger, log_function
from .validation import UserQuery, ArchitectureResult, MCPToolResponse, safe_validate
from .exceptions import AgentError, ModelError, ValidationError

logger = get_logger(__name__)


class LZBotAgent:
    """AI Agent for AWS Landing Zone design using Amazon Bedrock."""
    
    # System prompt for the AI agent
    SYSTEM_PROMPT = """
You are an AWS Solutions Architect expert. Design secure, scalable AWS Landing Zones following Well-Architected Framework.

Process:
1. Analyze requirements 
2. Design architecture covering: accounts, networking, security, monitoring
3. Create diagram showing key components and relationships using generate_diagram tool
4. Generate focused implementation plan
5. Create comprehensive documentation in Confluence with attached diagrams

Output Requirements:
- Concise textual design (max 2000 words) with key decisions and rationale
- Simple diagram saved to ./outputs directory using generate_diagram tool
- Create ONE epic using create_epic tool with clear title and description
- Create Confluence documentation using create_confluence_page tool (max 3000 words)
- Upload diagram to Confluence page using upload_confluence_attachment tool with the diagram file path
- Link JIRA to Confluence using link_jira_to_confluence tool

Keep ALL responses concise and focused. Use simple, direct language.
Default region: ap-southeast-2.
Always specify diagram file path: "The diagram is saved at: <filepath>".

IMPORTANT: 
- Do NOT use bulk_create_backlog - use individual tools only
- After creating Confluence page and generating diagram, ALWAYS upload the diagram as attachment
- Use the exact file path from generate_diagram output for upload_confluence_attachment
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
    
    @log_function
    def process_query(self, query: str, tools: List[Any]) -> Any:
        """
        Process architecture query using AI agent with validation.
        
        Args:
            query: User's architecture requirements
            tools: Available tools for the agent
            
        Returns:
            Agent response containing design and implementation details
            
        Raises:
            ValidationError: If query validation fails
            AgentError: If agent processing fails
            ModelError: If model interaction fails
        """
        logger.info("Processing architecture query with AI agent")
        logger.debug(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
        
        # Validate input query
        try:
            validated_query, errors = safe_validate({'description': query}, UserQuery)
            if errors:
                raise ValidationError(f"Query validation failed: {'; '.join(errors)}")
            logger.info("Query validation successful")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Query validation error: {str(e)}")
        
        agent = self.create_agent(tools)
        
        try:
            result = agent(query)
            logger.info("Successfully processed query with AI agent")
            
            # Validate agent result if it contains structured data
            self._validate_agent_result(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query with AI agent: {e}")
            if "model" in str(e).lower() or "bedrock" in str(e).lower():
                raise ModelError(f"Model processing failed: {str(e)}", model_name="claude-sonnet-4")
            else:
                raise AgentError(f"Agent processing failed: {str(e)}", agent_action="process_query")
    
    def _validate_agent_result(self, result: Any) -> None:
        """
        Validate agent result for basic structure and content.
        
        Args:
            result: Agent result to validate
            
        Raises:
            ValidationError: If result validation fails
        """
        try:
            # Basic validation - ensure result is not empty
            if not result:
                raise ValidationError("Agent result is empty")
            
            # If result has text content, validate minimum length
            result_str = str(result)
            if len(result_str.strip()) < 50:
                raise ValidationError("Agent result is too short to be meaningful")
            
            logger.info("Agent result validation successful")
            
        except ValidationError:
            raise
        except Exception as e:
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