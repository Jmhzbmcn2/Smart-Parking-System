# NFR-04 inspection: encryption of personal data

NFR-04: 100% of personal data is encrypted, AES-256 at rest and TLS 1.2 or newer in transit. Verification method: Inspection (SRS section 4). Mitigates hazard HZ-04 (leak of plate data and parking history).

Date of inspection: 2026-10-17. Tool versions: Python 3.13, `cryptography` 50.0.2, curl 8.21.0 (Schannel).

## At rest: AES-256-SIV column type

`backend/app/core/crypto.py` defines `EncryptedString`, a SQLAlchemy column type. It encrypts with AES-256-SIV (`cryptography` `AESSIV`, 64-byte key = two 256-bit keys) and stores base64 text. SIV is deterministic, so equal values give equal ciphertext. This keeps equality lookups (active session by plate, duplicate entry, login by username) and the unique active-plate index working. The accepted leak is equality only: two rows with the same plate have the same ciphertext.

The key comes from the environment variable `SPMS_DATA_KEY` (base64, 64 bytes). If it is not set, the backend creates `backend/.data_key` on first start and reuses it. `.data_key` and `*.pem` are git-ignored.

### Checklist of personal data columns

| Table | Column | Encrypted | Evidence |
|---|---|---|---|
| `parking_sessions` | `plate` | Yes | `test_plate_not_stored_in_plaintext` |
| `gate_events` | `plate` | Yes | `test_plate_not_stored_in_plaintext` |
| `reservations` | `plate` | Yes | `test_plate_not_stored_in_plaintext` |
| `audit_log` | `plate` | Yes | `test_plate_not_stored_in_plaintext` |
| `users` | `username` | Yes | `test_username_encrypted_but_login_works` |
| `reservations`, `audit_log` | `username` | Yes | `test_username_copies_encrypted` |
| `prices` | `created_by` (admin username) | Yes | `test_username_copies_encrypted` |

Not encrypted, and why:

| Column | Reason |
|---|---|
| `users.password_hash` | Already a salted scrypt hash, not reversible. |
| `users.token` | Random opaque token, not personal data. It is cleared on logout. |
| Amounts, timestamps, slot IDs, gate IDs | Not personal data. |

Other checks:

- `test_database_file_does_not_contain_the_plate` writes a plate into a file database and reads the raw bytes of the `.db` file: the plate is not in it.
- `test_same_plate_same_ciphertext` and the duplicate-entry 409 test show deterministic lookup still works.
- `test_key_from_env_must_be_64_bytes` and `test_missing_key_is_created_once_and_reused` cover the key loading.

Existing databases hold plaintext rows. After pulling the encryption change, delete `backend/spms.db` (see the README).

## In transit: HTTPS and TLS version

`npm run dev:be:https` serves the API on `https://localhost:8443` with a self-signed certificate made by `uv run --directory backend python mocks/make_cert.py` (writes `backend/certs/key.pem` and `cert.pem`, git-ignored). Run the frontend against it with `SPMS_HTTPS=1` (Vite then proxies `/api` to the HTTPS backend with `secure: false`).

PowerShell:

```text
uv run --directory backend python mocks/make_cert.py
npm run dev:be:https
$env:SPMS_HTTPS = "1"
npm run dev:fe
```

Git Bash:

```text
uv run --directory backend python mocks/make_cert.py
npm run dev:be:https
SPMS_HTTPS=1 npm run dev:fe
```

Python's default server TLS context refuses protocols below TLS 1.2. Check, with the HTTPS server running:

```text
curl -k https://localhost:8443/api/health
curl -k --tlsv1.2 --tls-max 1.2 https://localhost:8443/api/health
curl -k --tlsv1.1 --tls-max 1.1 https://localhost:8443/api/health
```

Output of this run:

```text
curl -k (default)                  -> {"status":"ok"}
curl -k --tlsv1.2 --tls-max 1.2    -> {"status":"ok"}, exit 0
curl -k --tlsv1.1 --tls-max 1.1    -> no response, exit 35 (SSL connect error)
```

Cross-check with Python `ssl` (client restricted to one protocol range):

```text
client max TLS 1.1: refused (SSLEOFError: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol)
client max TLS 1.2: connected, negotiated TLSv1.2
client TLS 1.3    : connected, negotiated TLSv1.3
```

Result: TLS 1.1 is refused; TLS 1.2 and 1.3 are accepted. The Vite proxy to the HTTPS backend was also checked: `curl http://127.0.0.1:5175/api/health` through a Vite dev server started with `SPMS_HTTPS=1` returned `{"status":"ok"}`.

## Related controls (HZ-04)

- Role-based access (SP-4.3): a driver gets 403 on admin endpoints (TC-13).
- Logout invalidates the token on the server: `test_logout_invalidates_token`.
- Device endpoints (`/api/lpr-events`, `/api/sensor-events`, `/api/payments/{id}/mock`) need the `X-Device-Key` header: `test_device_key_required_401`. The default key `dev-device-key` is for the demo; set `SPMS_DEVICE_KEY` in any other setting.

## Limits

- The certificate is self-signed, so browsers and clients need `-k` or an exception. A real deployment needs a certificate from a trusted authority.
- The data key sits next to the database in `backend/.data_key` by default. For real use, keep it in a secret store and pass it as `SPMS_DATA_KEY`.
- Deterministic encryption reveals which rows share a value. This is accepted for the course scope.
