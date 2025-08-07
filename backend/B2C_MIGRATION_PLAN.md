# B2B2C to B2C Migration Plan

## Overview
Converting Sonicus from B2B2C (Business-to-Business-to-Consumer) to B2C (Business-to-Consumer) architecture.

## Phase 1: Database Schema Migration

### Tables to Remove (Organization-centric)
- `organizations` - Main organization table
- `organization_analytics` - Organization-level analytics
- `organization_metrics` - Organization metrics
- `organization_sound_packages` - Organization package assignments

### Tables to Modify (Remove organization_id dependencies)
- `users` - Remove organization_id, make users independent
- `subscriptions` - Move from organization to user level
- `user_sessions` - Remove organization_id
- `sound_packages` - Remove organization_id, make global
- `therapy_sounds` - Remove organization restrictions
- `wellness_metrics` - Convert to user-level metrics
- `dashboard_widgets` - Convert to user-level dashboards
- `webhook_endpoints` - Remove organization filtering
- All analytics and tracking tables

### New Tables to Create
- `user_subscriptions` - Individual user subscriptions
- `user_sound_packages` - Direct user-to-package assignments
- `user_preferences` - Individual user preferences
- `user_analytics` - User-level analytics

## Phase 2: Model Updates

### User Model Changes
- Remove organization_id foreign key
- Add subscription fields directly to user
- Add direct sound package relationships
- Simplify user roles (remove org admin concept)

### Subscription Model Changes
- Change from organization-level to user-level
- Direct user-to-subscription relationship
- Individual billing and payment tracking

### Sound Package Model Changes
- Remove organization restrictions
- Make packages globally available
- User-level package assignments

## Phase 3: API Endpoint Changes

### Remove Organization Endpoints
- `/api/v1/organizations/*` - All organization management
- `/api/v1/super-admin/organizations/*` - Organization admin endpoints
- `/api/v1/organization-crud/*` - Organization CRUD operations

### Modify User Endpoints
- Direct user registration (no org context)
- User subscription management
- Personal dashboard and analytics
- Individual sound package access

### New B2C Endpoints
- `/api/v1/user/subscription` - User subscription management
- `/api/v1/user/packages` - Personal sound packages
- `/api/v1/user/analytics` - Personal analytics
- `/api/v1/user/preferences` - User preferences

## Phase 4: Authentication & Authorization

### Simplify Auth Model
- Remove organization context from JWT tokens
- Simplify user roles (user, admin, super_admin)
- Remove organization admin concept
- Direct user-based permissions

### Update Auth Middleware
- Remove organization validation
- Simplify permission checks
- Update token generation/validation

## Phase 5: Frontend Changes

### Remove Organization Features
- Organization dashboard
- User management (org admin view)
- Organization settings
- Multi-tenant switching

### Simplify User Experience
- Direct user onboarding
- Personal subscription management
- Individual therapy sound access
- Personal analytics dashboard

## Phase 6: Webhook System Updates

### Webhook Event Changes
- Remove organization.* events
- Add user.* events (user.registered, user.subscribed, etc.)
- Simplify webhook payload structure

## Phase 7: Data Migration

### Migration Strategy
1. Export existing user data
2. Create new B2C schema
3. Migrate user accounts (flatten org structure)
4. Migrate subscriptions to user level
5. Migrate sound package assignments
6. Archive organization-specific data

### Data Preservation
- Keep audit trail of organization data
- Maintain user account continuity
- Preserve subscription history
- Backup all organization-level analytics

## Implementation Order

1. ✅ Create migration scripts for database schema
2. ✅ Update models (users, subscriptions, sound_packages)
3. ✅ Update authentication system
4. ✅ Modify API endpoints
5. ✅ Update webhook system
6. ✅ Frontend modifications
7. ✅ Data migration execution
8. ✅ Testing and validation

## Considerations

### Business Impact
- Existing organization customers need transition plan
- Billing model changes (org-level to user-level)
- Customer communication strategy
- Pricing model adjustments

### Technical Considerations
- Data migration complexity
- Downtime minimization
- Rollback strategy
- Performance impact analysis

### User Experience
- Simplified onboarding flow
- Direct subscription management
- Personal analytics and insights
- Individual sound therapy journey

## Next Steps

1. Confirm migration approach
2. Create database migration scripts
3. Begin model modifications
4. Update authentication system
5. Modify API endpoints systematically
