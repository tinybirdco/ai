
# Tinybird Project

## Tinybird

### Overview
This project manages user token information for authentication and authorization purposes. It provides a secure way to store and retrieve user tokens across different channels.

### Data sources

#### user_tokens
This datasource stores user token information with a ReplacingMergeTree engine for deduplication based on user_id, channel_id, and updated_at. It's designed to maintain only the most recent token for each user-channel combination.

**Schema:**
- `user_id`: String - Unique identifier for the user
- `channel_id`: String - Identifier for the channel
- `token`: String - Authentication token
- `host`: String - Host where the token is valid
- `updated_at`: DateTime - Timestamp when the token was last updated

**Ingestion Example:**
```bash
curl -X POST "https://api.europe-west2.gcp.tinybird.co/v0/events?name=user_tokens" \
     -H "Authorization: Bearer $TB_ADMIN_TOKEN" \
     -d '{"user_id":"user123","channel_id":"channel456","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9","host":"example.com","updated_at":"2023-08-15 14:30:00"}'
```

### Endpoints

#### get_latest_user_token
This endpoint retrieves the most recent token and host for a specific user and channel combination. It returns only the latest record based on the updated_at timestamp.

**Parameters:**
- `user_id`: String - The user identifier to query for
- `channel_id`: String - The channel identifier to query for

**Usage Example:**
```bash
curl -X GET "https://api.europe-west2.gcp.tinybird.co/v0/pipes/get_latest_user_token.json?token=$TB_ADMIN_TOKEN&user_id=user123&channel_id=channel456"
```
