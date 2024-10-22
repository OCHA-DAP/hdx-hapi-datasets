import logging
from typing import Dict, List

from hdx.api.configuration import Configuration
from hdx.location.country import Country
from hdx.scraper.hapi.base_dataset import BaseDataset

logger = logging.getLogger(__name__)


class CountryDataset(BaseDataset):
    def __init__(
        self, folder: str, configuration: Configuration, countryiso3: str
    ) -> None:
        self.countryiso3 = countryiso3
        countryname = Country.get_country_name_from_iso3(countryiso3)
        super().__init__(folder, configuration, countryname)
        self.dataset.add_country_location(countryiso3)
        self.dataset.set_subnational(True)

    def add_resource(
        self,
        resource_info: Dict,
        hxltags: Dict,
        rows: List[Dict],
    ) -> bool:
        resource_name = resource_info["name"]
        resource_name = f"{resource_name} for {self.what}"
        resource_description = resource_info["description"]
        filename = resource_info["filename"]
        filename = f"{filename}_{self.countryiso3.lower()}.csv"
        return self._add_resource(
            resource_name, resource_description, filename, hxltags, rows
        )
