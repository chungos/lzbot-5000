# LZBot-5000

**An intelligent AWS Landing Zone design tool that leverages AWS Bedrock, Strands framework, AWS Diagram MCP Server, and JIRA/Confluence integration to automatically generate comprehensive, Well-Architected Framework-compliant landing zone architectures with professional diagrams, implementation guides, and automatic backlog publishing.**

## 🚀 Overview

LZBot-5000 is a production-ready AWS Landing Zone designer that combines:

- **AWS Bedrock** (Claude Sonnet 4) for intelligent architecture design
- **Strands Framework** for AI agent orchestration  
- **AWS Diagram MCP Server** for professional architecture diagram generation
- **JIRA/Confluence MCP Server** for automatic backlog and documentation publishing
- **Pydantic Validation** for robust input/output data integrity
- **Structured Logging** with comprehensive error handling and monitoring
- **Comprehensive Testing Suite** with integration validation
- **Production-Ready Architecture** with proper dependency management and optimization
- **Automatic Question Detection**: The AI agent recognizes when it needs more information
- **Interactive Dialogue**: Engages in back-and-forth conversation to understand your needs
- **Smart Continuation**: Knows when to stop asking questions and start designing
- **User Control**: You can type 'proceed' to continue with current information at any time

The tool takes natural language queries about your AWS requirements and produces:

- Professional architecture diagrams (PNG format) saved to `./outputs` directory
- Detailed implementation guides and documentation
- Well-Architected Framework compliance documentation
- Automated JIRA epics and stories with proper categorization
- Confluence pages with comprehensive architecture details and embedded diagrams
- Cost optimization strategies and recommendations


## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   LZBot-5000    │───▶│   AWS Bedrock   │
│  Validation     │    │   Core Agent    │    │  Claude Model   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  JIRA/Confluence│◀───│  MCP Clients    │───▶│  AWS Diagram    │
│   Integration   │    │   Management    │    │    Service      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
lzbot-5000/
├── lzbot/                      # Main package
│   ├── __init__.py            # Package exports
│   ├── agent.py               # AI agent with validation
│   ├── clients.py             # MCP client management
│   ├── file_handler.py        # File operations
│   ├── input_handler.py       # CLI processing with validation
│   ├── logging_config.py      # Structured logging framework
│   ├── exceptions.py          # Custom exception types
│   └── validation.py          # Pydantic models for I/O validation
├── tests/                      # Comprehensive test suite
│   ├── run_tests.py           # Interactive test runner
│   ├── test_config.py         # Updated test configuration
│   ├── test_jira_mcp.py       # JIRA integration tests
│   ├── test_confluence_mcp.py # Confluence integration tests
│   └── test_confluence_attachment.py # Attachment functionality
├── outputs/                   # Generated diagrams and documentation
├── DEPLOYMENT.md              # Production deployment guide
├── OPERATIONS.md              # Day-to-day operations guide
├── integration_test.py        # Integration test suite
├── test_validation.py         # Validation system tests
├── examples/                  # Example outputs and usage
├── main.py                    # Application entry point
├── pyproject.toml             # Modern Python packaging
├── .env.example              # Environment template
└── README.md                 # This file

#### AWS Bedrock Integration
- **Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Region**: `ap-southeast-2` (Sydney)
- **Configuration**: Token-optimized (max_tokens=4000, temperature=0.1)
- Expert-level AWS Solutions Architect knowledge
- Well-Architected Framework compliance

#### AWS Diagram MCP Server
- **Server**: `uvx --with jschema-to-python awslabs.aws-diagram-mcp-server@latest`
- **Transport**: STDIO via uvx with dependency isolation
- **Dependency Resolution**: jschema-to-python included via --with flag
- Generates professional AWS architecture diagrams
- Automatic diagram file management and organization

#### JIRA/Confluence MCP Server
- **Server**: GitHub-hosted custom MCP server
- **Repository**: `https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git`
- **Transport**: STDIO via uvx
- Real JIRA epic and story creation with proper API integration
- Confluence page creation with comprehensive architecture documentation
- **Confluence diagram embedding**: Working attachment functionality
- Story point estimation and Definition of Done

### Data Flow

```
User Query
    ↓
AI Agent (Claude via Bedrock)
    ↓
├─→ AWS Diagram MCP Server → Generates Architecture Diagrams
│
├─→ Generates Architecture Design & Implementation Backlog
│
└─→ JIRA/Confluence MCP Server
    ├─→ Creates JIRA Epic (6-month implementation)
    ├─→ Creates JIRA Sprints (6 x 2-week sprints)
    ├─→ Creates JIRA Stories (with story points & DoD)
    ├─→ Creates Confluence Page with architecture details
    ├─→ Uploads Diagrams to Confluence (WORKING)
    └─→ Links JIRA Epic to Confluence Page
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+ with pip and uvx installed
- AWS credentials with Bedrock access (Claude Sonnet v2)
- JIRA/Confluence API tokens (optional, for integration features)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd lzbot-5000

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Environment Configuration

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your actual values
# Required for AWS Bedrock:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY  
# - AWS_REGION (default: ap-southeast-2)

# Optional for JIRA/Confluence integration:
# - JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
# - CONFLUENCE_URL, CONFLUENCE_SPACE_KEY
# - JIRA_PROJECT_KEY, CONFLUENCE_PARENT_PAGE_ID
```

### 4. Usage

```bash
# Basic usage with query (includes conversational mode)
python main.py -q "Design a multi-region AWS CloudWAN architecture for connecting Sydney and Melbourne offices"

# Interactive conversational mode (recommended for complex requirements)
python main.py --interactive

# Check available options
python main.py --help

# Run in specific output directory
python main.py -q "Your query here" --output-dir ./custom-outputs

## 🧪 Testing

### Test Suite Overview

The project includes comprehensive testing with 100% success rate:

```bash
# Run all tests interactively
python tests/run_tests.py

# Run specific test categories
python tests/run_tests.py  # Select from: jira, confluence, config, all

# Direct test execution
cd tests/
python test_jira_mcp.py           # JIRA integration tests
python test_confluence_mcp.py     # Confluence integration tests
python test_confluence_attachment.py  # Attachment functionality
```

### Test Configuration

Tests support both real and mock modes:
- **Real Mode**: Uses actual JIRA/Confluence APIs (creates real tickets/pages)
- **Mock Mode**: Simulated responses for development (set `TEST_MODE=mock` in .env)

### Recent Test Results
```
📊 Test Results Summary
JIRA Tests: 2/2 passed (100% success rate)
- Epic Creation: ✅ PASSED (SCRUM-44 created)
- Story Creation: ✅ PASSED (SCRUM-45 created)
Confluence Attachment: ✅ PASSED (Page ID 4030501 with diagram)
Duration: 4.71s
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# AWS Configuration (Required)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-southeast-2

# JIRA Configuration (Optional)
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT

# Confluence Configuration (Optional)
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_SPACE_KEY=YOUR_SPACE
CONFLUENCE_PARENT_PAGE_ID=your-parent-page-id

# Test Configuration
TEST_MODE=real    # Set to "mock" for safe testing
```

### Getting API Credentials

#### JIRA API Token
1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage/api-tokens)
2. Click "Create API token"
3. Give it a label and copy the token
4. Use this as `JIRA_API_TOKEN`

#### Finding Project and Space Keys
- **JIRA Project Key**: Look at the URL or issue keys (e.g., SCRUM-123 → key is "SCRUM")
- **Confluence Space Key**: Check the URL when viewing your space
- **Page IDs**: Found in Confluence page URLs

## 🎯 Features

### Intelligent Conversational Design
- **Requirements Gathering**: AI agent asks clarifying questions to understand your specific needs
- **Interactive Dialogue**: Back-and-forth conversation for better architecture tailoring
- **Smart Question Detection**: Automatically determines when more information is needed
- **User Control**: Option to proceed with current information or provide more details

### Automatic JIRA Integration
- **Epic Creation**: 6-month implementation timeline
- **Sprint Planning**: 6 x 2-week sprints with logical grouping
- **Story Creation**: Detailed user stories with acceptance criteria
- **Story Point Estimation**: T-shirt sizing (XS=1, S=2, M=3, L=5, XL=8, XXL=13)
- **Definition of Done**: Comprehensive DoD for each story

### Confluence Documentation
- **Architecture Pages**: Detailed design documentation
- **Diagram Embedding**: Automatic upload and embedding of generated diagrams (WORKING)
- **Implementation Guides**: Step-by-step implementation instructions
- **Cost Analysis**: Budget estimates and optimization recommendations

### AWS Architecture Generation
- **Well-Architected Framework**: Compliance with all 6 pillars
- **Multi-Region Support**: CloudWAN, Global infrastructure
- **Security Focus**: Zero-trust architecture, comprehensive governance
- **Diagram Formats**: PNG with professional styling

## 🔒 Security & Best Practices

### Credential Management
- **Environment Variables**: All credentials stored in `.env` file
- **No Hardcoded Secrets**: Safe mock values for testing
- **Secure Masking**: Sensitive data masked in logs and output
- **Validation**: Comprehensive configuration validation

### Safe Testing
- **Mock Mode Default**: Prevents accidental API calls
- **Fallback Configuration**: Graceful degradation when credentials missing
- **Error Handling**: Comprehensive error catching and reporting

## 🐛 Troubleshooting

### Configuration Issues
```bash
# Check current configuration
python config.py

# Test configuration loading
python tests/test_config.py
```

### Test Failures
- Ensure environment variables are set correctly
- Check network connectivity to Atlassian services
- Verify API tokens are valid and have proper permissions
- Use mock mode for development: `export TEST_MODE=mock`

### Common Errors
- `ConfigError: Required environment variable 'X' is not set` → Set up .env file
- `403 Forbidden` → Check API token permissions in Atlassian
- `404 Not Found` → Verify project/space keys are correct
- `429 Too Many Requests` → API rate limiting, wait and retry

## 📈 Example Output

### Generated Architecture
- **CloudWAN Multi-Region**: Melbourne and Sydney connectivity
- **Landing Zone**: Multi-account governance structure
- **Security**: Zero-trust network architecture
- **Monitoring**: Comprehensive observability stack

### JIRA Integration Result
- **Epic**: "AWS CloudWAN Multi-Region Implementation"
- **6 Sprints**: Foundation, Networking, Security, Services, Monitoring, Optimization
- **25+ Stories**: Detailed implementation tasks with story points
- **Confluence Link**: Embedded in epic description

### Confluence Documentation
- **Architecture Overview**: High-level design and principles
- **Implementation Guide**: Step-by-step instructions
- **Embedded Diagrams**: Professional AWS architecture diagrams (verified working)
- **Cost Analysis**: Budget estimates and optimization strategies

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python tests/run_tests.py all`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Related Projects

- [AWS Diagram MCP Server](https://github.com/awslabs/aws-diagram-mcp-server)
- [Strands Framework](https://github.com/anthropics/strands)
- [Model Context Protocol](https://github.com/modelcontextprotocol)

---

**LZBot-5000** - Automating AWS Landing Zone design with AI-powered architecture generation and seamless JIRA/Confluence integration. 🚀
