# LZBot-5000 Production Deployment Guide

## Overview

LZBot-5000 is a professional AWS Landing Zone Designer with JIRA/Confluence integration. This guide covers production deployment, environment setup, and operational guidelines.

## Architecture Overview

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

## Prerequisites

### System Requirements

- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: 3.9 or higher (recommended: 3.11+)
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: 2GB free space for dependencies and outputs
- **Network**: Internet connection for MCP servers and AWS Bedrock

### Required Tools

1. **Python 3.9+** with pip
2. **uvx** (Universal eXecutable runner)
   ```bash
   # Install uvx
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Git** for version control
4. **AWS CLI** (optional, for credential management)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd landingzonedesigner/lzbot-5000
```

### 2. Python Dependencies

The application uses minimal dependencies and relies on MCP servers for functionality:

```bash
# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies (if using Pydantic validation)
pip install pydantic
pip install python-dotenv  # Optional, for .env file support
```

### 3. Verify uvx Installation

```bash
uvx --version
```

## Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# JIRA Configuration (Required)
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@domain.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_PROJECT_KEY="YOUR_PROJECT"
export JIRA_BOARD_ID="1"

# Confluence Configuration (Required)
export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="YOUR_SPACE"
export CONFLUENCE_PARENT_PAGE_ID="your-parent-page-id"  # Optional

# AWS Configuration (Optional)
export AWS_REGION="ap-southeast-2"
export AWS_PROFILE="your-aws-profile"  # Optional
```

### Configuration Sources

The application supports multiple configuration sources in order of precedence:

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **Default values** (for optional settings)

### Validation Modes

- **Pydantic Mode** (recommended): Uses Pydantic for robust validation
- **Legacy Mode**: Falls back to basic validation if Pydantic unavailable

## Deployment Options

### Option 1: Local Development/Testing

```bash
# Navigate to project directory
cd landingzonedesigner/lzbot-5000

# Set environment variables
source .env  # or export variables manually

# Run application
python3 main.py

# Or with specific query
python3 main.py -q "Design a multi-region AWS architecture"
```

### Option 2: Server Deployment

#### Systemd Service (Linux)

Create `/etc/systemd/system/lzbot.service`:

```ini
[Unit]
Description=LZBot-5000 AWS Landing Zone Designer
After=network.target

[Service]
Type=simple
User=lzbot
WorkingDirectory=/opt/lzbot-5000
Environment=PATH=/opt/lzbot-5000/venv/bin:/usr/local/bin:/usr/bin:/bin
EnvironmentFile=/opt/lzbot-5000/.env
ExecStart=/opt/lzbot-5000/venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable lzbot
sudo systemctl start lzbot
```

#### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install uvx and system dependencies
RUN apt-get update && apt-get install -y curl git && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Add uvx to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application
COPY . .

# Install Python dependencies
RUN pip install pydantic python-dotenv

# Create outputs directory
RUN mkdir -p outputs

# Set default command
CMD ["python3", "main.py"]
```

Build and run:
```bash
docker build -t lzbot-5000 .
docker run --env-file .env -v $(pwd)/outputs:/app/outputs lzbot-5000
```

### Option 3: Cloud Deployment

#### AWS EC2

1. **Launch EC2 Instance**
   - Recommended: t3.medium or larger
   - Security group: Allow SSH (22) and any custom ports
   - IAM role: Bedrock access permissions

2. **Install Dependencies**
   ```bash
   sudo yum update -y
   sudo yum install -y python3 python3-pip git
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Deploy Application**
   ```bash
   git clone <repository-url>
   cd landingzonedesigner/lzbot-5000
   pip3 install pydantic python-dotenv
   ```

4. **Configure AWS Credentials**
   ```bash
   aws configure
   # Or use IAM roles for EC2
   ```

## Security Considerations

### API Token Management

1. **JIRA API Tokens**
   - Use app-specific tokens, not personal passwords
   - Rotate tokens regularly (every 90 days)
   - Store in secure environment variables, not in code

2. **AWS Credentials**
   - Use IAM roles when possible
   - Follow principle of least privilege
   - Enable CloudTrail for audit logging

### Network Security

1. **Firewall Configuration**
   - Restrict inbound access to necessary ports only
   - Use VPN or bastion hosts for remote access
   - Enable AWS Security Groups and NACLs

2. **TLS/SSL**
   - All external API calls use HTTPS
   - Verify certificate validity
   - Use TLS 1.2 or higher

### Data Protection

1. **Sensitive Data**
   - API tokens and credentials never logged
   - Use environment variables, not config files
   - Implement secrets rotation

2. **Output Security**
   - Generated diagrams may contain sensitive architecture info
   - Secure storage of output files
   - Implement access controls for generated content

## Monitoring and Logging

### Application Logs

Configure structured logging:

```python
from lzbot.logging_config import setup_logging

# Production logging setup
setup_logging(
    level="INFO",
    log_file=Path("/var/log/lzbot/application.log"),
    json_format=True  # For structured logging
)
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages  
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical error conditions

### Monitoring Metrics

Key metrics to monitor:

1. **Application Health**
   - Successful architecture generations
   - API response times
   - Error rates by component

2. **Resource Usage**
   - Memory consumption
   - CPU utilization
   - Disk space for outputs

3. **External Dependencies**
   - MCP server connection status
   - AWS Bedrock API availability
   - JIRA/Confluence API response times

### Log Aggregation

For production environments, consider:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **AWS CloudWatch** Logs
- **Splunk** or similar enterprise solutions

## Performance Optimization

### Configuration Tuning

1. **Bedrock Model Settings**
   ```python
   # Optimized settings for production
   max_tokens=4000       # Balance quality vs. speed
   temperature=0.1       # Lower for consistency
   region="ap-southeast-2"  # Closest region
   ```

2. **MCP Client Optimization**
   - Connection pooling for repeated requests
   - Timeout configuration for reliability
   - Retry logic for transient failures

### Scaling Considerations

1. **Vertical Scaling**
   - Increase instance size for better performance
   - More memory helps with larger architecture requests

2. **Horizontal Scaling**
   - Multiple instances with load balancer
   - Shared storage for outputs
   - Session-less design enables easy scaling

### Caching Strategies

1. **Template Caching**
   - Cache common architecture patterns
   - Reuse validated configurations

2. **Output Caching**
   - Cache generated diagrams for similar requests
   - Implement cache invalidation strategy

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failures**
   ```bash
   # Test uvx installation
   uvx --version
   
   # Test MCP server manually
   uvx --from git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git jira-confluence-mcp
   ```

2. **AWS Bedrock Access Denied**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Verify Bedrock permissions
   aws bedrock list-foundation-models --region ap-southeast-2
   ```

3. **JIRA/Confluence Authentication**
   ```bash
   # Test API token
   curl -u user@domain.com:api_token https://domain.atlassian.net/rest/api/2/myself
   ```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LZBOT_LOG_LEVEL=DEBUG

# Or modify logging setup
python3 -c "
from lzbot.logging_config import setup_logging
setup_logging(level='DEBUG')
"
```

### Health Checks

Create health check script:

```python
#!/usr/bin/env python3
"""Health check script for LZBot-5000"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def health_check():
    try:
        # Test configuration loading
        from config import load_config
        config = load_config()
        print("✅ Configuration: OK")
        
        # Test MCP client creation
        from lzbot.clients import ClientManager
        env_vars = config.to_env_dict() if hasattr(config, 'to_env_dict') else config.get_all_env_vars()
        client_manager = ClientManager(env_vars)
        print("✅ MCP Clients: OK")
        
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if health_check() else 1)
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review application logs for errors
   - Check disk space in outputs directory
   - Verify external service connectivity

2. **Monthly**
   - Update dependencies (uvx, Python packages)
   - Review and rotate API tokens
   - Analyze performance metrics

3. **Quarterly**
   - Security audit of configurations
   - Review and update documentation
   - Test disaster recovery procedures

### Backup Procedures

1. **Configuration Backup**
   ```bash
   # Backup environment configuration
   cp .env .env.backup.$(date +%Y%m%d)
   ```

2. **Output Backup**
   ```bash
   # Backup generated outputs
   tar -czf outputs_backup_$(date +%Y%m%d).tar.gz outputs/
   ```

### Update Procedures

1. **Application Updates**
   ```bash
   # Backup current version
   cp -r lzbot-5000 lzbot-5000.backup
   
   # Pull updates
   git pull origin main
   
   # Test new version
   python3 integration_test.py
   ```

2. **Dependency Updates**
   ```bash
   # Update uvx
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Update Python packages
   pip install --upgrade pydantic python-dotenv
   ```

## Support and Resources

### Documentation
- **API Reference**: See individual module docstrings
- **Configuration Guide**: This document
- **Troubleshooting**: See troubleshooting section above

### Community
- **Issues**: Report bugs via Git repository
- **Discussions**: Architecture questions and improvements
- **Contributing**: Follow contribution guidelines

### Professional Support
- **Enterprise Support**: Available for production deployments
- **Custom Development**: Architecture-specific modifications
- **Training**: Team training for operations and maintenance

---

## Appendix

### A. Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | Yes | - | JIRA instance URL |
| `JIRA_EMAIL` | Yes | - | JIRA user email |
| `JIRA_API_TOKEN` | Yes | - | JIRA API token |
| `JIRA_PROJECT_KEY` | Yes | - | JIRA project key |
| `JIRA_BOARD_ID` | No | "1" | JIRA board ID |
| `CONFLUENCE_URL` | Yes | - | Confluence instance URL |
| `CONFLUENCE_SPACE_KEY` | Yes | - | Confluence space key |
| `CONFLUENCE_PARENT_PAGE_ID` | No | - | Parent page for new pages |
| `AWS_REGION` | No | "ap-southeast-2" | AWS region |
| `AWS_PROFILE` | No | - | AWS profile name |

### B. Port Requirements

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| Application | 8080 | TCP | Web interface (optional) |
| SSH | 22 | TCP | Remote management |
| HTTPS | 443 | TCP | External API calls |

### C. IAM Permissions

Minimum AWS IAM permissions required:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

### D. Firewall Rules

Recommended iptables rules:

```bash
# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS outbound
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Drop other inbound
iptables -A INPUT -j DROP
```