from __future__ import annotations

import base64
import hashlib
import html
import json
import logging
import os
import secrets
import threading
import time
import urllib.parse
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable

import httpx
import jwt
import keyring
from jwt import PyJWKClient

from .db import db, json_load, now

log = logging.getLogger("viet-font-tool.providers")

ProviderId = str
CHATGPT = "chatgpt"
OLLAMA = "ollama_cloud"
APP_NAME = "Viet Font Studio"
OPENAI_ISSUER = "https://auth.openai.com"
OPENAI_AUTHORIZATION_ENDPOINT = "https://auth.openai.com/api/accounts/authorize"
OPENAI_TOKEN_ENDPOINT = "https://auth.openai.com/api/accounts/oauth/token"
OPENAI_API = "https://api.openai.com/v1"
OLLAMA_API = "https://ollama.com"
SECRET_SERVICE = "VietFontStudio"
PLAN_SCOPE = "chatgpt.tokens.use.direct"
OAUTH_SCOPES = "openid profile email offline_access resource.invoke chatgpt.tokens.use.direct"
RESOURCE = "https://api.openai.com/v1"
CALLBACK_PATH = "/auth/callback"
CALLBACK_TIMEOUT_SECONDS = 600
MODEL_CACHE_SECONDS = 60


class ProviderError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass
class OAuthTransaction:
    state: str
    nonce: str
    verifier: str
    redirect_uri: str
    frontend_origin: str
    host_id: str
    client_id: str
    is_registration: bool
    login_hint: str | None
    server: HTTPServer
    started_at: float
    callback_received: threading.Event


_oauth_lock = threading.RLock()
_token_refresh_lock = threading.Lock()
_oauth_pending: dict[str, OAuthTransaction] = {}
_model_cache_lock = threading.Lock()
_model_cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
_discovery_cache: dict[str, Any] | None = None


def _secure_keyring() -> None:
    try:
        backend = keyring.get_keyring()
        module = type(backend).__module__
        if backend.priority <= 0 or not module.startswith((
            "keyring.backends.Windows", "keyring.backends.macOS",
            "keyring.backends.SecretService", "keyring.backends.kwallet",
            "keyring.backends.libsecret",
        )):
            raise ProviderError(
                "SECURE_CREDENTIAL_STORE_UNAVAILABLE",
                "No operating-system credential store is available. Provider keys were not saved.",
                503,
            )
    except ProviderError:
        raise
    except Exception as exc:
        raise ProviderError(
            "SECURE_CREDENTIAL_STORE_UNAVAILABLE",
            "The operating-system credential store could not be opened.",
            503,
        ) from exc


def _get_secret(name: str) -> str | None:
    _secure_keyring()
    try:
        return keyring.get_password(SECRET_SERVICE, name)
    except Exception as exc:
        raise ProviderError(
            "SECURE_CREDENTIAL_STORE_UNAVAILABLE",
            "The operating-system credential store could not read this connection.",
            503,
        ) from exc


def _set_secret(name: str, value: str) -> None:
    _secure_keyring()
    try:
        keyring.set_password(SECRET_SERVICE, name, value)
    except Exception as exc:
        raise ProviderError(
            "SECURE_CREDENTIAL_STORE_UNAVAILABLE",
            "The operating-system credential store could not save this connection.",
            503,
        ) from exc


def _delete_secret(name: str) -> None:
    _secure_keyring()
    try:
        keyring.delete_password(SECRET_SERVICE, name)
    except keyring.errors.PasswordDeleteError:
        pass
    except Exception as exc:
        raise ProviderError(
            "SECURE_CREDENTIAL_STORE_UNAVAILABLE",
            "The operating-system credential store could not remove this connection.",
            503,
        ) from exc


def _replace_secrets(values: dict[str, str]) -> None:
    previous = {name: _get_secret(name) for name in values}
    written: list[str] = []
    try:
        for name, value in values.items():
            _set_secret(name, value)
            written.append(name)
    except Exception:
        for name in reversed(written):
            try:
                if previous[name] is None:
                    _delete_secret(name)
                else:
                    _set_secret(name, str(previous[name]))
            except Exception:
                pass
        raise


def _connection(provider_id: str) -> dict[str, Any] | None:
    with db() as conn:
        row = conn.execute("SELECT * FROM ai_provider_connections WHERE provider_id=?", (provider_id,)).fetchone()
    return dict(row) if row else None


def _setting(key: str) -> str | None:
    with db() as conn:
        row = conn.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def _set_setting(key: str, value: str | None) -> None:
    with db() as conn:
        if value is None:
            conn.execute("DELETE FROM app_settings WHERE key=?", (key,))
        else:
            conn.execute(
                "INSERT INTO app_settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )


def _upsert_connection(
    provider_id: str,
    *,
    status: str,
    auth_mode: str,
    account_label: str | None = None,
    account_subject: str | None = None,
    client_id: str | None = None,
    scopes: list[str] | None = None,
    expires_at: float | None = None,
    error_code: str | None = None,
    selected_model_id: str | None = None,
) -> None:
    with db() as conn:
        conn.execute(
            "INSERT INTO ai_provider_connections(provider_id,status,auth_mode,account_label,account_subject,client_id,scopes_json,expires_at,error_code,selected_model_id,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(provider_id) DO UPDATE SET "
            "status=excluded.status,auth_mode=excluded.auth_mode,account_label=excluded.account_label,"
            "account_subject=excluded.account_subject,client_id=excluded.client_id,scopes_json=excluded.scopes_json,"
            "expires_at=excluded.expires_at,error_code=excluded.error_code,"
            "selected_model_id=COALESCE(excluded.selected_model_id,ai_provider_connections.selected_model_id),updated_at=excluded.updated_at",
            (
                provider_id, status, auth_mode, account_label, account_subject, client_id,
                json.dumps(scopes or []), expires_at, error_code, selected_model_id, now(),
            ),
        )


def _mark_connection_error(provider_id: str, code: str, auth_mode: str) -> None:
    current = _connection(provider_id) or {}
    _upsert_connection(
        provider_id, status="needs_reconnect", auth_mode=auth_mode,
        account_label=current.get("account_label"), account_subject=current.get("account_subject"),
        client_id=current.get("client_id"), scopes=json_load(current.get("scopes_json"), []),
        expires_at=current.get("expires_at"), error_code=code,
        selected_model_id=current.get("selected_model_id"),
    )


def get_providers_payload() -> dict[str, Any]:
    selected = _setting("selected_provider_id")
    providers = []
    for provider_id, auth_mode, label in (
        (CHATGPT, "chatgpt_plan_oauth", "ChatGPT"),
        (OLLAMA, "api_key", "Ollama Cloud"),
    ):
        row = _connection(provider_id) or {}
        status = row.get("status", "disconnected")
        error_code = row.get("error_code")
        secret_name = {
            CHATGPT: f"chatgpt.{row.get('client_id') or 'default'}.access_token",
            OLLAMA: "ollama_cloud.api_key",
        }[provider_id]
        if status == "connected":
            try:
                if not _get_secret(secret_name):
                    status, error_code = "needs_reconnect", "CREDENTIAL_MISSING"
            except ProviderError:
                status, error_code = "needs_reconnect", "SECURE_CREDENTIAL_STORE_UNAVAILABLE"
        if provider_id == CHATGPT and status == "connected":
            scopes = set(json_load(row.get("scopes_json"), []))
            if not {PLAN_SCOPE, "resource.invoke", "offline_access"}.issubset(scopes):
                status, error_code = "needs_reconnect", "CHATGPT_PLAN_SCOPE_MISSING"
            else:
                try:
                    if not _get_secret(f"chatgpt.{row.get('client_id')}.refresh_token"):
                        status, error_code = "needs_reconnect", "CHATGPT_REFRESH_TOKEN_MISSING"
                except ProviderError:
                    status, error_code = "needs_reconnect", "SECURE_CREDENTIAL_STORE_UNAVAILABLE"
        providers.append({
            "id": provider_id,
            "status": status,
            "accountLabel": row.get("account_label") or (label if status == "connected" else None),
            "selectedModelId": row.get("selected_model_id"),
            "authMode": row.get("auth_mode", auth_mode),
            "errorCode": error_code,
        })
    if selected not in {item["id"] for item in providers}:
        selected = None
    return {"selectedProviderId": selected, "providers": providers}


def _frontend_origin(origin: str | None) -> str:
    if not origin:
        return "http://127.0.0.1:8000"
    parts = urllib.parse.urlsplit(origin)
    if parts.scheme != "http" or parts.hostname not in {"127.0.0.1", "localhost"} or parts.username or parts.password or parts.path not in {"", "/"} or parts.query or parts.fragment:
        raise ProviderError("INVALID_FRONTEND_ORIGIN", "Sign in can only be started by the local application.", 400)
    return f"http://{parts.netloc}"


def _host_id() -> str:
    value = _setting("chatgpt_ext_agent_host_id")
    if value:
        return value
    value = f"urn:uuid:{uuid.uuid4()}"
    _set_setting("chatgpt_ext_agent_host_id", value)
    return value


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _openid_config() -> dict[str, Any]:
    global _discovery_cache
    if _discovery_cache:
        return _discovery_cache
    try:
        response = httpx.get(f"{OPENAI_ISSUER}/.well-known/openid-configuration", timeout=15)
        response.raise_for_status()
        value = response.json()
        if value.get("issuer") != OPENAI_ISSUER or not value.get("jwks_uri"):
            raise ValueError("Unexpected OpenID discovery metadata")
        _discovery_cache = value
        return value
    except Exception as exc:
        raise ProviderError("CHATGPT_DISCOVERY_FAILED", "Could not load ChatGPT sign-in metadata.", 502) from exc


def _callback_page(target_origin: str, ok: bool, error_code: str | None = None, state: str | None = None) -> bytes:
    message: dict[str, Any] = {"type": "vfk:provider-auth-complete", "providerId": CHATGPT, "ok": ok}
    if error_code:
        message["errorCode"] = error_code
    if state:
        message["state"] = state
    encoded = json.dumps(message, separators=(",", ":")).replace("</", "<\\/")
    origin_json = json.dumps(target_origin)
    title = "ChatGPT connected" if ok else "ChatGPT connection failed"
    detail = "You can return to Viet Font Studio." if ok else "Return to Viet Font Studio and try connecting again."
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>"
        + html.escape(title)
        + "</title><style>body{font:16px system-ui;background:#0b1220;color:#eef4ff;display:grid;min-height:90vh;place-items:center}main{max-width:32rem;padding:2rem;border:1px solid #243650;border-radius:1rem;background:#111d30}p{color:#aabbd0}</style></head><body><main><h1>"
        + html.escape(title)
        + "</h1><p>"
        + html.escape(detail)
        + "</p></main><script>history.replaceState(null,\"\",\"/auth/callback\");const message="
        + encoded
        + ";const target="
        + origin_json
        + ";if(window.opener&&!window.opener.closed){window.opener.postMessage(message,target);window.close();}</script></body></html>"
    ).encode("utf-8")


def start_chatgpt_connect(frontend_origin: str | None = None) -> dict[str, str]:
    origin = _frontend_origin(frontend_origin)
    existing = _connection(CHATGPT) or {}
    existing_client = existing.get("client_id")
    is_registration = not bool(existing_client)
    client_id = "dynamic_agent_client" if is_registration else str(existing_client)
    state = _b64url(secrets.token_bytes(32))
    nonce = _b64url(secrets.token_bytes(32))
    verifier = _b64url(secrets.token_bytes(48))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    callback_port = int(os.environ.get("VFK_OAUTH_CALLBACK_PORT", "0"))
    callback_bind_host = "0.0.0.0" if callback_port else "127.0.0.1"
    server = HTTPServer((callback_bind_host, callback_port), BaseHTTPRequestHandler)
    server.timeout = CALLBACK_TIMEOUT_SECONDS
    port = int(server.server_address[1])
    redirect_uri = f"http://127.0.0.1:{port}{CALLBACK_PATH}"
    txn = OAuthTransaction(
        state=state, nonce=nonce, verifier=verifier, redirect_uri=redirect_uri,
        frontend_origin=origin, host_id=_host_id(), client_id=client_id,
        is_registration=is_registration,
        # Keep the ID token inside the OS credential store; omit the optional id_token_hint
        # so no token is returned to the browser as part of the authorization URL.
        login_hint=existing.get("account_label"), server=server, started_at=time.monotonic(),
        callback_received=threading.Event(),
    )
    with _oauth_lock:
        expired = [key for key, value in _oauth_pending.items() if time.monotonic() - value.started_at > CALLBACK_TIMEOUT_SECONDS]
        for key in expired:
            stale = _oauth_pending.pop(key)
            stale.server.server_close()
        _oauth_pending[state] = txn

    handler = _make_callback_handler()
    server.RequestHandlerClass = handler

    def serve_once() -> None:
        try:
            deadline = time.monotonic() + CALLBACK_TIMEOUT_SECONDS
            while not txn.callback_received.is_set() and time.monotonic() < deadline:
                server.timeout = min(10.0, max(0.1, deadline - time.monotonic()))
                try:
                    server.handle_request()
                except OSError:
                    break
        finally:
            server.server_close()
            with _oauth_lock:
                _oauth_pending.pop(state, None)

    threading.Thread(target=serve_once, name="chatgpt-oauth-callback", daemon=True).start()
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": OAUTH_SCOPES,
        "resource": RESOURCE,
        "state": state,
        "nonce": nonce,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "ext_agent_host_id": txn.host_id,
    }
    if is_registration:
        params["agent_name_hint"] = APP_NAME
    else:
        if txn.login_hint:
            params["login_hint"] = txn.login_hint
    return {"authorizationUrl": OPENAI_AUTHORIZATION_ENDPOINT + "?" + urllib.parse.urlencode(params)}


def _exchange_code(txn: OAuthTransaction, code: str, issued_client_id: str) -> dict[str, Any]:
    try:
        response = httpx.post(
            OPENAI_TOKEN_ENDPOINT,
            data={
                "grant_type": "authorization_code", "client_id": issued_client_id,
                "code": code, "code_verifier": txn.verifier,
                "redirect_uri": txn.redirect_uri, "resource": RESOURCE,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise ProviderError("CHATGPT_TOKEN_EXCHANGE_FAILED", "ChatGPT sign-in could not be completed. Start a new sign-in attempt.", 502) from exc
    if not payload.get("access_token") or not payload.get("id_token"):
        raise ProviderError("CHATGPT_TOKEN_RESPONSE_INVALID", "ChatGPT returned an incomplete sign-in response.", 502)
    return payload


def _validate_id_token(id_token: str, client_id: str, nonce: str) -> dict[str, Any]:
    try:
        discovery = _openid_config()
        jwks = PyJWKClient(discovery["jwks_uri"], cache_jwk_set=True, lifespan=3600)
        signing_key = jwks.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=[signing_key.algorithm_name],
            audience=client_id,
            issuer=OPENAI_ISSUER,
            options={"require": ["exp", "iat", "sub", "nonce"]},
        )
        if not secrets.compare_digest(str(claims.get("nonce", "")), nonce):
            raise ValueError("Nonce mismatch")
        return claims
    except Exception as exc:
        raise ProviderError("CHATGPT_ID_TOKEN_INVALID", "ChatGPT identity validation failed.", 401) from exc


def _save_chatgpt_tokens(client_id: str, payload: dict[str, Any], claims: dict[str, Any], scopes: list[str], host_id: str) -> str:
    subject = str(claims.get("sub", ""))
    if not subject:
        raise ProviderError("CHATGPT_IDENTITY_MISSING", "ChatGPT did not return a valid account identity.", 401)
    existing = _connection(CHATGPT) or {}
    if existing.get("client_id") == client_id and existing.get("account_subject") and existing["account_subject"] != subject:
        raise ProviderError("CHATGPT_ACCOUNT_MISMATCH", "This sign-in returned a different ChatGPT account. Disconnect the saved account before switching.", 409)
    account_key = f"chatgpt.{client_id}"
    current_refresh = _get_secret(f"{account_key}.refresh_token")
    secrets_to_save = {
        f"{account_key}.access_token": str(payload["access_token"]),
        f"{account_key}.id_token": str(payload["id_token"]),
    }
    refresh = payload.get("refresh_token")
    if refresh:
        secrets_to_save[f"{account_key}.refresh_token"] = str(refresh)
    _replace_secrets(secrets_to_save)
    granted = bool({PLAN_SCOPE, "resource.invoke", "offline_access"}.issubset(set(scopes)))
    has_refresh = bool(payload.get("refresh_token") or current_refresh)
    granted = granted and has_refresh
    status = "connected" if granted else "needs_reconnect"
    expires_at = time.time() + max(0, int(payload.get("expires_in", 0)))
    account_label = str(claims.get("email") or claims.get("name") or "ChatGPT account")[:200]
    with db() as conn:
        conn.execute(
            "INSERT INTO ai_provider_connections(provider_id,status,auth_mode,account_label,account_subject,client_id,scopes_json,expires_at,error_code,selected_model_id,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(provider_id) DO UPDATE SET "
            "status=excluded.status,auth_mode=excluded.auth_mode,account_label=excluded.account_label,"
            "account_subject=excluded.account_subject,client_id=excluded.client_id,scopes_json=excluded.scopes_json,"
            "expires_at=excluded.expires_at,error_code=excluded.error_code,updated_at=excluded.updated_at",
            (
                CHATGPT, status, "chatgpt_plan_oauth", account_label, subject, client_id,
                json.dumps(scopes), expires_at,
                None if granted else ("CHATGPT_PLAN_SCOPE_MISSING" if PLAN_SCOPE not in scopes else "CHATGPT_REFRESH_TOKEN_MISSING"),
                existing.get("selected_model_id") if existing.get("client_id") in (None, client_id) else None, now(),
            ),
        )
        conn.execute(
            "INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            ("chatgpt_ext_agent_host_id", host_id),
        )
    return status


def _handle_callback(txn: OAuthTransaction, query: dict[str, list[str]]) -> tuple[bool, str | None]:
    returned_state = (query.get("state") or [""])[0]
    if not secrets.compare_digest(returned_state, txn.state):
        return False, "OAUTH_STATE_MISMATCH"
    oauth_error = (query.get("error") or [""])[0]
    if oauth_error:
        return False, "CHATGPT_ACCESS_DENIED" if oauth_error == "access_denied" else "CHATGPT_AUTHORIZATION_FAILED"
    code = (query.get("code") or [""])[0]
    if not code:
        return False, "CHATGPT_CODE_MISSING"
    callback_client_id = (query.get("client_id") or [""])[0]
    if txn.is_registration:
        if not callback_client_id or callback_client_id == "dynamic_agent_client":
            return False, "CHATGPT_REGISTRATION_INCOMPLETE"
        issued_client_id = callback_client_id
    else:
        if callback_client_id and callback_client_id != txn.client_id:
            return False, "CHATGPT_CLIENT_MISMATCH"
        issued_client_id = txn.client_id
    try:
        tokens = _exchange_code(txn, code, issued_client_id)
        claims = _validate_id_token(str(tokens["id_token"]), issued_client_id, txn.nonce)
        token_scopes = tokens.get("scope") or tokens.get("scopes") or (query.get("scope") or [""])[0]
        scopes = token_scopes.split() if isinstance(token_scopes, str) else [str(scope) for scope in token_scopes]
        status = _save_chatgpt_tokens(issued_client_id, tokens, claims, scopes, txn.host_id)
        return status == "connected", None if status == "connected" else "CHATGPT_PLAN_SCOPE_MISSING"
    except ProviderError as exc:
        return False, exc.code
    except Exception:
        log.exception("ChatGPT OAuth callback processing failed")
        return False, "CHATGPT_AUTHORIZATION_FAILED"


def _make_callback_handler() -> type[BaseHTTPRequestHandler]:
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_error(404)
                return
            query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            state = (query.get("state") or [""])[0]
            with _oauth_lock:
                txn = _oauth_pending.get(state)
            if not txn:
                body = _callback_page("http://127.0.0.1:8000", False, "OAUTH_STATE_INVALID")
                ok, error_code, target = False, "OAUTH_STATE_INVALID", None
            else:
                ok, error_code = _handle_callback(txn, query)
                body = _callback_page(txn.frontend_origin, ok, error_code, txn.state)
                target = txn.frontend_origin
            self.send_response(200 if target else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            if txn and state == txn.state:
                txn.callback_received.set()

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return CallbackHandler


def _request_provider_json(url: str, token: str, *, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=httpx.Timeout(90.0, connect=15.0), follow_redirects=False) as client:
            response = client.request(method, url, headers={"Authorization": f"Bearer {token}"}, json=body)
        if response.status_code in {401, 403}:
            raise ProviderError("PROVIDER_AUTH_REJECTED", "The provider rejected this connection. Reconnect the provider and try again.", 401)
        response.raise_for_status()
        return response.json()
    except ProviderError:
        raise
    except httpx.TimeoutException as exc:
        raise ProviderError("PROVIDER_TIMEOUT", "The provider did not respond in time.", 504) from exc
    except httpx.HTTPStatusError as exc:
        raise ProviderError("PROVIDER_REQUEST_FAILED", "The provider could not complete the request.", 502) from exc
    except Exception as exc:
        raise ProviderError("PROVIDER_UNAVAILABLE", "Could not reach the selected provider.", 502) from exc


def _refresh_chatgpt_token(row: dict[str, Any]) -> str:
    # Refresh tokens may rotate. Serialize refreshes so model listing and a worker
    # request cannot race with the same saved refresh token.
    with _token_refresh_lock:
        return _refresh_chatgpt_token_locked(_connection(CHATGPT) or row)


def _refresh_chatgpt_token_locked(row: dict[str, Any]) -> str:
    client_id = str(row.get("client_id") or "")
    account_key = f"chatgpt.{client_id}"
    access_token = _get_secret(f"{account_key}.access_token")
    refresh_token = _get_secret(f"{account_key}.refresh_token")
    scopes = json_load(row.get("scopes_json"), [])
    if not client_id or not {PLAN_SCOPE, "resource.invoke", "offline_access"}.issubset(set(scopes)):
        raise ProviderError("CHATGPT_RECONNECT_REQUIRED", "Reconnect ChatGPT and grant permission to use your plan.", 401)
    if access_token and float(row.get("expires_at") or 0) > time.time() + 90:
        return access_token
    if not refresh_token:
        _mark_connection_error(CHATGPT, "CHATGPT_RECONNECT_REQUIRED", "chatgpt_plan_oauth")
        raise ProviderError("CHATGPT_RECONNECT_REQUIRED", "Reconnect ChatGPT to continue using its plan.", 401)
    try:
        response = httpx.post(
            OPENAI_TOKEN_ENDPOINT,
            data={"grant_type": "refresh_token", "client_id": client_id, "refresh_token": refresh_token, "resource": RESOURCE},
            timeout=30,
        )
        if response.status_code in {400, 401}:
            _mark_connection_error(CHATGPT, "CHATGPT_RECONNECT_REQUIRED", "chatgpt_plan_oauth")
            raise ProviderError("CHATGPT_RECONNECT_REQUIRED", "Reconnect ChatGPT to continue using its plan.", 401)
        response.raise_for_status()
        tokens = response.json()
        if not tokens.get("access_token"):
            raise ValueError("Missing access token")
        next_scopes_raw = tokens.get("scope") or tokens.get("scopes") or scopes
        next_scopes = next_scopes_raw.split() if isinstance(next_scopes_raw, str) else list(next_scopes_raw)
        if not {PLAN_SCOPE, "resource.invoke", "offline_access"}.issubset(set(next_scopes)):
            _mark_connection_error(CHATGPT, "CHATGPT_PLAN_SCOPE_MISSING", "chatgpt_plan_oauth")
            raise ProviderError("CHATGPT_PLAN_SCOPE_MISSING", "ChatGPT plan permission is no longer available. Reconnect ChatGPT.", 401)
        secrets_to_save = {f"{account_key}.access_token": str(tokens["access_token"])}
        if tokens.get("refresh_token"):
            secrets_to_save[f"{account_key}.refresh_token"] = str(tokens["refresh_token"])
        _replace_secrets(secrets_to_save)
        expires_at = time.time() + max(0, int(tokens.get("expires_in", 3600)))
        with db() as conn:
            conn.execute(
                "UPDATE ai_provider_connections SET status='connected',scopes_json=?,expires_at=?,error_code=NULL,updated_at=? WHERE provider_id=?",
                (json.dumps(next_scopes), expires_at, now(), CHATGPT),
            )
        return str(tokens["access_token"])
    except ProviderError:
        raise
    except Exception as exc:
        raise ProviderError("CHATGPT_REFRESH_FAILED", "ChatGPT authorization could not be refreshed. Reconnect and try again.", 401) from exc


def _chatgpt_models() -> list[dict[str, str]]:
    row = _connection(CHATGPT)
    if not row or row.get("status") not in {"connected", "needs_reconnect"}:
        raise ProviderError("PROVIDER_NOT_CONNECTED", "Connect ChatGPT before loading its models.", 409)
    token = _refresh_chatgpt_token(row)
    try:
        payload = _request_provider_json(f"{OPENAI_API}/models", token)
    except ProviderError as exc:
        if exc.code == "PROVIDER_AUTH_REJECTED":
            _mark_connection_error(CHATGPT, "CHATGPT_RECONNECT_REQUIRED", "chatgpt_plan_oauth")
            raise ProviderError("CHATGPT_RECONNECT_REQUIRED", "Reconnect ChatGPT to continue using its plan.", 401) from exc
        raise
    raw_models = payload.get("models", [])
    if not isinstance(raw_models, list):
        raise ProviderError("MODEL_CATALOG_INVALID", "ChatGPT returned an invalid model list.", 502)
    models = [
        {"id": str(model.get("slug")), "displayName": str(model.get("display_name") or model.get("slug"))}
        for model in raw_models
        if isinstance(model, dict) and model.get("visibility") == "list" and model.get("slug")
    ]
    return models


def _ollama_models(token: str) -> list[dict[str, str]]:
    payload = _request_provider_json(f"{OLLAMA_API}/v1/models", token)
    raw_models = payload.get("data", [])
    if not isinstance(raw_models, list):
        raise ProviderError("MODEL_CATALOG_INVALID", "Ollama Cloud returned an invalid model list.", 502)
    return [
        {"id": str(model["id"]), "displayName": str(model["id"])}
        for model in raw_models if isinstance(model, dict) and model.get("id")
    ]


def _cached_models(provider_id: str) -> list[dict[str, str]] | None:
    with _model_cache_lock:
        cached = _model_cache.get(provider_id)
        if cached and time.monotonic() - cached[0] < MODEL_CACHE_SECONDS:
            return [dict(item) for item in cached[1]]
    return None


def _cache_models(provider_id: str, models: list[dict[str, str]]) -> list[dict[str, str]]:
    with _model_cache_lock:
        _model_cache[provider_id] = (time.monotonic(), [dict(item) for item in models])
    return models


def list_provider_models(provider_id: str) -> list[dict[str, str]]:
    if provider_id not in {CHATGPT, OLLAMA}:
        raise ProviderError("UNKNOWN_PROVIDER", "Unknown AI provider.", 404)
    cached = _cached_models(provider_id)
    if cached is not None:
        return cached
    if provider_id == CHATGPT:
        return _cache_models(provider_id, _chatgpt_models())
    token = _get_secret("ollama_cloud.api_key")
    if not token:
        raise ProviderError("PROVIDER_NOT_CONNECTED", "Connect Ollama Cloud before loading its models.", 409)
    try:
        return _cache_models(provider_id, _ollama_models(token))
    except ProviderError as exc:
        if exc.code == "PROVIDER_AUTH_REJECTED":
            _mark_connection_error(OLLAMA, "OLLAMA_API_KEY_REJECTED", "api_key")
        raise


def connect_ollama_cloud(api_key: str) -> dict[str, Any]:
    value = api_key.strip()
    if len(value) < 8 or len(value) > 4096:
        raise ProviderError("INVALID_API_KEY", "Enter a valid Ollama Cloud API key.", 422)
    models = _ollama_models(value)
    if not models:
        raise ProviderError("NO_OLLAMA_MODELS", "Ollama Cloud returned no models for this connection.", 422)
    _set_secret("ollama_cloud.api_key", value)
    existing = _connection(OLLAMA) or {}
    _upsert_connection(
        OLLAMA, status="connected", auth_mode="api_key", account_label="Ollama Cloud",
        error_code=None, selected_model_id=existing.get("selected_model_id"),
    )
    if existing.get("selected_model_id") not in {model["id"] for model in models}:
        with db() as conn:
            conn.execute("UPDATE ai_provider_connections SET selected_model_id=NULL WHERE provider_id=?", (OLLAMA,))
    _cache_models(OLLAMA, models)
    return _provider_status(OLLAMA)


def _provider_status(provider_id: str) -> dict[str, Any]:
    payload = get_providers_payload()
    return next(provider for provider in payload["providers"] if provider["id"] == provider_id)


def select_provider(provider_id: str) -> dict[str, Any]:
    if provider_id not in {CHATGPT, OLLAMA}:
        raise ProviderError("UNKNOWN_PROVIDER", "Unknown AI provider.", 404)
    status = _provider_status(provider_id)
    if status["status"] != "connected":
        raise ProviderError("PROVIDER_NOT_CONNECTED", "Connect this provider before selecting it.", 409)
    _set_setting("selected_provider_id", provider_id)
    return get_providers_payload()


def select_model(provider_id: str, model_id: str) -> dict[str, Any]:
    if provider_id not in {CHATGPT, OLLAMA}:
        raise ProviderError("UNKNOWN_PROVIDER", "Unknown AI provider.", 404)
    value = model_id.strip()
    if not value or len(value) > 200 or any(ord(char) < 32 for char in value):
        raise ProviderError("INVALID_MODEL_ID", "Select a model from this provider's model list.", 422)
    models = list_provider_models(provider_id)
    if value not in {model["id"] for model in models}:
        raise ProviderError("MODEL_NOT_AVAILABLE", "This model is not available to the connected account. Reload the model list.", 422)
    with db() as conn:
        conn.execute(
            "UPDATE ai_provider_connections SET selected_model_id=?,updated_at=? WHERE provider_id=?",
            (value, now(), provider_id),
        )
    return _provider_status(provider_id)


def disconnect_provider(provider_id: str) -> dict[str, Any]:
    if provider_id not in {CHATGPT, OLLAMA}:
        raise ProviderError("UNKNOWN_PROVIDER", "Unknown AI provider.", 404)
    row = _connection(provider_id)
    secret_names: list[str]
    if provider_id == CHATGPT:
        client_id = (row or {}).get("client_id")
        secret_names = [f"chatgpt.{client_id}.{name}" for name in ("access_token", "refresh_token", "id_token")] if client_id else []
        if client_id:
            try:
                refresh_token = _get_secret(f"chatgpt.{client_id}.refresh_token")
                discovery = _openid_config()
                revoke = discovery.get("revocation_endpoint")
                if refresh_token and revoke:
                    httpx.post(
                        revoke, data={"client_id": client_id, "token": refresh_token, "token_type_hint": "refresh_token"}, timeout=10,
                    )
            except Exception:
                # Local credentials are still removed even when the provider is unreachable.
                pass
    else:
        secret_names = ["ollama_cloud.api_key"]
    for name in secret_names:
        _delete_secret(name)
    with db() as conn:
        conn.execute("DELETE FROM ai_provider_connections WHERE provider_id=?", (provider_id,))
        selected = conn.execute("SELECT value FROM app_settings WHERE key='selected_provider_id'").fetchone()
        if selected and selected["value"] == provider_id:
            conn.execute("DELETE FROM app_settings WHERE key='selected_provider_id'")
    with _model_cache_lock:
        _model_cache.pop(provider_id, None)
    return {"id": provider_id, "status": "disconnected", "authMode": "chatgpt_plan_oauth" if provider_id == CHATGPT else "api_key", "selectedModelId": None, "accountLabel": None, "errorCode": None}


def get_selected_provider_config() -> tuple[str, str, str] | None:
    provider_id = _setting("selected_provider_id")
    if provider_id not in {CHATGPT, OLLAMA}:
        return None
    status = _provider_status(provider_id)
    if status["status"] != "connected":
        raise ProviderError("PROVIDER_NOT_CONNECTED", "The selected AI provider is no longer connected. Reconnect it or choose another provider.", 409)
    model_id = status.get("selectedModelId")
    if not model_id:
        raise ProviderError("MODEL_NOT_SELECTED", "Choose a model for the selected AI provider before generating VER options.", 409)
    return provider_id, str(model_id), str(status["accountLabel"] or provider_id)


def generate_json(provider_id: str, model_id: str, instructions: str, input_data: dict[str, Any]) -> dict[str, Any]:
    prompt = json.dumps(input_data, ensure_ascii=False, separators=(",", ":"))
    if provider_id == CHATGPT:
        row = _connection(CHATGPT) or {}
        token = _refresh_chatgpt_token(row)
        body = {
            "model": model_id,
            "instructions": instructions,
            "input": [{"role": "user", "content": prompt}],
            "store": False,
            "stream": True,
        }
        text = _chatgpt_stream(token, body)
    elif provider_id == OLLAMA:
        token = _get_secret("ollama_cloud.api_key")
        if not token:
            raise ProviderError("PROVIDER_NOT_CONNECTED", "Ollama Cloud is not connected.", 409)
        try:
            payload = _request_provider_json(
                f"{OLLAMA_API}/api/chat", token, method="POST",
                body={
                    "model": model_id,
                    "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": prompt}],
                    "format": "json", "stream": False,
                    "options": {"temperature": 0.2},
                },
            )
        except ProviderError as exc:
            if exc.code == "PROVIDER_AUTH_REJECTED":
                _mark_connection_error(OLLAMA, "OLLAMA_API_KEY_REJECTED", "api_key")
            raise
        message = payload.get("message") or {}
        text = str(message.get("content") or "")
    else:
        raise ProviderError("UNKNOWN_PROVIDER", "Unknown AI provider.", 404)
    try:
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("JSON root must be an object")
        return value
    except Exception as exc:
        raise ProviderError("AI_RESPONSE_INVALID", "The selected model did not return valid structured JSON. Try again or choose another model.", 502) from exc


def _chatgpt_stream(token: str, body: dict[str, Any]) -> str:
    chunks: list[str] = []
    completed = False
    failed_code: str | None = None
    try:
        with httpx.stream(
            "POST", f"{OPENAI_API}/responses", headers={"Authorization": f"Bearer {token}"},
            json=body, timeout=httpx.Timeout(180.0, connect=20.0),
        ) as response:
            if response.status_code in {401, 403}:
                _mark_connection_error(CHATGPT, "CHATGPT_RECONNECT_REQUIRED", "chatgpt_plan_oauth")
                raise ProviderError("CHATGPT_RECONNECT_REQUIRED", "ChatGPT rejected this connection. Reconnect and try again.", 401)
            if response.status_code == 429:
                raise ProviderError("CHATGPT_USAGE_LIMIT", "ChatGPT plan usage is currently unavailable or at its limit.", 429)
            response.raise_for_status()
            event_data: list[str] = []
            for line in response.iter_lines():
                if not line:
                    if event_data:
                        event = _parse_sse_event("\n".join(event_data))
                        event_data.clear()
                        event_type = event.get("type")
                        if event_type == "response.output_text.delta":
                            chunks.append(str(event.get("delta", "")))
                        elif event_type == "response.failed":
                            error = (event.get("response") or {}).get("error") or {}
                            failed_code = str(error.get("code") or "CHATGPT_RESPONSE_FAILED")
                        elif event_type == "response.incomplete":
                            failed_code = "CHATGPT_RESPONSE_INCOMPLETE"
                        elif event_type == "response.completed":
                            completed = True
                    continue
                if line.startswith("data:"):
                    event_data.append(line[5:].lstrip())
            if event_data:
                event = _parse_sse_event("\n".join(event_data))
                if event.get("type") == "response.completed":
                    completed = True
                elif event.get("type") in {"response.failed", "response.incomplete"}:
                    failed_code = str(event.get("type"))
                elif event.get("type") == "response.output_text.delta":
                    chunks.append(str(event.get("delta", "")))
    except ProviderError:
        raise
    except httpx.TimeoutException as exc:
        raise ProviderError("PROVIDER_TIMEOUT", "ChatGPT did not respond in time.", 504) from exc
    except httpx.HTTPStatusError as exc:
        raise ProviderError("CHATGPT_REQUEST_FAILED", "ChatGPT could not complete this request.", 502) from exc
    except Exception as exc:
        raise ProviderError("CHATGPT_STREAM_FAILED", "ChatGPT response stream ended unexpectedly.", 502) from exc
    if failed_code:
        if "usage_limit" in failed_code or "usage_unavailable" in failed_code:
            raise ProviderError("CHATGPT_USAGE_LIMIT", "ChatGPT plan usage is currently unavailable or at its limit.", 429)
        raise ProviderError("CHATGPT_RESPONSE_FAILED", "ChatGPT could not complete this response.", 502)
    if not completed:
        raise ProviderError("CHATGPT_STREAM_INCOMPLETE", "ChatGPT response ended before completion. Retry the request.", 502)
    output = "".join(chunks).strip()
    if not output:
        raise ProviderError("AI_RESPONSE_EMPTY", "The selected model returned an empty response.", 502)
    return output


def _parse_sse_event(value: str) -> dict[str, Any]:
    data = value.strip()
    if data == "[DONE]":
        return {"type": "done"}
    try:
        parsed = json.loads(data)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
