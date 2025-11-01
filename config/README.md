# Configuration Structure

OmicsOracle uses a dual-configuration system for flexibility and clarity.

## Two Configuration Locations

### 1. Root Configuration (`/config/`)
**Purpose**: Deployment and infrastructure configuration

```
config/
├── development.yml     - Development environment settings
├── production.yml      - Production environment settings
├── testing.yml         - Test environment settings
├── nginx.conf          - Nginx web server configuration
├── nginx.ssl.conf      - Nginx SSL configuration
└── prometheus.yml      - Prometheus monitoring configuration
```

**Used For**:
- Environment-specific settings
- Web server configuration
- Monitoring configuration
- Deployment configuration

### 2. Application Configuration (`/omics_oracle_v2/config/`)
**Purpose**: Application business logic configuration

**Used For**:
- Application constants
- Feature flags
- Business logic configuration
- Module-specific settings

## Configuration Hierarchy

```
Environment Variables (.env)
        ↓
Root Config (config/*.yml)
        ↓
Application Config (omics_oracle_v2/config/)
        ↓
Application Code
```

## Usage Guidelines

### When to use `/config/`
- Setting up new deployment environments
- Configuring web servers (Nginx)
- Setting up monitoring (Prometheus)
- Environment-specific overrides

### When to use `/omics_oracle_v2/config/`
- Application feature configuration
- Module-specific settings
- Business logic constants
- Code-level configuration

## Environment Variables

Primary configuration method via `.env` file:

```bash
# API Keys
OPENAI_API_KEY=sk-...
NCBI_EMAIL=user@example.com
NCBI_API_KEY=...

# Application Settings
OMICS_AI_MODEL=gpt-4-turbo-preview
OMICS_AI_MAX_TOKENS=4000

# Database
DATABASE_URL=sqlite:///omics_oracle.db

# Redis Cache
REDIS_URL=redis://localhost:6379/0
```

## Configuration Loading Order

1. **Environment variables** (`.env` file)
2. **Root config files** (`config/*.yml`) based on environment
3. **Application config** (`omics_oracle_v2/core/config.py`)
4. **Module configs** (if any)

## Best Practices

### ✅ DO:
- Use environment variables for secrets and API keys
- Use root config for deployment settings
- Use app config for business logic
- Document all configuration options
- Provide `.env.example` for reference

### ❌ DON'T:
- Commit secrets to version control
- Duplicate configuration across locations
- Hard-code configuration in application code
- Mix deployment and application configuration

## Example Configurations

### Development Setup
```bash
# .env
ENVIRONMENT=development
DEBUG=true
OMICS_AI_MODEL=gpt-4-turbo-preview
```

### Production Setup
```bash
# .env
ENVIRONMENT=production
DEBUG=false
OMICS_AI_MODEL=gpt-4-turbo-preview
DATABASE_URL=postgresql://...
REDIS_URL=redis://production:6379/0
```

## Configuration Files Reference

| File | Purpose | When to Edit |
|------|---------|--------------|
| `.env` | Environment variables | Always (local development) |
| `config/development.yml` | Dev environment | Adding dev-specific settings |
| `config/production.yml` | Prod environment | Production deployment |
| `config/nginx.conf` | Web server | Changing server config |
| `omics_oracle_v2/core/config.py` | App config | Application settings |

## Troubleshooting

### Configuration not loading?
1. Check `.env` file exists in project root
2. Verify environment variable names are correct
3. Check `ENVIRONMENT` variable matches config file
4. Restart application after config changes

### Settings being overridden?
Check configuration hierarchy - environment variables > root config > app config

---

**Last Updated**: October 31, 2025
**Maintainer**: OmicsOracle Team
