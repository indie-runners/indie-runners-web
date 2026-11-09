# W-105 — Google unreachable, or a userinfo error, on the sign-in callback is a raw 500

`priority: 4` · `effort: S` · `area: routing` · `deploy: batched`
`source: docs/DEV_NOTES.md 2026-11-03 (while on W-094)`

## What is wrong

W-094 caught Google refusing a code. Two other failures on the same
callback still escape as a 500, the plain "Internal Server Error" page:

1. `httpx.RequestError`, a timeout or no route to Google's token
   endpoint, raised from `exchange_code_for_token`.
2. `get_userinfo`'s `raise_for_status()`: a 4xx or 5xx from Google's
   userinfo endpoint after a good exchange.

Neither has been seen in production. Both are the shape W-094 fixed.

## Evidence

The developer's note:

> `httpx.RequestError` (timeout or no route to Google's token endpoint)
> still escapes `exchange_code_for_token` as a 500: W-094 handles
> Google's refusal, not Google's absence. `get_userinfo` keeps
> `raise_for_status()`, as the spec left it; a 4xx there after a good
> exchange is the same shape, never seen in the log.

```
app/services/auth_service.py:32   response = await client.post(GOOGLE_TOKEN_URL, data={
app/services/auth_service.py:55   response.raise_for_status()
app/main.py:1111                  userinfo = await svc.get_userinfo(token_data["access_token"])
```

## Acceptance

1. Both failures render the page a refused code renders today
   (`signin_failed.html`), not a 500. Status: the developer names it and
   why (W-094 used `400` for a refusal; Google being down is not the
   visitor's fault).
2. Each writes one stderr line naming which call failed and the error
   class or status, never the code or the token.
3. Shown once each, locally: point the token URL at a closed port, and
   force a userinfo error. Paste both responses.
4. A refused code still behaves as W-094 left it, signed in and out.

## Out of scope

- Retrying the call.
- `UserService`'s `ValueError` path (`main.py:1114`), already a 400.
- The log line's severity in Cloud Logging. That is W-051.
