# Delegation Audit Logging API

All endpoints below are prefixed with `/api/audit/delegation`.

## 1. Get Delegation Chain

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/{token_id}/chain` | Protected |

### Response
```jsonc
[
  {
    "delegation_id": "uuid",
    "token_id": "uuid",
    "principal_id": "user_uuid",
    "delegate_id": "agent_uuid",
    "action": "token_issued",
    "timestamp": "ISO-8601",
    "scopes": ["read:data", "write:tasks"],
    "metadata": {
      "task_id": "task-123",
      "task_description": "Analyze customer data"
    }
  },
  {
    "delegation_id": "uuid",
    "token_id": "uuid",
    "principal_id": "agent_uuid",
    "delegate_id": "agent_uuid2",
    "action": "token_issued",
    "timestamp": "ISO-8601",
    "scopes": ["read:data"],
    "metadata": {
      "task_id": "subtask-456",
      "task_description": "Extract customer insights"
    }
  }
]
```

## 2. Get User Delegation Activity

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/user/{user_id}` | Protected |

### Response
```jsonc
{
  "delegations_as_principal": [
    {
      "delegation_id": "uuid",
      "token_id": "uuid",
      "delegate_id": "agent_uuid",
      "action": "token_issued",
      "timestamp": "ISO-8601",
      "scopes": ["read:data", "write:tasks"],
      "metadata": {
        "task_id": "task-123",
        "task_description": "Analyze customer data"
      }
    }
  ],
  "delegations_received": [
    {
      "delegation_id": "uuid",
      "token_id": "uuid",
      "principal_id": "user_uuid2",
      "action": "token_issued",
      "timestamp": "ISO-8601",
      "scopes": ["read:tickets"],
      "metadata": {
        "task_id": "task-789",
        "task_description": "Review support tickets"
      }
    }
  ]
}
```

## 3. Get Delegation Statistics

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/stats` | Protected |

### Response
```jsonc
{
  "total_delegations": 1250,
  "active_delegated_tokens": 423,
  "revoked_delegated_tokens": 827,
  "top_delegators": [
    {
      "user_id": "user-123",
      "delegation_count": 87
    },
    {
      "user_id": "user-456",
      "delegation_count": 65
    }
  ],
  "top_delegates": [
    {
      "agent_id": "agent-789",
      "delegation_count": 112
    },
    {
      "agent_id": "agent-012",
      "delegation_count": 98
    }
  ]
}
```

## Notes
- Comprehensive logging of all token delegations
- Tracks delegations made by and received by users
- Provides detailed audit trail for compliance and security
- Delegation chain shows the complete path of token delegation
- Statistics provide insights into delegation patterns and usage
