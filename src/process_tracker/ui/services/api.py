from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
import asyncio

# мягкая зависимость от httpx
try:
    import httpx  # type: ignore
except Exception:
    httpx = None  # type: ignore

from ...core.config import settings  # type: ignore


def _default_base_url() -> str:
    base = getattr(settings, "api_base_url", None) or ""
    base = base.strip("/") if base else ""
    if not base:
        base = f"http://127.0.0.1:{getattr(settings, 'api_port', 8787)}/api/v1"
    else:
        if not base.endswith("/api/v1"):
            base = base.rstrip("/") + "/api/v1"
    return base


def _build_timeout() -> Any:
    """
    Совместимость с разными версиями httpx:
    - новые: нужно указать либо default, либо все 4 поля
    - старые: допускают частичные значения
    """
    if httpx is None:
        return None
    try:
        # универсальный вариант: один общий таймаут + явные connect/read/write/pool
        return httpx.Timeout(20.0, connect=5.0, read=20.0, write=20.0, pool=5.0)
    except Exception:
        try:
            # запасной — только общий
            return httpx.Timeout(20.0)
        except Exception:
            # минимальный фоллбек
            return None


class Api:
    def __init__(self) -> None:
        self.base_url: str = _default_base_url()
        self._token: Optional[str] = None
        self._client: Any = None

    def set_token(self, token: Optional[str]) -> None:
        self._token = (token or "").strip() or None

    async def _ensure_client(self) -> None:
        if self._client is not None:
            return
        if httpx is not None:
            timeout = _build_timeout()
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)
        else:
            self._client = object()  # маркер фоллбека

    async def _req(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: Dict[str, Any] | None = None,
    ) -> Any:
        await self._ensure_client()
        url = path if path.startswith("http") else f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        if httpx is not None:
            r = await self._client.request(method, url, json=json_body, params=params, headers=headers)
            r.raise_for_status()
            return r.json() if r.content else None

        # ---- фоллбек на urllib (синхронный) ----
        import urllib.request, urllib.parse  # noqa: WPS433

        def _do_sync():
            data = None
            query = ("?" + urllib.parse.urlencode(params)) if params else ""
            req = urllib.request.Request(
                url + query,
                method=method.upper(),
                headers={**headers, "Content-Type": "application/json"} if json_body is not None else headers,
                data=json.dumps(json_body).encode("utf-8") if json_body is not None else None,
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                return json.loads(body.decode("utf-8")) if body else None

        return await asyncio.to_thread(_do_sync)

    # ---------------- AUTH ----------------

    async def login_dev(self, email: str, roles: List[str], perms: List[str]) -> Dict[str, Any]:
        return await self._req("POST", "/auth/login", json_body={"email": email, "roles": roles, "perms": perms})

    async def me(self) -> Dict[str, Any]:
        return await self._req("GET", "/auth/me")

    # ---------------- TASKS ----------------

    async def list_tasks(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return await self._req("GET", "/tasks", params={"limit": limit, "offset": offset})

    async def create_task(self, title: str) -> Dict[str, Any]:
        return await self._req("POST", "/tasks", json_body={"title": title})

    # ---------------- PROCESSES ----------------

    async def list_processes(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return await self._req("GET", "/processes", params={"limit": limit, "offset": offset})

    async def create_process(self, name: str, status: str = "new") -> Dict[str, Any]:
        return await self._req("POST", "/processes", json_body={"name": name, "status": status})

    # ---------------- HELPERS ----------------

    async def dashboard_counts(self) -> Dict[str, int]:
        tasks = await self.list_tasks(limit=1000)
        open_cnt = sum(1 for t in tasks if not t.get("done"))
        done_cnt = sum(1 for t in tasks if t.get("done"))
        procs = await self.list_processes(limit=1000)
        return {"open": int(open_cnt), "done": int(done_cnt), "proc": int(len(procs))}

    async def aclose(self) -> None:
        if httpx is not None and self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
        self._client = None


api = Api()
