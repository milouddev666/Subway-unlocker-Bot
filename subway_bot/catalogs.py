from __future__ import annotations

import json
import logging
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from subway_bot.constants import CATALOG_ENDPOINTS
from subway_bot.i18n import ar

logger = logging.getLogger(__name__)


class CatalogError(RuntimeError):
    """Raised when a remote catalog cannot be loaded or interpreted."""


@dataclass(frozen=True)
class CatalogEntry:
    number: int
    id: str
    name: str
    extras: tuple[str, ...] = ()


class CatalogRepository:
    def __init__(self, *, cache_dir: Path, ttl_seconds: int, timeout_seconds: float) -> None:
        self._cache_dir = cache_dir
        self._ttl_seconds = ttl_seconds
        self._timeout_seconds = timeout_seconds
        self._memory_cache: dict[str, tuple[float, Any]] = {}

    def get_catalog(self, kind: str) -> list[CatalogEntry]:
        if kind == "characters":
            return self._get_character_catalog()
        if kind == "hoverboards":
            return self._get_hoverboard_catalog()
        if kind == "portraits":
            return self._get_profile_catalog(profile_key="profilePortraits", links_key="Portraits")
        if kind == "frames":
            return self._get_profile_catalog(profile_key="profileFrames", links_key="Frames")
        raise CatalogError(ar("نوع فهرس غير معروف: ") + kind)

    def resolve_numbers(self, kind: str, numbers: list[int]) -> list[CatalogEntry]:
        catalog = self.get_catalog(kind)
        by_number = {entry.number: entry for entry in catalog}
        missing = [str(number) for number in numbers if number not in by_number]
        if missing:
            raise CatalogError(
                ar("أرقام غير معروفة في فهرس ")
                + kind
                + ": "
                + ", ".join(missing)
                + ". "
                + ar("استخدم /catalog ")
                + kind
                + ar(" لعرض الأرقام الصحيحة.")
            )
        return [by_number[number] for number in numbers]

    def resolve_ids_to_numbers(self, kind: str, ids: list[str]) -> list[int]:
        catalog = self.get_catalog(kind)
        by_id = {entry.id: entry.number for entry in catalog}
        missing = [item_id for item_id in ids if item_id not in by_id]
        if missing:
            raise CatalogError(
                ar("هناك معرفات غير معروفة داخل الملف المرفوع لقسم ")
                + kind
                + ": "
                + ", ".join(missing)
            )
        return sorted(by_id[item_id] for item_id in ids)

    def resolve_id_to_number(self, kind: str, item_id: str) -> int:
        catalog = self.get_catalog(kind)
        by_id = {entry.id: entry.number for entry in catalog}
        try:
            return by_id[item_id]
        except KeyError as exc:
            raise CatalogError(
                ar("المعرف التالي غير معروف داخل الملف المرفوع لقسم ")
                + kind
                + ": "
                + item_id
            ) from exc

    def format_page(self, kind: str, page: int, page_size: int) -> str:
        if page <= 0:
            raise CatalogError(ar("رقم الصفحة يبدأ من 1."))

        catalog = self.get_catalog(kind)
        total_pages = max(1, (len(catalog) + page_size - 1) // page_size)
        if page > total_pages:
            raise CatalogError(ar(f"هذه الصفحة غير موجودة. آخر صفحة هي {total_pages}."))

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_items = catalog[start_index:end_index]

        header = ar(f"فهرس {kind} — الصفحة {page}/{total_pages}")
        lines = [header, ""]
        lines.extend(f"{entry.number}. {entry.name} ({entry.id})" for entry in page_items)
        return "\n".join(lines)

    def _get_character_catalog(self) -> list[CatalogEntry]:
        data = self._load_json("characters_data", CATALOG_ENDPOINTS["characters"]["data"])
        links = self._load_json("characters_links", CATALOG_ENDPOINTS["characters"]["links"])
        link_map = {int(item["number"]): item for item in links}

        catalog: list[CatalogEntry] = []
        for item in data:
            number = int(item["number"])
            link = link_map.get(number, {})
            outfits = tuple(entry["id"] for entry in item.get("outfits") or ())
            catalog.append(
                CatalogEntry(
                    number=number,
                    id=item["id"],
                    name=str(link.get("name", item["id"])),
                    extras=outfits,
                )
            )
        return sorted(catalog, key=lambda entry: entry.number)

    def _get_hoverboard_catalog(self) -> list[CatalogEntry]:
        data = self._load_json("boards_data", CATALOG_ENDPOINTS["hoverboards"]["data"])
        links = self._load_json("boards_links", CATALOG_ENDPOINTS["hoverboards"]["links"])
        link_map = {int(item["number"]): item for item in links}

        catalog: list[CatalogEntry] = []
        for item in data:
            number = int(item["number"])
            link = link_map.get(number, {})
            upgrades = tuple(entry["id"] for entry in item.get("upgrades") or ())
            catalog.append(
                CatalogEntry(
                    number=number,
                    id=item["id"],
                    name=str(link.get("name", item["id"])),
                    extras=upgrades,
                )
            )
        return sorted(catalog, key=lambda entry: entry.number)

    def _get_profile_catalog(self, *, profile_key: str, links_key: str) -> list[CatalogEntry]:
        data = self._load_json("playerprofile_data", CATALOG_ENDPOINTS["playerprofile"]["data"])
        links = self._load_json("playerprofile_links", CATALOG_ENDPOINTS["playerprofile"]["links"])

        profile_ids = data[profile_key]
        profile_links = links[links_key]

        catalog: list[CatalogEntry] = []
        for index, item_id in enumerate(profile_ids, start=1):
            link = profile_links[index - 1] if index - 1 < len(profile_links) else {}
            catalog.append(
                CatalogEntry(
                    number=index,
                    id=item_id,
                    name=str(link.get("name", item_id)),
                )
            )
        return catalog

    def _load_json(self, cache_key: str, url: str) -> Any:
        now = time.time()
        memory_entry = self._memory_cache.get(cache_key)
        if memory_entry and memory_entry[0] > now:
            return memory_entry[1]

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / f"{cache_key}.json"

        if cache_path.exists() and now - cache_path.stat().st_mtime <= self._ttl_seconds:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            self._memory_cache[cache_key] = (now + self._ttl_seconds, data)
            return data

        try:
            data = self._fetch_json(url)
        except Exception as exc:
            if cache_path.exists():
                logger.warning(
                    "Falling back to stale cache for %s after fetch failure: %s",
                    cache_key,
                    exc,
                )
                data = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                raise CatalogError(
                    ar("تعذر تحميل بيانات الفهرس المطلوبة الآن. حاول مرة أخرى لاحقًا.")
                ) from exc
        else:
            with NamedTemporaryFile(
                "w",
                encoding="utf-8",
                delete=False,
                dir=self._cache_dir,
            ) as handle:
                json.dump(data, handle)
                temp_path = Path(handle.name)
            temp_path.replace(cache_path)

        self._memory_cache[cache_key] = (now + self._ttl_seconds, data)
        return data

    def _fetch_json(self, url: str) -> Any:
        request = urllib.request.Request(url, headers={"User-Agent": "subway-telegram-bot/1.0"})
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
