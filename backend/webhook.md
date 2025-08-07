# Webhook System Documentation

## Overview

The Sonicus webhook system automatically triggers HTTP notifications when organizations are created in the platform. This enables real-time integration with external systems, CRM platforms, billing systems, or any service that needs to be notified of new organization events.

## Architecture

### Components

1. **WebhookService** (`app/services/webhook_service.py`)
   - Core webhook delivery service
   - Database-backed webhook endpoint management
   - Delivery tracking and retry mechanisms
   - Webhook signature verification support

2. **Database Models**
   - `WebhookEndpoint` - Stores webhook endpoint configurations
   - `WebhookDelivery` - Tracks webhook delivery attempts and status

3. **Organization Creation Endpoints** (Enhanced with webhook triggers)
   - `app/routers/organization_management.py` - Admin-level organization creation
   - `app/routers/super_admin.py` - Platform-level organization management
   - `app/routers/organization_crud.py` - Full onboarding workflow

4. **Webhook Management API** (`app/routers/webhook_management.py`)
   - Endpoint registration and management
   - Testing and validation capabilities
   - Super admin authentication required

## Configuration

### Database Setup

The webhook system uses two database tables in the `sonicus` schema:

1. **webhook_endpoints** - Stores webhook endpoint configurations
2. **webhook_deliveries** - Tracks delivery attempts and results

These tables are automatically created when you run the application for the first time.

### Webhook Endpoint Registration

Register webhook endpoints using the API:

```bash
curl -X POST "http://127.0.0.1:18100/api/v1/webhooks/endpoints" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPER_ADMIN_TOKEN" \
  -d '{
    "url": "https://your-webhook-endpoint.com/webhook",
    "events": ["organization.created"],
    "name": "Primary CRM Integration",
    "description": "Sends organization data to our CRM system",
    "timeout_seconds": 10,
    "max_retries": 3
  }'
```

## Webhook Payload

### Organization Created Event

When an organization is created, webhooks receive a POST request with the following JSON payload:

```json
{
  "event_type": "organization.created",
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-08-07T16:20:52.123456Z",
  "data": {
    "organization": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Example Corporation",
      "display_name": "Example Corporation Inc.",
      "domain": "example.com",
      "primary_contact_email": "admin@example.com",
      "subscription_tier": "premium",
      "subscription_status": "active",
      "max_users": 250,
      "industry": "Technology",
      "company_size": "50-100",
      "created_at": "2025-08-07T16:20:52.123456Z",
      "trial_end_date": null
    }
  }
}
```

### HTTP Headers

Webhooks are sent with the following headers:
- `Content-Type: application/json`
- `User-Agent: Sonicus-Webhooks/1.0`
- `X-Sonicus-Event: organization.created`
- `X-Sonicus-Event-ID: 550e8400-e29b-41d4-a716-446655440000`
- `X-Sonicus-Timestamp: 2025-08-07T16:20:52.123456Z`
- `X-Sonicus-Signature: sha256=...` (if secret key configured)

## API Endpoints

### Webhook Management Endpoints

All webhook management endpoints require super admin authentication and are available under `/api/v1/webhooks/`:

#### 1. Create Webhook Endpoint
```http
POST /api/v1/webhooks/endpoints
```

**Request Body:**
```json
{
  "url": "https://your-webhook.com/hook",
  "events": ["organization.created"],
  "name": "CRM Integration",
  "description": "Sends organization data to CRM",
  "organization_id": null,
  "secret_key": "optional-secret-for-signatures",
  "timeout_seconds": 10,
  "max_retries": 3
}
```

**Response:**
```json
{
  "id": "webhook-endpoint-id",
  "url": "https://your-webhook.com/hook",
  "message": "Webhook endpoint created successfully"
}
```

#### 2. Test Webhook Endpoint
```http
POST /api/v1/webhooks/test
```

**Request Body:**
```json
{
  "url": "https://your-test-webhook.com/hook",
  "test_data": {
    "custom": "test data"
  }
}
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "response_time_ms": 145.2,
  "error_message": null
}
```

#### 3. Trigger Test Webhook
```http
POST /api/v1/webhooks/trigger-test
```

Sends a test organization creation webhook to all registered endpoints.

**Response:**
```json
{
  "message": "Test webhook triggered successfully",
  "test_organization_id": "test-org-12345"
}
```

## Integration Points

### Organization Creation Triggers

Webhooks are automatically triggered when organizations are created through any of these endpoints:

1. **Admin Organization Creation**
   - Endpoint: `POST /api/v1/organizations/`
   - File: `app/routers/organization_management.py`
   - Trigger: Background task after successful creation

2. **Super Admin Platform Management**
   - Endpoint: `POST /api/v1/super-admin/organizations/`
   - File: `app/routers/super_admin.py`
   - Trigger: Async task for fire-and-forget execution

3. **Full Organization Onboarding**
   - Endpoint: `POST /api/v1/organization-crud/organizations/`
   - File: `app/routers/organization_crud.py`
   - Trigger: Background task with comprehensive data

## Error Handling

### Webhook Delivery Failures

The webhook system is designed to be resilient:

1. **Non-blocking**: Webhook failures do not prevent organization creation
2. **Parallel Delivery**: Multiple webhooks are sent concurrently
3. **Timeout Protection**: 30-second timeout per webhook request
4. **Error Logging**: All webhook failures are logged for monitoring

### Error Response Format

When webhook delivery fails, the system logs errors but continues processing:

```python
logger.error(f"Webhook delivery failed to {url}: {error_message}")
```

### Retry Logic

Currently, the system does not implement automatic retries. Consider implementing this for production use:
- Exponential backoff retry strategy
- Dead letter queue for failed webhooks
- Webhook delivery status tracking

## Testing

### Using Swagger UI

1. Access the API documentation: `http://127.0.0.1:18100/docs`
2. Navigate to the "webhooks" section
3. Use the test endpoints to validate webhook configuration
4. Test with services like webhook.site or ngrok for development

### Testing with webhook.site

1. Go to https://webhook.site and get a unique URL
2. Set the environment variable:
   ```bash
   WEBHOOK_URL=https://webhook.site/your-unique-id
   ```
3. Create an organization and check webhook.site for the payload

### Local Testing with ngrok

1. Install ngrok and expose your local webhook handler:
   ```bash
   ngrok http 3001  # If your webhook handler runs on port 3001
   ```
2. Use the ngrok URL as your webhook endpoint
3. Create organizations to test webhook delivery

## Production Considerations

### Security

1. **HTTPS Only**: All webhook URLs must use HTTPS in production
2. **Signature Verification**: Use secret keys to verify webhook authenticity
3. **Authentication**: Super admin authentication required for webhook management
4. **IP Whitelisting**: Consider restricting webhook sources by IP if needed

### Database Management

1. **Delivery Tracking**: All webhook attempts are logged in the database
2. **Retention Policy**: Consider implementing cleanup of old delivery records
3. **Monitoring**: Monitor webhook_deliveries table for failed deliveries
4. **Indexing**: Database indexes are created for optimal performance

### Scalability

1. **Async Processing**: Webhooks are sent asynchronously to prevent blocking
2. **Parallel Delivery**: Multiple webhooks are sent concurrently
3. **Retry Logic**: Built-in retry mechanism with configurable attempts
4. **Circuit Breaker**: Consider implementing for consistently failing endpoints

## Code Examples

### Custom Webhook Handler (Example)

```python
# Example webhook handler in Flask/FastAPI
from fastapi import FastAPI, Request
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/webhook/organization-created")
async def handle_organization_webhook(request: Request):
    try:
        payload = await request.json()
        
        if payload.get("event") == "organization_created":
            org_id = payload.get("organization_id")
            org_name = payload.get("organization_name")
            
            # Process the organization creation event
            await process_new_organization(org_id, org_name, payload.get("data"))
            
            return {"status": "success", "message": "Organization webhook processed"}
        
        return {"status": "ignored", "message": "Unknown event type"}
    
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return {"status": "error", "message": str(e)}

async def process_new_organization(org_id: int, org_name: str, org_data: dict):
    """Process the new organization data"""
    # Add to CRM system
    # Send welcome emails
    # Initialize billing
    # etc.
    pass
```

### Environment Configuration Example

```bash
# No environment variables needed - webhooks are managed via API
# All webhook endpoints are stored in the database
```

### Database Schema

**webhook_endpoints table:**
- `id` - UUID primary key
- `url` - Webhook endpoint URL  
- `secret_key` - Optional secret for signature verification
- `events` - JSON array of event types to send
- `is_active` - Enable/disable endpoint
- `organization_id` - Org-specific webhooks (NULL for global)
- `timeout_seconds` - Request timeout
- `max_retries` - Maximum retry attempts
- `name` - Human-readable name
- `description` - Description
- `created_at`, `updated_at` - Timestamps
- `last_success_at`, `last_failure_at` - Status tracking

**webhook_deliveries table:**
- `id` - UUID primary key
- `endpoint_id` - Reference to webhook_endpoints
- `event_type` - Type of event sent
- `event_id` - Unique identifier for the event
- `payload` - JSON payload sent
- `status` - pending, sent, failed, retrying
- `http_status_code` - Response status code
- `response_body`, `response_headers` - Response data
- `error_message` - Error details if failed
- `attempt_count`, `max_attempts` - Retry tracking
- `created_at`, `last_attempt_at`, `delivered_at` - Timestamps

## Troubleshooting

### Common Issues

1. **Webhooks Not Firing**
   - Check environment variables are set correctly
   - Verify webhook URLs are accessible
   - Check application logs for error messages

2. **Webhook Timeouts**
   - Ensure webhook endpoints respond within 30 seconds
   - Check network connectivity
   - Verify endpoint is not overloaded

3. **Invalid Payloads**
   - Verify webhook endpoint expects JSON
   - Check for payload parsing errors
   - Ensure proper Content-Type headers

### Debug Logging

Enable debug logging to troubleshoot webhook issues:

```python
import logging
logging.getLogger("app.services.simple_webhook_service").setLevel(logging.DEBUG)
```

### Testing Webhook Connectivity

```bash
# Test webhook endpoint manually
curl -X POST https://your-webhook.com/hook \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook connectivity"}'
```

## Changelog

### Version 2.0.0 (August 7, 2025)
- **BREAKING CHANGE**: Migrated from environment variable configuration to database-backed webhook management
- Added webhook endpoint registration via API
- Added delivery tracking and retry mechanisms  
- Added webhook signature verification support
- Added comprehensive webhook management endpoints
- Removed simple webhook service in favor of full-featured service
- Added database tables: webhook_endpoints, webhook_deliveries
- Enhanced error handling and logging
- Added organization-specific webhook filtering

### Version 1.0.0 (August 7, 2025)
- Initial webhook system implementation
- Organization creation event support
- Environment variable configuration
- Webhook management API endpoints
- Parallel webhook delivery
- Comprehensive error handling and logging

## Support

For webhook-related issues:
1. Check application logs in `/logs/` directory
2. Use the webhook management API endpoints for testing
3. Verify environment variable configuration
4. Test webhook endpoints independently

## Future Enhancements

Planned webhook system improvements:
- Webhook signature verification for security
- Retry mechanism with exponential backoff  
- Webhook delivery status tracking
- Additional organization events (updated, deleted)
- User creation/modification events
- Subscription change events
- Custom event filtering per webhook URL
