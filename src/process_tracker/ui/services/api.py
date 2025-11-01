from __future__ import annotations
import os
import httpx
from typing import Any, Dict, Iterable, Optional


class ApiClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://127.0.0.1:8787/api/v1")
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[str] = None

    async def _ensure_client(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    def set_token(self, token: Optional[str]) -> None:
        self._token = token

    async def _req(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: Dict[str, Any] | None = None,
    ) -> Any:
        await self._ensure_client()
        assert self._client
        headers: Dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        r = await self._client.request(method.upper(), path, json=json_body, params=params, headers=headers)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        return r.json() if ct.startswith("application/json") else r.content

    # ---- Auth (dev) ----
    async def login_dev(self, email: str, roles: Iterable[str], perms: Iterable[str]):
        return await self._req(
            "POST", "/auth/login",
            json_body={"email": email, "roles": list(roles), "perms": list(perms)}
        )

    async def me(self):
        return await self._req("GET", "/auth/me")

    # ---- Users ----
    async def users_list(self):
        return await self._req("GET", "/users")

    async def users_create(self, payload: Dict[str, Any]):
        return await self._req("POST", "/users", json_body=payload)

    async def users_patch(self, user_id: int, patch: Dict[str, Any]):
        return await self._req("PATCH", f"/users/{user_id}", json_body=patch)

    async def users_delete(self, user_id: int):
        return await self._req("DELETE", f"/users/{user_id}")

    # ---- Templates ----
    async def templates_list(self, q: Optional[str] = None):
        return await self._req("GET", "/templates", params={"q": q} if q else None)

    async def templates_create(self, payload: Dict[str, Any]):
        return await self._req("POST", "/templates", json_body=payload)

    async def templates_patch(self, template_id: int, patch: Dict[str, Any]):
        return await self._req("PATCH", f"/templates/{template_id}", json_body=patch)

    async def templates_delete(self, template_id: int):
        return await self._req("DELETE", f"/templates/{template_id}")

    # ---- Webhooks ----
    async def webhooks_list(self):
        return await self._req("GET", "/webhooks")

    async def webhooks_create(self, payload: Dict[str, Any]):
        return await self._req("POST", "/webhooks", json_body=payload)

    async def webhooks_patch(self, hook_id: int, patch: Dict[str, Any]):
        return await self._req("PATCH", f"/webhooks/{hook_id}", json_body=patch)

    async def webhooks_delete(self, hook_id: int):
        return await self._req("DELETE", f"/webhooks/{hook_id}")

    async def webhooks_test(self, hook_id: int, event: str, payload: Dict[str, Any]):
        return await self._req("POST", f"/webhooks/{hook_id}/test", json_body={"event": event, "payload": payload})

    # ---- Views ----
    async def views_list(self, resource: Optional[str] = None):
        params = {"resource": resource} if resource else None
        return await self._req("GET", "/views", params=params)

    async def views_create(self, payload: Dict[str, Any]):
        return await self._req("POST", "/views", json_body=payload)

    async def views_patch(self, view_id: int, patch: Dict[str, Any]):
        return await self._req("PATCH", f"/views/{view_id}", json_body=patch)

    async def views_delete(self, view_id: int):
        return await self._req("DELETE", f"/views/{view_id}")

    # ---- Audit ----
    async def audit_list(
        self,
        entity: Optional[str] = None,
        entity_id: Optional[int] = None,
        event: Optional[str] = None,
        limit: int = 100,
    ):
        params: Dict[str, Any] = {"limit": limit}
        if entity:
            params["entity"] = entity
        if entity_id is not None:
            params["entity_id"] = entity_id
        if event:
            params["event"] = event
        return await self._req("GET", "/audit", params=params)

    async def audit_add(self, payload: Dict[str, Any]):
        return await self._req("POST", "/audit", json_body=payload)

    # ---- Files ----
    async def files_upload(self, files: list[tuple[str, bytes]]):
        await self._ensure_client()
        assert self._client
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        mp = [("files", (name, content, "application/octet-stream")) for name, content in files]
        r = await self._client.post("/files", files=mp, headers=headers)
        r.raise_for_status()
        return r.json()

    async def files_get(self, filename: str) -> bytes:
        await self._ensure_client()
        assert self._client
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        r = await self._client.get(f"/files/{filename}", headers=headers)
        r.raise_for_status()
        return r.content


# Singleton для UI
api = ApiClient()
