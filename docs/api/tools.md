# Tools API

All endpoints below are prefixed with `/api/tools`.

---

## 1. Create Tool

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/` | Protected* |

### Request Body (`CreateToolRequest`)
```jsonc
{
  "name": "My Tool",
  "description": "Purpose of the tool",
  "category": "text-processing",
  "permissions_required": ["scope-uuid", "READ_DATA"],
  "input_schema": {
    "type": "object",
    "properties": { "text": { "type": "string" } },
    "required": ["text"]
  }
}
```

### Response — `201 Created`
```jsonc
{
  "message": "Tool created successfully",
  "tool": {
    "tool_id": "uuid",
    "name": "My Tool",
    "category": "text-processing",
    "permissions_required": ["scope-uuid"],
    "inputSchema": { /* same as input_schema */ },
    "is_active": true,
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  }
}
```

---

## 2. List Tools

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/` | Protected* |

Optional query params:
- `category`
- `is_active` (bool)

### Response
```jsonc
{ "tools": [ { /* tool */ }, … ] }
```

---

## 3. Get Tool by ID

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/{tool_id}` | Protected* |

Returns a single tool object (`inputSchema` alias provided).

---

## 4. Update Tool

| Method | Path | Auth |
|--------|------|------|
| `PUT` | `/{tool_id}` | Protected* |

Body matches `UpdateToolRequest` (all fields optional). Example:
```jsonc
{
  "description": "New description",
  "input_schema": { ... }
}
```

### Response
```jsonc
{
  "message": "Tool updated successfully",
  "tool": { /* updated tool */ }
}
```

---

## 5. Delete Tool

| Method | Path | Auth |
|--------|------|------|
| `DELETE` | `/{tool_id}` | Protected* |

If the tool is associated with agents, deletion is blocked.

---

## 6. Activate / Deactivate Tool

| Action | Method & Path |
|--------|---------------|
| Activate   | `POST /{tool_id}/activate` |
| Deactivate | `POST /{tool_id}/deactivate` |

---

### Notes
*Endpoints marked **Protected*** will require bearer tokens once auth is implemented.

`inputSchema` in responses is the alias for the `parameters` JSON field stored in the DB.
