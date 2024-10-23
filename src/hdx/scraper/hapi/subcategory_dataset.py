import logging
from typing import Dict, List, Optional

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.scraper.hapi.base_dataset import BaseDataset

logger = logging.getLogger(__name__)


class SubcategoryDataset(BaseDataset):
    def __init__(
        self,
        folder: str,
        configuration: Configuration,
        subcategory: str,
    ) -> None:
        super().__init__(folder, configuration, subcategory, subcategory)
        self.dataset.set_subnational(True)  # check
        self.countries = set()

    def add_country(self, countryiso3: str) -> None:
        self.countries.add(countryiso3)

    def get_dataset(self) -> Optional[Dataset]:
        self.dataset.add_country_locations(sorted(self.countries))
        return super().get_dataset()

    def add_resource(
        self,
        resource_info: Dict,
        hxltags: Dict,
        rows: List[Dict],
    ) -> bool:
        resource_name = resource_info["name"]
        resource_name = f"Global {resource_name}"
        resource_description = resource_info["description"]
        filename = resource_info["filename"]
        filename = f"{filename}_global.csv"
        return self._add_resource(
            resource_name, resource_description, filename, hxltags, rows
        )
