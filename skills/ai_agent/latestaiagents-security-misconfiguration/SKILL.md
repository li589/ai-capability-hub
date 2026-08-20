---
name: security-misconfiguration
description: |
  OWASP A06 - Security Misconfiguration Detection. Use this skill when configuring
  servers, frameworks, cloud services, or deploying applications. Activate when:
  server config, nginx config, apache config, CORS, headers, debug mode, default credentials,
  error messages, directory listing, cloud security, S3 bucket, environment variables.
install_source: official
install_method: download
skill_id: official_QZAAnZ9Y
enabled_at: 1787232602289
version: 1.0.0
name_zh: 安全开发
---

# Security Misconfiguration (OWASP A06)

**Detect and fix insecure default configurations, missing security headers, exposed debug info, and cloud misconfigurations.**

## When to Use

- Configuring web servers (Nginx, Apache)
- Setting up cloud resources (AWS, GCP, Azure)
- Deploying applications to production
- Reviewing security headers
- Auditing CORS configuration
- Checking for exposed sensitive endpoints

## Common Misconfigurations

| Issue | Risk | Impact |
|-------|------|--------|
| Debug mode enabled | HIGH | Information disclosure |
| Default credentials | CRITICAL | Full system compromise |
| Missing security headers | MEDIUM | XSS, clickjacking |
| Directory listing | MEDIUM | Information disclosure |
| Verbose error messages | MEDIUM | Attack surface exposure |
| Open cloud storage | CRITICAL | Data breach |
| Unnecessary services | MEDIUM | Increased attack surface |

## Detection Patterns

### Debug Mode in Production

```javascript
// VULNERABLE - Debug mode enabled
app.set('env', 'development');
DEBUG=* node app.js

// VULNERABLE - Stack traces in errors
app.use((err, req, res, next) => {
  res.status(500).json({
    error: err.message,
    stack: err.stack // Never in production!
  });
});

// VULNERABLE - Source maps in production
// webpack.config.js
devtool: 'source-map' // Exposes source code
```

### Missing Security Headers

```javascript
// VULNERABLE - No security headers set
app.get('/', (req, res) => {
  res.send('<html>...</html>');
});

// Check current headers
curl -I https://example.com
// Missing: X-Frame-Options, CSP, etc.
```

### CORS Misconfiguration

```javascript
// VULNERABLE - Allow all origins
app.use(cors({
  origin: '*',
  credentials: true // Dangerous with wildcard!
}));

// VULNERABLE - Reflecting origin
app.use(cors({
  origin: req.headers.origin, // Reflects any origin
  credentials: true
}));
```

### Cloud Storage Misconfiguration

```json
// VULNERABLE - Public S3 bucket policy
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-bucket/*"
  }]
}
```

## Secure Implementation

### 1. Security Headers (Express.js)

```javascript
const helmet = require('helmet');

app.use(helmet({
  // Content Security Policy
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"], // Adjust as needed
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.example.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      objectSrc: ["'none'"],
      frameAncestors: ["'none'"],
      upgradeInsecureRequests: []
    }
  },

  // Prevent clickjacking
  frameguard: { action: 'deny' },

  // Prevent MIME type sniffing
  noSniff: true,

  // XSS filter
  xssFilter: true,

  // HSTS
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  },

  // Referrer policy
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },

  // Permissions policy
  permittedCrossDomainPolicies: { permittedPolicies: 'none' }
}));

// Additional headers
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Permitted-Cross-Domain-Policies', 'none');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  next();
});
```

### 2. CORS Configuration

```javascript
const cors = require('cors');

const allowedOrigins = [
  'https://example.com',
  'https://app.example.com',
  'https://admin.example.com'
];

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, curl)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS not allowed'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['X-Total-Count'],
  maxAge: 86400 // 24 hours
}));
```

### 3. Production Error Handling

```javascript
// Environment-aware error handler
app.use((err, req, res, next) => {
  // Log full error for debugging
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
    userId: req.user?.id
  });

  // Send safe response
  const statusCode = err.statusCode || 500;
  const response = {
    error: {
      message: statusCode === 500
        ? 'Internal server error'  // Generic message in production
        : err.message,
      code: err.code || 'UNKNOWN_ERROR',
      requestId: req.id // For support tickets
    }
  };

  // Include stack trace only in development
  if (process.env.NODE_ENV === 'development') {
    response.error.stack = err.stack;
  }

  res.status(statusCode).json(response);
});
```

### 4. Nginx Secure Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # SSL Configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';" always;

    # Hide server version
    server_tokens off;

    # Disable directory listing
    autoindex off;

    # Block access to hidden files
    location ~ /\. {
        deny all;
    }

    # Block access to sensitive files
    location ~* \.(git|env|config|sql|log|bak|swp)$ {
        deny all;
    }

    # Restrict methods
    if ($request_method !~ ^(GET|POST|PUT|DELETE|OPTIONS)$) {
        return 405;
    }
}
```

### 5. AWS S3 Secure Configuration

```javascript
// Secure S3 bucket policy
const s3BucketPolicy = {
  Version: '2012-10-17',
  Statement: [
    {
      Sid: 'DenyPublicAccess',
      Effect: 'Deny',
      Principal: '*',
      Action: 's3:*',
      Resource: [
        'arn:aws:s3:::my-bucket',
        'arn:aws:s3:::my-bucket/*'
      ],
      Condition: {
        Bool: {
          'aws:SecureTransport': 'false'
        }
      }
    }
  ]
};

// Block public access settings
const publicAccessBlock = {
  BlockPublicAcls: true,
  IgnorePublicAcls: true,
  BlockPublicPolicy: true,
  RestrictPublicBuckets: true
};
```

```bash
# AWS CLI - Block public access
aws s3api put-public-access-block \
  --bucket my-bucket \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 6. Environment Configuration

```javascript
// config/index.js - Environment-aware configuration
const config = {
  development: {
    debug: true,
    logLevel: 'debug',
    sourceMaps: true,
    showErrors: true
  },
  production: {
    debug: false,
    logLevel: 'error',
    sourceMaps: false,
    showErrors: false,
    helmet: true,
    rateLimit: true
  }
};

module.exports = config[process.env.NODE_ENV] || config.production;
```

### 7. Docker Security

```dockerfile
# Use specific version, not 'latest'
FROM node:20.11-alpine

# Run as non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

WORKDIR /app

# Copy package files first (better caching)
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Don't expose unnecessary ports
EXPOSE 3000

# Use exec form, not shell form
CMD ["node", "server.js"]
```

## Security Configuration Checklist

### Server Configuration
- [ ] Debug mode disabled in production
- [ ] Server version headers hidden
- [ ] Directory listing disabled
- [ ] Default pages removed
- [ ] Unnecessary services disabled
- [ ] TLS 1.2+ only
- [ ] Strong cipher suites

### Application Configuration
- [ ] Security headers set (CSP, HSTS, etc.)
- [ ] CORS properly configured
- [ ] Error messages don't leak info
- [ ] Source maps disabled in production
- [ ] Default credentials changed
- [ ] Secrets in environment variables

### Cloud Configuration
- [ ] S3 buckets not public
- [ ] IAM roles use least privilege
- [ ] Security groups restrict access
- [ ] Logging enabled
- [ ] Encryption at rest enabled

## Testing Tools

```bash
# Check security headers
curl -I https://example.com

# Online header checker
# https://securityheaders.com

# SSL/TLS configuration
# https://www.ssllabs.com/ssltest/

# Check for exposed .git
curl -I https://example.com/.git/HEAD

# Check for directory listing
curl https://example.com/images/

# S3 bucket checker
aws s3 ls s3://bucket-name --no-sign-request
```

## Best Practices

1. **Use Configuration Management**: Ansible, Terraform, etc.
2. **Automate Security Scans**: In CI/CD pipeline
3. **Environment Separation**: Different configs for dev/staging/prod
4. **Regular Audits**: Review configurations periodically
5. **Principle of Least Privilege**: Minimal permissions
6. **Defense in Depth**: Multiple security layers
7. **Monitor Changes**: Alert on configuration changes
