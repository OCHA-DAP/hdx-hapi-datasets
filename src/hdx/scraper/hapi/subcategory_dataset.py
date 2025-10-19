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
        subcategory_config = configuration["subcategories"][subcategory]
        title = subcategory_config["title"]
        name = configuration["dataset_name"].format(suffix=subcategory)
        super().__init__(folder, configuration, title, name)
        subnational = False
        for header in subcategory_config["headers"]:
            if header in (
                "provider_admin1_name",
                "provider_admin2_name",
                "admin1_code",
                "admin2_code",
            ):
                subnational = True
                break
        self.dataset.set_subnational(subnational)
        self.countries = set()

    def add_country(self, countryiso3: str) -> None:
        self.countries.add(countryiso3)

    def get_dataset(self) -> Optional[Dataset]:
        self.dataset.add_country_locations(sorted(self.countries))
        return super().get_dataset()

    def add_resource(
        self,
        subcategory: str,
        subcategory_info: Dict,
        rows: List[Dict],
    ) -> bool:
        resource_info = subcategory_info["resource"]
        resource_name = resource_info["name"]
        resource_name = f"Global {resource_name}"
        resource_description = resource_info["description"]
        filename = resource_info["filename"]
        filename = f"{filename}_global.csv"
        headers = subcategory_info["headers"]
        p_coded = resource_info.get("p_coded")
        return self._add_resource(
            resource_name, resource_description, filename, headers, rows, p_coded
        )
