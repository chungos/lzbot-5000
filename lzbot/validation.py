"""
Input/Output validation models for LZBot-5000
Provides Pydantic models for validating user inputs and API responses.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import re


class ArchitectureComplexity(str, Enum):
    """Architecture complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


class AWSRegion(str, Enum):
    """Common AWS regions."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_2 = "ap-southeast-2"


class UserQuery(BaseModel):
    """Model for validating user architecture requests."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    description: str = Field(
        ..., 
        min_length=10, 
        max_length=5000,
        description="Architecture description or requirements"
    )
    complexity: Optional[ArchitectureComplexity] = Field(
        default=ArchitectureComplexity.MODERATE,
        description="Expected architecture complexity"
    )
    preferred_region: Optional[AWSRegion] = Field(
        default=AWSRegion.AP_SOUTHEAST_2,
        description="Preferred AWS region"
    )
    requirements: Optional[List[str]] = Field(
        default_factory=list,
        description="Specific requirements or constraints"
    )
    budget_considerations: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Budget or cost considerations"
    )
    compliance_requirements: Optional[List[str]] = Field(
        default_factory=list,
        description="Compliance requirements (SOX, HIPAA, etc.)"
    )
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Description cannot be empty')
        
        # Check for minimum meaningful content
        words = v.split()
        if len(words) < 5:
            raise ValueError('Description must contain at least 5 words')
        
        return v
    
    @field_validator('requirements')
    @classmethod
    def validate_requirements(cls, v: List[str]) -> List[str]:
        return [req.strip() for req in v if req.strip()]

    @field_validator('compliance_requirements')
    @classmethod
    def validate_compliance(cls, v: List[str]) -> List[str]:
        valid_compliance = {
            'sox', 'hipaa', 'gdpr', 'pci-dss', 'fisma', 'iso-27001',
            'soc2', 'fedramp', 'nist', 'cis'
        }
        
        validated = []
        for req in v:
            req_lower = req.lower().strip()
            if req_lower in valid_compliance:
                validated.append(req_lower)
            else:
                # Allow custom compliance requirements but log them
                validated.append(req.strip())
        
        return validated


class ConversationResponse(BaseModel):
    """Model for validating conversational responses - more flexible than UserQuery."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    response: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User response in conversation"
    )
    
    @field_validator('response')
    @classmethod
    def validate_response(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Response cannot be empty')
        return v


class JiraIssueRequest(BaseModel):
    """Model for JIRA issue creation requests."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    summary: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=32767)  # JIRA limit
    issue_type: str = Field(default="Task", description="JIRA issue type")
    priority: str = Field(default="Medium", description="Issue priority")
    labels: Optional[List[str]] = Field(default_factory=list)
    assignee: Optional[str] = Field(default=None, description="Assignee username")
    
    @field_validator('labels')
    @classmethod
    def validate_labels(cls, v: List[str]) -> List[str]:
        # Clean and validate JIRA labels (no spaces, valid characters)
        validated = []
        for label in v:
            # Remove spaces and special characters except hyphens and underscores
            clean_label = re.sub(r'[^a-zA-Z0-9_-]', '', label.strip().replace(' ', ''))
            if clean_label:
                validated.append(clean_label)
        return validated


class ConfluencePageRequest(BaseModel):
    """Model for Confluence page creation requests."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    space_key: Optional[str] = Field(default=None, min_length=1, max_length=255)
    parent_page_id: Optional[str] = Field(default=None)
    labels: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        # Basic validation for Confluence content
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v


class DiagramRequest(BaseModel):
    """Model for diagram generation requests."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    diagram_type: str = Field(default="architecture", description="Type of diagram")
    format: str = Field(default="png", pattern=r'^(png|svg|pdf)$')
    include_labels: bool = Field(default=True)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        # Ensure title is suitable for filename
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v):
            raise ValueError('Title contains invalid characters for filename')
        return v


class ArchitectureResult(BaseModel):
    """Model for architecture generation results."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    query: UserQuery
    design_content: str = Field(..., min_length=100)
    diagrams: List[str] = Field(default_factory=list, description="Generated diagram file paths")
    jira_issue_key: Optional[str] = Field(default=None)
    confluence_page_url: Optional[str] = Field(default=None)
    implementation_notes: Optional[str] = Field(default=None)
    estimated_cost: Optional[str] = Field(default=None)
    
    @field_validator('design_content')
    @classmethod
    def validate_design_content(cls, v: str) -> str:
        words = v.split()
        if len(words) < 50:
            raise ValueError(f'Design content must be more substantial (at least 50 words, got {len(words)})')
        return v


class MCPToolResponse(BaseModel):
    """Model for MCP tool responses."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    tool_name: str
    success: bool
    result: Optional[Union[str, Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    @field_validator('result')
    @classmethod
    def validate_result(cls, v, info):
        # If success is True, result should not be None
        values = info.data if hasattr(info, 'data') else {}
        if values.get('success') and v is None:
            raise ValueError('Result cannot be None when success is True')
        return v


class FileOperationResult(BaseModel):
    """Model for file operation results."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    operation: str
    file_path: str
    success: bool
    file_size: Optional[int] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        if not v or v.isspace():
            raise ValueError('File path cannot be empty')
        return v


class ConfigValidationRequest(BaseModel):
    """Model for configuration validation requests."""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    jira_url: str = Field(..., min_length=10)
    jira_email: str = Field(..., min_length=5)
    confluence_url: str = Field(..., min_length=10)
    test_connection: bool = Field(default=False)
    
    @field_validator('jira_url', 'confluence_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v.rstrip('/')
    
    @field_validator('jira_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


# Validation utility functions
def validate_user_input(data: Dict[str, Any], model_class: BaseModel) -> BaseModel:
    """
    Validate user input against a Pydantic model.
    
    Args:
        data: Raw input data
        model_class: Pydantic model class for validation
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
    """
    return model_class.model_validate(data)


def validate_architecture_query(query_text: str, **kwargs) -> UserQuery:
    """
    Validate and parse an architecture query.
    
    Args:
        query_text: User's architecture description
        **kwargs: Additional query parameters
        
    Returns:
        Validated UserQuery instance
    """
    data = {'description': query_text, **kwargs}
    return UserQuery.model_validate(data)


def safe_validate(data: Dict[str, Any], model_class: BaseModel) -> tuple[BaseModel, Optional[List[str]]]:
    """
    Safely validate data and return both result and errors.
    
    Args:
        data: Data to validate
        model_class: Pydantic model class
        
    Returns:
        Tuple of (validated_model_or_None, list_of_error_messages)
    """
    try:
        validated = model_class.model_validate(data)
        return validated, None
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc']) if error['loc'] else 'root'
                errors.append(f"{field}: {error['msg']}")
        else:
            errors.append(str(e))
        return None, errors


def format_validation_errors(errors: List[str]) -> str:
    """Format validation errors for user display."""
    if not errors:
        return ""
    
    formatted = "❌ Validation Errors:\n"
    for error in errors:
        formatted += f"  • {error}\n"
    
    return formatted