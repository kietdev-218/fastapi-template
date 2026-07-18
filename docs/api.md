# API Guidelines & Endpoints

This document describes the API versioning scheme, request-response handling, JWT authentication, and endpoints
reference.

---

## API Versioning & Structure

- **Base Path**: `/api/v1`
- **Interactive Docs**: Available at `/docs` (Swagger UI) only when `ENVIRONMENT=development`.
- **Validation**: Handled automatically using Pydantic v2 schemas in `app/schemas/`.
- **Error Envelope**: All exception handlers return a standard JSON envelope as defined in
  [API Response Standard](api-response-standard.md):
    ```json
    {
        "success": false,
        "code": 80400,
        "message": "Invalid data",
        "data": null,
        "meta": null,
        "errors": [{ "field": "email", "message": "Invalid email format" }],
        "timestamp": "2026-07-18T10:00:00Z",
        "traceId": "a1b2c3d4-uuid"
    }
    ```

---

## Zero Trust Authentication Flow (Ory Stack)

This service relies on a Zero Trust architecture using the Ory ecosystem (Kratos, Oathkeeper, Keto). It does not issue
its own authentication tokens to the client.

1. **Client Login**: The client authenticates against Ory Kratos and receives a session cookie.
2. **Access Proxy**: The client sends requests to Ory Oathkeeper (acting as the Identity & Access Proxy).
3. **Session Verification & Authorization**: Oathkeeper verifies the Kratos session, checks permissions via Keto, and
   uses the `id_token` mutator to generate a signed JWT.
4. **Backend Validation**: Oathkeeper forwards the request to this FastAPI service with the generated JWT in the header
   (`Authorization: Bearer <token>`). The FastAPI service cryptographically verifies this JWT using Oathkeeper's public
   JSON Web Key Set (JWKS).

---

## Endpoints Reference

| Method  | Path             | Auth | Description                               |
| ------- | ---------------- | ---- | ----------------------------------------- |
| **GET** | `/api/v1/health` | None | Health check & database connection probe. |

---

## Related Documentation

- [Development Guide](development.md)
- [Architecture Guide](architecture.md)
