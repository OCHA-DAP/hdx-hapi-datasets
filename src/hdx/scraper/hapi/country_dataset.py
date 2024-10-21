import logging
from datetime import datetime
from typing import Dict, List, Optional

from slugify import slugify

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.location.country import Country
from hdx.utilities.dateparse import default_date, default_enddate

logger = logging.getLogger(__name__)


class CountryDataset:
    def __init__(
        self, folder: str, configuration: Configuration, countryiso3: str
    ) -> None:
        self.folder = folder
        self.configuration = configuration["dataset"]
        title = self.configuration["title"]
        countryname = Country.get_country_name_from_iso3(countryiso3)
        title = f"{title} {countryname}"
        logger.info(f"Creating dataset: {title}")
        name = self.configuration["name"]
        name = f"{name}-{countryiso3}"
        slugified_name = slugify(name).lower()
        self.dataset = Dataset(
            {
                "name": slugified_name,
                "title": title,
            }
        )
        self.dataset.set_maintainer("196196be-6037-4488-8b71-d786adf4c081")
        self.dataset.set_organization("hdx")
        self.dataset.set_expected_update_frequency("Every day")
        self.dataset.add_country_location(countryiso3)
        self.tags = {"hxl"}
        self.start_date = default_enddate
        self.end_date = default_date
        self.sources = set()
        self.dataset.set_subnational(True)

    def update_start_date(self, date: datetime) -> None:
        if date < self.start_date:
            self.start_date = date

    def update_end_date(self, date: datetime) -> None:
        if date > self.end_date:
            self.end_date = date

    def add_tags(self, tags: List[str]) -> None:
        self.tags.update(tags)

    def add_sources(self, sources: List[str]) -> None:
        self.sources.add(sources)

    def get_dataset(self) -> Optional[Dataset]:
        if len(self.dataset.get_resources()) == 0:
            return None
        self.dataset.add_tags(sorted(self.tags))
        self.dataset.set_time_period(self.start_date, self.end_date)
        self.dataset["dataset_source"] = ", ".join(sorted(self.sources))
        return self.dataset

    def add_resource(
        self,
        resource_info: Dict,
        hxltags: Dict,
        rows: List[Dict],
    ) -> bool:
        countryiso3 = self.dataset.get_location_iso3s()[0]
        country_name = Country.get_country_name_from_iso3(countryiso3)
        resource_name = resource_info["name"]
        resource_name = f"{resource_name} {country_name}"
        resource_description = resource_info["description"]
        filename = resource_info["filename"]
        filename = f"{filename}_{countryiso3.lower()}.csv"
        resourcedata = {
            "name": resource_name,
            "description": resource_description,
        }
        headers = list(hxltags.keys())
        success, results = self.dataset.generate_resource_from_iterable(
            headers,
            rows,
            hxltags,
            self.folder,
            filename,
            resourcedata,
        )
        return success
