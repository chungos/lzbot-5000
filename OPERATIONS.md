# LZBot-5000 Operations Guide

## Daily Operations

### Quick Health Check

```bash
# Navigate to application directory
cd /path/to/lzbot-5000

# Run health check
python3 integration_test.py

# Check logs for errors
tail -f /var/log/lzbot/application.log | grep ERROR
```

### Monitoring Dashboard

Key metrics to monitor daily:

1. **Application Status**
   - Service uptime
   - Error rate (should be < 1%)
   - Response time (should be < 30s)

2. **Resource Usage**
   - CPU usage (should be < 80%)
   - Memory usage (should be < 70%)
   - Disk space (outputs directory)

3. **External Dependencies**
   - AWS Bedrock API status
   - JIRA/Confluence connectivity
   - MCP server availability

## Common Operational Tasks

### Viewing Logs

```bash
# Real-time log monitoring
tail -f /var/log/lzbot/application.log

# Search for specific errors
grep "ERROR\|CRITICAL" /var/log/lzbot/application.log

# View last 100 lines
tail -100 /var/log/lzbot/application.log
```

### Managing Output Files

```bash
# Check output directory size
du -sh outputs/

# Clean old files (older than 30 days)
find outputs/ -type f -mtime +30 -delete

# Archive monthly outputs
tar -czf archive/outputs_$(date +%Y%m).tar.gz outputs/
```

### Configuration Management

```bash
# Validate current configuration
python3 -c "from config import validate_environment; validate_environment()"

# Test configuration without running full application
python3 -c "
from config import load_config
config = load_config()
print('Configuration loaded successfully')
"
```

## Incident Response

### Application Not Starting

1. **Check Configuration**
   ```bash
   python3 -c "from config import load_config; load_config()"
   ```

2. **Verify Dependencies**
   ```bash
   uvx --version
   python3 -c "import pydantic; print('Pydantic available')"
   ```

3. **Check Environment Variables**
   ```bash
   echo $JIRA_URL
   echo $CONFLUENCE_URL
   # Ensure all required variables are set
   ```

### Architecture Generation Failures

1. **Check AWS Bedrock Access**
   ```bash
   aws bedrock list-foundation-models --region ap-southeast-2
   ```

2. **Verify MCP Server Connectivity**
   ```bash
   uvx --from git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git jira-confluence-mcp --help
   ```

3. **Test JIRA/Confluence API**
   ```bash
   curl -u $JIRA_EMAIL:$JIRA_API_TOKEN $JIRA_URL/rest/api/2/myself
   ```

### Performance Issues

1. **Check Resource Usage**
   ```bash
   top -p $(pgrep -f "python.*main.py")
   iostat 1 5
   ```

2. **Analyze Logs for Bottlenecks**
   ```bash
   grep "took" /var/log/lzbot/application.log | tail -20
   ```

3. **Review Configuration**
   - Reduce Bedrock model tokens if responses are slow
   - Check network latency to AWS region
   - Verify MCP server performance

## Maintenance Procedures

### Weekly Maintenance

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== LZBot-5000 Weekly Maintenance ==="

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Clean old logs (keep 30 days)
find /var/log/lzbot/ -name "*.log" -mtime +30 -delete

# Update health check
python3 integration_test.py

# Check disk space
df -h

# Review error logs
echo "Errors in the last week:"
grep "ERROR\|CRITICAL" /var/log/lzbot/application.log | grep "$(date -d '7 days ago' +%Y-%m-%d)"

echo "Weekly maintenance completed"
```

### Monthly Maintenance

```bash
#!/bin/bash
# monthly_maintenance.sh

echo "=== LZBot-5000 Monthly Maintenance ==="

# Archive old outputs
mkdir -p archive
tar -czf archive/outputs_$(date +%Y%m).tar.gz outputs/

# Update dependencies
pip install --upgrade pydantic python-dotenv

# Check for uvx updates
curl -LsSf https://astral.sh/uv/install.sh | sh

# Generate usage report
echo "Usage report for $(date +%Y-%m):"
grep "Architecture design completed" /var/log/lzbot/application.log | wc -l
echo "Successful completions this month"

# Security check
echo "Checking for exposed credentials..."
grep -r "password\|token\|secret" . --exclude-dir=.git --exclude-dir=__pycache__ | grep -v ".md:" | grep -v "example"

echo "Monthly maintenance completed"
```

## Performance Tuning

### Configuration Optimization

```python
# config_optimization.py
"""Optimize configuration for production environment"""

# Bedrock model settings
OPTIMIZED_BEDROCK_CONFIG = {
    "max_tokens": 3000,      # Reduced for faster responses
    "temperature": 0.1,      # Lower for consistency
    "region": "ap-southeast-2"  # Closest region
}

# Logging optimization
PRODUCTION_LOGGING = {
    "level": "INFO",         # Reduce debug overhead
    "json_format": True,     # Better for log aggregation
    "include_timestamp": True
}

# MCP client optimization
MCP_CLIENT_CONFIG = {
    "connection_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1
}
```

### Memory Management

```bash
# Monitor memory usage
watch -n 5 'ps aux | grep python.*main.py'

# Check for memory leaks
python3 -c "
import psutil
import time
p = psutil.Process()
for i in range(5):
    print(f'Memory: {p.memory_info().rss / 1024 / 1024:.2f} MB')
    time.sleep(10)
"
```

## Security Operations

### Security Monitoring

```bash
# Check for failed authentication attempts
grep "authentication failed\|unauthorized" /var/log/lzbot/application.log

# Monitor API token usage
grep "API_TOKEN" /var/log/lzbot/application.log

# Check for suspicious activity
grep "unusual\|suspicious\|security" /var/log/lzbot/application.log
```

### Credential Rotation

```bash
#!/bin/bash
# rotate_credentials.sh

echo "=== Credential Rotation ==="

# Backup current config
cp .env .env.backup.$(date +%Y%m%d)

echo "1. Update JIRA API token in Atlassian admin"
echo "2. Update CONFLUENCE_API_TOKEN environment variable"
echo "3. Test new credentials"

# Test after update
python3 -c "
from config import load_config
config = load_config()
print('New credentials validated')
"

echo "Credential rotation completed"
```

### Security Audit

```bash
#!/bin/bash
# security_audit.sh

echo "=== Security Audit ==="

# Check file permissions
find . -type f -perm -o+w -exec ls -l {} \;

# Check for world-readable config files
find . -name "*.env" -o -name "config*" | xargs ls -la

# Verify TLS connections
grep -i "ssl\|tls" /var/log/lzbot/application.log

# Check for hardcoded secrets
grep -r "password\|token\|secret" . --exclude-dir=.git | grep -v ".md:"

echo "Security audit completed"
```

## Troubleshooting Playbook

### Issue: High Memory Usage

**Symptoms**: Application using >2GB RAM

**Investigation**:
```bash
# Check process memory
ps aux | grep python | head -5

# Check for memory leaks
python3 -m memory_profiler main.py
```

**Resolution**:
1. Restart application
2. Review recent architecture requests (complex requests use more memory)
3. Consider increasing instance size if persistent

### Issue: Slow Response Times

**Symptoms**: Architecture generation taking >60 seconds

**Investigation**:
```bash
# Check AWS Bedrock latency
time aws bedrock list-foundation-models --region ap-southeast-2

# Check MCP server response
time uvx --from git+https://github.com/vishnuprasad-mantel/jira-confluence-mcp-server.git jira-confluence-mcp --help
```

**Resolution**:
1. Check network connectivity
2. Reduce max_tokens in Bedrock config
3. Verify AWS region selection

### Issue: JIRA Integration Failures

**Symptoms**: "JIRA API authentication failed"

**Investigation**:
```bash
# Test JIRA connectivity
curl -u $JIRA_EMAIL:$JIRA_API_TOKEN $JIRA_URL/rest/api/2/myself

# Check token expiration
curl -u $JIRA_EMAIL:$JIRA_API_TOKEN $JIRA_URL/rest/api/2/myself | jq .
```

**Resolution**:
1. Verify API token is current
2. Check JIRA permissions
3. Regenerate API token if needed

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/lzbot-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp .env "$BACKUP_DIR/"

# Backup recent outputs
cp -r outputs/ "$BACKUP_DIR/"

# Backup logs
cp -r /var/log/lzbot/ "$BACKUP_DIR/"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup created: $BACKUP_DIR.tar.gz"
```

### Recovery Procedures

```bash
#!/bin/bash
# recovery.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# Extract backup
tar -xzf "$BACKUP_FILE"
BACKUP_DIR="${BACKUP_FILE%.tar.gz}"

# Restore configuration
cp "$BACKUP_DIR/.env" .

# Restore outputs
cp -r "$BACKUP_DIR/outputs/" .

echo "Recovery completed from $BACKUP_FILE"
```

## Contact Information

### Escalation Matrix

| Severity | Contact | Response Time |
|----------|---------|---------------|
| Critical | On-call engineer | 15 minutes |
| High | Team lead | 2 hours |
| Medium | Developer team | 4 hours |
| Low | Standard support | 24 hours |

### Emergency Contacts

- **System Administrator**: admin@company.com
- **Development Team**: dev-team@company.com
- **Security Team**: security@company.com

### Support Resources

- **Documentation**: README.md, DEPLOYMENT.md
- **Issue Tracking**: Git repository issues
- **Monitoring**: Company monitoring dashboard
- **Logs**: Centralized logging system