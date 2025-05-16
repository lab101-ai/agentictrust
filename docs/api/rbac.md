# Role-Based Access Control (RBAC) API

All endpoints below are prefixed with `/api/rbac`.

## 1. Create Role

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/roles` | Protected |

### Request Body (`CreateRoleRequest`)
```jsonc
{
  "name": "Support Agent",
  "description": "Customer support representative",
  "permissions": [
    "read:tickets",
    "update:ticket_status",
    "create:ticket_note"
  ]
}
```

### Response — `201 Created`
```jsonc
{
  "message": "Role created successfully",
  "role": {
    "role_id": "uuid",
    "name": "Support Agent",
    "description": "Customer support representative",
    "permissions": [
      "read:tickets",
      "update:ticket_status",
      "create:ticket_note"
    ],
    "is_active": true,
    "created_at": "ISO-8601"
  }
}
```

## 2. List Roles

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/roles` | Protected |

### Response
```jsonc
{
  "roles": [
    {
      "role_id": "uuid",
      "name": "Support Agent",
      "description": "Customer support representative",
      "permissions_count": 3,
      "is_active": true
    },
    {
      "role_id": "uuid",
      "name": "Support Manager",
      "description": "Customer support team manager",
      "permissions_count": 8,
      "is_active": true
    }
  ]
}
```

## 3. Get Role

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/roles/{role_id}` | Protected |

### Response
```jsonc
{
  "role_id": "uuid",
  "name": "Support Agent",
  "description": "Customer support representative",
  "permissions": [
    "read:tickets",
    "update:ticket_status",
    "create:ticket_note"
  ],
  "is_active": true,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

## 4. Update Role

|| Method | Path | Auth |
||--------|------|------|
|| `PUT` | `/roles/{role_id}` | Protected |

### Request Body
```jsonc
{
  "name": "Senior Support Agent",
  "description": "Senior customer support representative",
  "permissions": [
    "read:tickets",
    "update:ticket_status",
    "create:ticket_note",
    "delete:ticket_note"
  ],
  "is_active": true
}
```

### Response
```jsonc
{
  "message": "Role updated successfully",
  "role": {
    "role_id": "uuid",
    "name": "Senior Support Agent",
    "description": "Senior customer support representative",
    "permissions": [
      "read:tickets",
      "update:ticket_status",
      "create:ticket_note",
      "delete:ticket_note"
    ],
    "is_active": true,
    "updated_at": "ISO-8601"
  }
}
```

## 5. Delete Role

|| Method | Path | Auth |
||--------|------|------|
|| `DELETE` | `/roles/{role_id}` | Protected |

### Response — `200 OK`
```jsonc
{
  "message": "Role deleted successfully"
}
```

## 6. Assign Role to User/Agent

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/assign` | Protected |

### Request Body
```jsonc
{
  "user_id": "uuid",
  "role_id": "uuid",
  "scope": "company_uuid"
}
```

### Response
```jsonc
{
  "message": "Role assigned successfully",
  "assignment": {
    "assignment_id": "uuid",
    "user_id": "uuid",
    "role_id": "uuid",
    "scope": "company_uuid",
    "assigned_at": "ISO-8601"
  }
}
```

## 7. Revoke Role from User/Agent

|| Method | Path | Auth |
||--------|------|------|
|| `DELETE` | `/assignments/{assignment_id}` | Protected |

### Response — `200 OK`
```jsonc
{
  "message": "Role assignment revoked successfully"
}
```

## 8. List User/Agent Roles

|| Method | Path | Auth |
||--------|------|------|
|| `GET` | `/users/{user_id}/roles` | Protected |

### Response
```jsonc
{
  "roles": [
    {
      "assignment_id": "uuid",
      "role_id": "uuid",
      "role_name": "Support Agent",
      "scope": "company_uuid",
      "assigned_at": "ISO-8601"
    }
  ]
}
```

## 9. Check Permission

|| Method | Path | Auth |
||--------|------|------|
|| `POST` | `/check_permission` | Protected |

### Request Body
```jsonc
{
  "user_id": "uuid",
  "permission": "read:tickets",
  "resource_context": {
    "ticket_id": "uuid",
    "company_id": "uuid"
  }
}
```

### Response
```jsonc
{
  "allowed": true,
  "reason": "User has 'Support Agent' role with 'read:tickets' permission",
  "roles": ["Support Agent"]
}
```

## Notes
- Granular permission management
- Roles can be scoped to specific organizations
- Supports complex permission hierarchies
- Permissions can be checked against resource contexts
- Role assignments can be time-limited
