# Phase 3: Scale (Zaoya v1)

> **Version**: v1
> **Timeline**: Months 5-6 (Post v0 Launch)
> **Complexity**: Large
> **Status**: Pending

---

## Phase Overview

Phase 3 focuses on infrastructure maturity and team enablement. Custom domains establish professional credibility for users, team collaboration unlocks B2B opportunities, integrations connect Zaoya to the broader ecosystem, and PostgreSQL migration prepares for enterprise scale.

### Connection to Project Goals

This phase expands the addressable market from individual creators to small teams and businesses. Custom domains and integrations make Zaoya suitable for professional use cases, while the database migration ensures reliable performance as usage grows.

---

## Prerequisites

### From Phase 2 (Must be completed)

- [ ] A/B testing system operational
- [ ] Advanced analytics functional
- [ ] AI image generation working
- [ ] Premium tier launched and generating revenue
- [ ] Payment integration stable

### Technical Prerequisites

- [ ] SSL certificate automation solution identified
- [ ] PostgreSQL instance provisioned
- [ ] Email service provider selected (Resend, SendGrid, etc.)
- [ ] Team/workspace data model designed

---

## Detailed Tasks

### 1. Custom Domains

#### 1.1 Domain Configuration System

**Foundation for custom domains**

```typescript
interface CustomDomain {
  id: string;
  project_id: string;
  domain: string;           // "example.com" or "app.example.com"
  verification_status: 'pending' | 'verified' | 'failed';
  ssl_status: 'pending' | 'provisioning' | 'active' | 'error';
  verification_token: string;
  verified_at?: Date;
  created_at: Date;
}

// DNS verification record
interface VerificationRecord {
  type: 'TXT';
  host: '_zaoya-verify';
  value: string;  // e.g., "zaoya-site-verification=abc123"
}

// Required CNAME record
interface CNAMERecord {
  type: 'CNAME';
  host: '@' | 'www' | string;  // Subdomain or root
  value: 'pages.zaoya.app';
}
```

**Tasks**:
- [ ] Create `custom_domains` table migration
- [ ] Generate unique verification tokens
- [ ] Implement domain validation (format, not blocked)
- [ ] Create domain configuration API endpoints
- [ ] Build domain management UI
- [ ] Add domain limit per plan (Pro: 1, Team: 3, Business: 10)

#### 1.2 DNS Verification

**Sequential: Core verification flow**

```typescript
// Verification flow
async function verifyDomain(domain: CustomDomain): Promise<boolean> {
  const txtRecords = await dns.resolveTxt(`_zaoya-verify.${domain.domain}`);

  for (const record of txtRecords) {
    const value = record.join('');
    if (value === `zaoya-site-verification=${domain.verification_token}`) {
      return true;
    }
  }
  return false;
}

// Verification job (runs periodically)
async function domainVerificationJob() {
  const pendingDomains = await db.customDomain.findMany({
    where: { verification_status: 'pending' }
  });

  for (const domain of pendingDomains) {
    const verified = await verifyDomain(domain);
    if (verified) {
      await db.customDomain.update({
        where: { id: domain.id },
        data: {
          verification_status: 'verified',
          verified_at: new Date(),
        }
      });
      await provisionSSL(domain);
    }
  }
}
```

**Tasks**:
- [ ] Implement DNS TXT record lookup
- [ ] Create verification check endpoint (manual trigger)
- [ ] Build background verification job (every 5 min)
- [ ] Handle verification timeout (expire after 7 days)
- [ ] Send email on verification success/failure
- [ ] Show clear DNS instructions in UI

#### 1.3 SSL Certificate Provisioning

**Sequential: Depends on verification**

```typescript
// Using Let's Encrypt via Cloudflare or similar
interface SSLCertificate {
  domain: string;
  issued_at: Date;
  expires_at: Date;
  auto_renew: boolean;
}

// Cloudflare for SaaS approach
async function provisionSSL(domain: CustomDomain): Promise<void> {
  // Option 1: Cloudflare for SaaS
  await cloudflare.customHostnames.create({
    zone_id: ZAOYA_ZONE_ID,
    hostname: domain.domain,
    ssl: {
      method: 'http',
      type: 'dv',
    }
  });

  // Option 2: Let's Encrypt with Caddy/Traefik
  // Caddy automatically provisions certs for configured domains
}

// Certificate renewal job
async function renewCertificates() {
  const expiringSoon = await db.customDomain.findMany({
    where: {
      ssl_status: 'active',
      ssl_expires_at: { lte: addDays(new Date(), 30) }
    }
  });

  for (const domain of expiringSoon) {
    await renewSSL(domain);
  }
}
```

**Tasks**:
- [ ] Set up Cloudflare for SaaS (recommended) or Let's Encrypt
- [ ] Implement SSL provisioning on verification
- [ ] Create SSL status tracking
- [ ] Build certificate renewal job
- [ ] Handle provisioning failures with retry
- [ ] Show SSL status in domain settings

#### 1.4 Custom Domain Routing

**Sequential: Brings it all together**

```typescript
// Request routing middleware
async function customDomainMiddleware(req: Request, next: Next) {
  const host = req.headers.get('host');

  // Check if custom domain
  if (!host.endsWith('.zaoya.app')) {
    const customDomain = await db.customDomain.findFirst({
      where: {
        domain: host,
        verification_status: 'verified',
        ssl_status: 'active',
      },
      include: { project: true }
    });

    if (customDomain) {
      // Rewrite to project content
      req.projectId = customDomain.project_id;
      return serveProject(req, customDomain.project);
    }

    return new Response('Domain not configured', { status: 404 });
  }

  return next(req);
}
```

**Tasks**:
- [ ] Implement custom domain routing middleware
- [ ] Handle www vs non-www normalization
- [ ] Support subdomain custom domains
- [ ] Update canonical URLs for custom domains
- [ ] Add custom domain to project settings
- [ ] Test SSL handshake and routing end-to-end

#### 1.5 Domain Management UI

**Parallelizable with backend**

```
┌────────────────────────────────────────────────────────────────────┐
│ Custom Domain Settings                                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Current Domain: example.com                                        │
│ Status: ✅ Verified | 🔒 SSL Active                                │
│                                                                    │
│ ─────────────────────────────────────────────────────────────────  │
│                                                                    │
│ To connect a new domain, add these DNS records:                    │
│                                                                    │
│ ┌────────┬──────────────────┬─────────────────────────────────┐   │
│ │ Type   │ Host             │ Value                           │   │
│ ├────────┼──────────────────┼─────────────────────────────────┤   │
│ │ TXT    │ _zaoya-verify    │ zaoya-site-verification=abc123  │   │
│ │ CNAME  │ @                │ pages.zaoya.app                 │   │
│ └────────┴──────────────────┴─────────────────────────────────┘   │
│                                                                    │
│ [Copy DNS Records]                       [Check Verification]      │
│                                                                    │
│ ⚠️ DNS changes can take up to 48 hours to propagate                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create domain settings panel in project settings
- [ ] Build DNS record display with copy buttons
- [ ] Show verification status with progress
- [ ] Add SSL status indicator
- [ ] Create "Check Now" verification button
- [ ] Handle domain removal/change
- [ ] Show troubleshooting tips

---

### 2. Team Collaboration (Basic)

#### 2.1 Team Data Model

**Foundation for collaboration**

```typescript
interface Team {
  id: string;
  name: string;
  slug: string;           // For team URL: /team/{slug}
  owner_id: string;
  plan: 'team' | 'business' | 'enterprise';
  created_at: Date;
}

interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  invited_by: string;
  joined_at: Date;
}

interface TeamInvite {
  id: string;
  team_id: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  token: string;
  expires_at: Date;
  accepted_at?: Date;
  created_at: Date;
}

// Project ownership can be user OR team
interface Project {
  // Existing fields...
  owner_type: 'user' | 'team';
  owner_id: string;  // user_id or team_id
}
```

**Tasks**:
- [ ] Create `teams` table migration
- [ ] Create `team_members` table with roles
- [ ] Create `team_invites` table
- [ ] Update projects table for team ownership
- [ ] Add unique constraint on team slug
- [ ] Create indexes for efficient queries

#### 2.2 Team Management

**Sequential: Core team functionality**

```typescript
// Team API endpoints
POST   /api/teams                    // Create team
GET    /api/teams                    // List user's teams
GET    /api/teams/:id                // Get team details
PUT    /api/teams/:id                // Update team settings
DELETE /api/teams/:id                // Delete team (owner only)

// Member management
GET    /api/teams/:id/members        // List members
POST   /api/teams/:id/members        // Invite member
PUT    /api/teams/:id/members/:uid   // Update member role
DELETE /api/teams/:id/members/:uid   // Remove member

// Invites
POST   /api/teams/:id/invites        // Create invite
GET    /api/invites/:token           // Get invite details
POST   /api/invites/:token/accept    // Accept invite
DELETE /api/teams/:id/invites/:iid   // Cancel invite
```

**Tasks**:
- [ ] Implement team CRUD endpoints
- [ ] Create member management endpoints
- [ ] Build invite system with email sending
- [ ] Implement invite acceptance flow
- [ ] Add team switching in UI
- [ ] Handle team deletion (transfer or delete projects)

#### 2.3 Role-Based Permissions

**Sequential: Depends on team model**

```typescript
type Permission =
  | 'project:create'
  | 'project:edit'
  | 'project:delete'
  | 'project:publish'
  | 'team:manage_members'
  | 'team:manage_settings'
  | 'team:manage_billing';

const rolePermissions: Record<string, Permission[]> = {
  owner: [
    'project:create', 'project:edit', 'project:delete', 'project:publish',
    'team:manage_members', 'team:manage_settings', 'team:manage_billing'
  ],
  admin: [
    'project:create', 'project:edit', 'project:delete', 'project:publish',
    'team:manage_members', 'team:manage_settings'
  ],
  editor: [
    'project:create', 'project:edit', 'project:publish'
  ],
  viewer: [
    // Read-only access
  ],
};

// Permission check middleware
function requirePermission(permission: Permission) {
  return async (req: Request, next: Next) => {
    const user = req.user;
    const teamId = req.params.teamId || req.body.teamId;

    const member = await db.teamMember.findFirst({
      where: { team_id: teamId, user_id: user.id }
    });

    if (!member || !rolePermissions[member.role].includes(permission)) {
      return new Response('Forbidden', { status: 403 });
    }

    return next(req);
  };
}
```

**Tasks**:
- [ ] Define role-permission matrix
- [ ] Create permission check utility
- [ ] Implement permission middleware
- [ ] Update all team endpoints with permission checks
- [ ] Add permission UI (show/hide actions based on role)
- [ ] Test all permission boundaries

#### 2.4 Team UI

**Parallelizable with backend**

```
┌────────────────────────────────────────────────────────────────────┐
│ Team: Acme Inc                                      [Settings ⚙️]  │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Members (4/5)                                        [Invite +]    │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐    │
│ │ 👤 John Doe           john@acme.com         Owner      ⋮  │    │
│ │ 👤 Jane Smith         jane@acme.com         Admin      ⋮  │    │
│ │ 👤 Bob Wilson         bob@acme.com          Editor     ⋮  │    │
│ │ 👤 Alice Brown        alice@acme.com        Viewer     ⋮  │    │
│ └────────────────────────────────────────────────────────────┘    │
│                                                                    │
│ Pending Invites (1)                                                │
│                                                                    │
│ ┌────────────────────────────────────────────────────────────┐    │
│ │ ✉️ charlie@acme.com    Editor    Expires in 6 days   [X]   │    │
│ └────────────────────────────────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create team dashboard page
- [ ] Build member list with role badges
- [ ] Implement invite modal
- [ ] Add role change dropdown
- [ ] Create member removal confirmation
- [ ] Build pending invites section
- [ ] Add team settings page
- [ ] Implement team switcher in sidebar

#### 2.5 Activity Feed

**Parallelizable with other team features**

```typescript
interface ActivityEvent {
  id: string;
  team_id: string;
  user_id: string;
  action: string;
  resource_type: 'project' | 'page' | 'member' | 'settings';
  resource_id: string;
  metadata: Record<string, any>;
  created_at: Date;
}

// Example activities:
// - "John created project 'Landing Page'"
// - "Jane published page 'Home'"
// - "Bob invited alice@acme.com"
// - "Alice updated project settings"
```

**Tasks**:
- [ ] Create activity_events table
- [ ] Log activities on key actions
- [ ] Build activity feed API endpoint
- [ ] Create activity feed UI component
- [ ] Add filtering by resource type
- [ ] Implement pagination

---

### 3. First Integrations

#### 3.1 Stripe Integration

**Payment integration in published pages**

```typescript
interface StripeIntegration {
  project_id: string;
  stripe_account_id: string;  // Connected account
  connected_at: Date;
  webhook_secret: string;
}

// User connects their Stripe account
// Published pages can then include payment forms
// Revenue goes directly to user's Stripe account
```

**Tasks**:
- [ ] Implement Stripe Connect OAuth flow
- [ ] Store connected account credentials
- [ ] Create payment form component for generated pages
- [ ] Handle webhook events for payment confirmations
- [ ] Add payment success/failure pages
- [ ] Show payment analytics in dashboard

#### 3.2 Email Marketing Integration

**Capture leads and sync to email platforms**

```typescript
interface EmailIntegration {
  project_id: string;
  provider: 'mailchimp' | 'convertkit' | 'resend';
  api_key: string;  // Encrypted
  list_id?: string;
  connected_at: Date;
}

// Form submissions can be synced to email lists
async function syncToEmailProvider(
  integration: EmailIntegration,
  submission: FormSubmission
) {
  switch (integration.provider) {
    case 'mailchimp':
      return mailchimp.lists.addMember(integration.list_id, {
        email_address: submission.email,
        merge_fields: submission.fields,
      });
    case 'convertkit':
      return convertkit.subscribers.create({
        email: submission.email,
        fields: submission.fields,
      });
    // ...
  }
}
```

**Tasks**:
- [ ] Implement Mailchimp integration
- [ ] Implement ConvertKit integration
- [ ] Implement Resend integration
- [ ] Create integration settings UI
- [ ] Map form fields to email provider fields
- [ ] Handle sync errors gracefully
- [ ] Show sync status in form submissions

#### 3.3 Webhook System

**Allow users to send data to external services**

```typescript
interface Webhook {
  id: string;
  project_id: string;
  url: string;
  events: string[];  // ['form_submit', 'page_view', 'conversion']
  secret: string;    // For signature verification
  active: boolean;
  created_at: Date;
}

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event: string;
  payload: Record<string, any>;
  response_status: number;
  response_body?: string;
  delivered_at: Date;
}

// Webhook delivery
async function deliverWebhook(webhook: Webhook, event: string, data: any) {
  const payload = {
    event,
    data,
    timestamp: new Date().toISOString(),
    project_id: webhook.project_id,
  };

  const signature = createHmac('sha256', webhook.secret)
    .update(JSON.stringify(payload))
    .digest('hex');

  const response = await fetch(webhook.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Zaoya-Signature': signature,
    },
    body: JSON.stringify(payload),
  });

  // Log delivery
  await db.webhookDelivery.create({
    data: {
      webhook_id: webhook.id,
      event,
      payload,
      response_status: response.status,
      response_body: await response.text(),
    }
  });
}
```

**Tasks**:
- [ ] Create webhooks table and delivery log
- [ ] Implement webhook registration API
- [ ] Build webhook delivery system with retries
- [ ] Add signature verification documentation
- [ ] Create webhook management UI
- [ ] Show delivery history with status
- [ ] Implement webhook testing (send test event)

#### 3.4 Zapier Integration

**Connect to 5000+ apps via Zapier**

```typescript
// Zapier triggers (events Zaoya sends to Zapier)
const zapierTriggers = [
  'new_form_submission',
  'new_visitor',
  'conversion_goal_reached',
  'page_published',
];

// Zapier actions (things Zaoya can do from Zapier)
const zapierActions = [
  'create_project',
  'publish_page',
  'update_content',
];
```

**Tasks**:
- [ ] Create Zapier app in Zapier Developer Platform
- [ ] Implement trigger endpoints (polling or hooks)
- [ ] Implement action endpoints
- [ ] Create authentication flow
- [ ] Write Zapier app documentation
- [ ] Submit for Zapier review (optional for v1)

---

### 4. PostgreSQL Migration

#### 4.1 Migration Planning

**Critical: Production database migration**

```typescript
// Current: SQLite (better-sqlite3)
// Target: PostgreSQL (via Drizzle ORM)

// Migration steps:
// 1. Set up PostgreSQL instance (Neon, Supabase, or self-hosted)
// 2. Update Drizzle config for PostgreSQL
// 3. Run schema migrations on PostgreSQL
// 4. Create data migration script
// 5. Test thoroughly in staging
// 6. Execute migration with minimal downtime
```

**Tasks**:
- [ ] Provision PostgreSQL instance
- [ ] Update Drizzle configuration
- [ ] Generate PostgreSQL migrations
- [ ] Test schema compatibility
- [ ] Document migration runbook

#### 4.2 Data Migration Script

**Sequential: After schema is ready**

```typescript
// Migration script
async function migrateData() {
  // 1. Export SQLite data
  const sqliteDb = new Database('zaoya.db');
  const tables = ['users', 'projects', 'pages', 'analytics_events', ...];

  for (const table of tables) {
    console.log(`Migrating ${table}...`);
    const rows = sqliteDb.prepare(`SELECT * FROM ${table}`).all();

    // 2. Batch insert to PostgreSQL
    const batchSize = 1000;
    for (let i = 0; i < rows.length; i += batchSize) {
      const batch = rows.slice(i, i + batchSize);
      await pgDb.insert(table).values(batch);
    }

    console.log(`Migrated ${rows.length} rows from ${table}`);
  }
}
```

**Tasks**:
- [ ] Create data export script from SQLite
- [ ] Handle data type conversions (e.g., JSON, dates)
- [ ] Implement batch insertion for performance
- [ ] Verify row counts match
- [ ] Test data integrity

#### 4.3 Zero-Downtime Migration

**Sequential: Production cutover**

```
┌──────────────────────────────────────────────────────────────────┐
│                    Migration Timeline                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ T-7 days:  Set up PostgreSQL, test migrations                    │
│ T-3 days:  Run data migration to PostgreSQL (read-only copy)     │
│ T-1 day:   Final testing, team notification                      │
│                                                                  │
│ T-0 (Migration Window):                                          │
│   1. Enable maintenance mode (30 min window)                     │
│   2. Final data sync (delta since T-3)                           │
│   3. Switch DATABASE_URL to PostgreSQL                           │
│   4. Verify application health                                   │
│   5. Disable maintenance mode                                    │
│                                                                  │
│ T+1 day:  Monitor for issues, keep SQLite backup                 │
│ T+7 days: Decommission SQLite                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Tasks**:
- [ ] Create maintenance mode page
- [ ] Build delta sync script (changes since initial migration)
- [ ] Prepare rollback plan
- [ ] Coordinate with team on migration window
- [ ] Execute migration
- [ ] Monitor post-migration

#### 4.4 Performance Optimization

**Post-migration improvements**

```typescript
// PostgreSQL-specific optimizations

// 1. Connection pooling
import { Pool } from 'pg';
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
});

// 2. Query optimization
// Add indexes for common queries
CREATE INDEX idx_analytics_project_date ON analytics_events(project_id, timestamp);
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_pages_project ON pages(project_id, slug);

// 3. Read replicas for analytics (future)
// Route heavy read queries to replica
```

**Tasks**:
- [ ] Configure connection pooling
- [ ] Add production indexes
- [ ] Set up query monitoring (pg_stat_statements)
- [ ] Optimize slow queries identified
- [ ] Plan read replica setup (for Phase 4+)

---

## Technical Considerations

### Custom Domains

- **SSL Provider**: Cloudflare for SaaS is easiest, Let's Encrypt with Caddy for self-hosted
- **DNS Propagation**: Can take 24-48 hours; set expectations
- **Wildcard vs Individual**: Start with individual certs, wildcard adds complexity

### Team Collaboration

- **Data Isolation**: Ensure team data is isolated from personal accounts
- **Audit Trail**: Log all permission changes for compliance
- **Invite Security**: Use cryptographically secure tokens, expire quickly

### PostgreSQL Migration

- **Downtime**: Aim for < 30 minutes
- **Data Integrity**: Verify all foreign keys and constraints
- **Rollback Plan**: Keep SQLite running in read-only mode during migration

---

## Acceptance Criteria

### Custom Domains
- [ ] User can add custom domain to project
- [ ] DNS verification works within 5 minutes of correct records
- [ ] SSL certificate provisions automatically
- [ ] Custom domain serves project content correctly
- [ ] www redirect works (www.example.com → example.com)

### Team Collaboration
- [ ] User can create team and invite members
- [ ] Invites send email with acceptance link
- [ ] Roles correctly restrict actions
- [ ] Team projects visible to all team members
- [ ] Activity feed shows team actions

### Integrations
- [ ] Stripe Connect works for payment forms
- [ ] Form submissions sync to email providers
- [ ] Webhooks deliver events reliably
- [ ] Integration settings UI is clear

### PostgreSQL Migration
- [ ] All data migrated without loss
- [ ] Application performance equal or better
- [ ] Migration completes within 30-minute window
- [ ] No application errors post-migration

---

## Risk Factors

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SSL provisioning failures | Medium | Medium | Clear error messages, manual fallback process |
| Permission bugs expose data | High | Low | Thorough permission testing, audit logging |
| Integration API changes | Medium | Medium | Version pinning, monitoring for deprecations |
| Database migration data loss | Critical | Low | Multiple backups, verification scripts, rollback plan |
| DNS propagation delays | Low | High | Set user expectations, provide testing tools |

---

## Estimated Scope

**Overall**: Large

| Feature | Complexity | Effort |
|---------|------------|--------|
| Custom Domains | Large | 30% of phase |
| Team Collaboration | Large | 35% of phase |
| First Integrations | Medium | 20% of phase |
| PostgreSQL Migration | Medium | 15% of phase |

**Key Effort Drivers**:
1. SSL certificate automation complexity
2. Permission system thoroughness
3. Integration API variations
4. Migration risk mitigation

---

## Dependencies

### External
- Cloudflare (custom domains/SSL) or Let's Encrypt
- PostgreSQL provider (Neon, Supabase, Railway)
- Stripe Connect
- Email providers (Mailchimp, ConvertKit, Resend)

### Internal (from Phase 2)
- Payment system (for billing team plans)
- User authentication system
- Analytics infrastructure

---

## Definition of Done

Phase 3 is complete when:

1. ✅ All acceptance criteria pass
2. ✅ 100+ custom domains configured and serving
3. ✅ Team features tested with 5+ real teams
4. ✅ At least 2 integrations active with users
5. ✅ PostgreSQL migration complete with zero data loss
6. ✅ Performance benchmarks maintained or improved
7. ✅ Security audit passed (especially permissions)
8. ✅ Documentation updated
9. ✅ Operations team trained on new infrastructure
