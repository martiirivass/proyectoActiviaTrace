import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class MoodleWSException(Exception):
    pass


class MoodleWSClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _call(self, wsfunction: str, **params) -> dict:
        client = await self._get_client()
        url = f"{self.base_url}/webservice/rest/server.php"
        params["wstoken"] = self.token
        params["wsfunction"] = wsfunction
        params["moodlewsrestformat"] = "json"

        last_exc = None
        delays = [1, 4, 9]

        for attempt in range(len(delays) + 1):
            try:
                response = await client.post(url, data=params)
                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and "exception" in data:
                    raise MoodleWSException(
                        f"Moodle WS error: {data.get('message', 'Unknown error')} "
                        f"(code: {data.get('errorcode', 'unknown')})"
                    )

                return data

            except httpx.TimeoutException as e:
                last_exc = MoodleWSException(f"Timeout al conectar con Moodle: {str(e)}")
            except httpx.HTTPStatusError as e:
                last_exc = MoodleWSException(
                    f"HTTP error {e.response.status_code} de Moodle: {e.response.text[:200]}"
                )
            except MoodleWSException:
                raise
            except Exception as e:
                last_exc = MoodleWSException(f"Error inesperado al conectar con Moodle: {str(e)}")

            if attempt < len(delays):
                logger.warning(
                    "Moodle WS attempt %d failed, retrying in %ds: %s",
                    attempt + 1, delays[attempt], last_exc,
                )
                await asyncio.sleep(delays[attempt])

        raise last_exc  # type: ignore

    async def get_users_by_cohort(self, cohorte_id: int | str) -> list[dict]:
        data = await self._call(
            "core_cohort_get_members",
            cohortids=[cohorte_id],
        )
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("userids", [])
        return []

    async def get_activities_by_course(self, materia_id: int | str) -> list[dict]:
        data = await self._call(
            "core_course_get_contents",
            courseid=materia_id,
        )
        return data if isinstance(data, list) else []
