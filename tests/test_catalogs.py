from pathlib import Path

from subway_bot.catalogs import CatalogRepository


class FakeCatalogRepository(CatalogRepository):
    def __init__(self) -> None:
        super().__init__(cache_dir=Path("."), ttl_seconds=60, timeout_seconds=1)
        self.payloads = {
            "characters_data": [
                {"number": 1, "id": "jake", "outfits": [{"id": "default"}]},
                {"number": 2, "id": "tricky", "outfits": None},
            ],
            "characters_links": [
                {"number": 1, "name": "Jake"},
                {"number": 2, "name": "Tricky"},
            ],
            "boards_data": [
                {"number": 1, "id": "default", "upgrades": [{"id": "default"}]},
            ],
            "boards_links": [
                {"number": 1, "name": "Default Board"},
            ],
            "playerprofile_data": {
                "profilePortraits": ["portrait_1", "portrait_2"],
                "profileFrames": ["frame_1"],
            },
            "playerprofile_links": {
                "Portraits": [{"name": "Portrait One"}, {"name": "Portrait Two"}],
                "Frames": [{"name": "Frame One"}],
            },
        }

    def _load_json(self, cache_key: str, url: str):  # type: ignore[override]
        return self.payloads[cache_key]


def test_character_catalog_merges_names_and_outfits() -> None:
    repository = FakeCatalogRepository()
    catalog = repository.get_catalog("characters")

    assert catalog[0].name == "Jake"
    assert catalog[0].extras == ("default",)
    assert catalog[1].extras == ()


def test_profile_catalog_paginates() -> None:
    repository = FakeCatalogRepository()
    page = repository.format_page("portraits", page=1, page_size=1)

    assert "\u0627\u0644\u0635\u0641\u062d\u0629 1/2" in page
    assert "1. Portrait One (portrait_1)" in page


def test_resolve_ids_to_numbers() -> None:
    repository = FakeCatalogRepository()
    assert repository.resolve_ids_to_numbers("portraits", ["portrait_2", "portrait_1"]) == [1, 2]
