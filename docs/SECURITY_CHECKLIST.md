# Pre-Launch Security Checklist

This checklist should be completed before deploying Zaoya v0 to production.

## Authentication

- [ ] JWT tokens expire appropriately (default: 7 days)
- [ ] JWT secret key is strong and randomly generated
- [ ] Password hashing uses bcrypt with appropriate work factor
- [ ] OAuth secrets are stored in environment variables (not in code)
- [ ] OAuth redirect URIs are properly configured
- [ ] Session invalidation works on password change
- [ ] Token refresh mechanism is working

## Input Validation

- [ ] All user input is sanitized (HTML/JS stripped from form data)
- [ ] SQL injection prevented (parameterized queries only)
- [ ] XSS prevented (output encoding, CSP headers)
- [ ] File uploads validated (type, size) - if implemented
- [ ] Email addresses validated before use
- [ ] URL parameters validated and length-limited

## Network Security

- [ ] HTTPS enforced everywhere (redirect HTTP to HTTPS)
- [ ] CORS properly configured (not allowing `*` in production)
- [ ] Rate limiting is active (100 req/min, 1000 req/hour)
- [ ] CSP headers present on published pages
- [ ] WebSocket connections authenticated (if used)

## Published Page Security

- [ ] Published pages served from separate domain (pages.zaoya.app)
- [ ] CSP blocks all inline scripts except zaoya-runtime.js
- [ ] frame-ancestors set to 'none' (prevents clickjacking)
- [ ] No auth cookies sent to published pages
- [ ] Generated JavaScript validated via AST

## Data Protection

- [ ] Sensitive data encrypted at rest (passwords, API keys)
- [ ] Secrets stored in environment variables only
- [ ] Database backups encrypted
- [ ] Logs don't contain secrets or PII
- [ ] IP addresses hashed for analytics (privacy-friendly)

## API Security

- [ ] Request size limited (10MB max)
- [ ] Rate limiting per IP active
- [ ] Error messages don't leak implementation details
- [ ] API versioning implemented
- [ ] Deprecated endpoints marked for removal

## Monitoring

- [ ] Error logging configured and working
- [ ] Failed login attempts tracked
- [ ] Rate limit violations logged
- [ ] Unusual activity alerts configured
- [ ] Uptime monitoring set up

## Dependencies

- [ ] Dependencies regularly updated
- [ ] No known critical vulnerabilities in dependencies
- [ ] Unnecessary dependencies removed
- [ ] License compliance checked

## Production Configuration

- [ ] DEBUG mode disabled
- [ ] ENVIRONMENT set to "production"
- [ ] SECRET_KEY changed from default
- [ ] Database URL uses production database
- [ ] CORS origins set to actual domains
- [ ] Email API keys configured
- [ ] AI API keys configured

## Testing

- [ ] Security testing performed (OWASP Top 10)
- [ ] Penetration testing completed
- [ ] Error handling tested
- [ ] Rate limiting tested
- [ ] Authentication flow tested end-to-end

## Compliance

- [ ] Privacy policy in place
- [ ] Terms of service in place
- [ ] GDPR considerations addressed (EU users)
- [ ] Data retention policy defined
- [ ] User data export functionality available
- [ ] User data deletion functionality available

## Post-Launch

- [ ] Security incident response plan prepared
- [ ] Bug bounty program considered
- [ ] Regular security audits scheduled
- [ ] Dependency scanning automated
