import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from slugify import slugify

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.utilities.dateparse import default_date, default_enddate

logger = logging.getLogger(__name__)


class BaseDataset(ABC):
    def __init__(
        self, folder: str, configuration: Configuration, what: str
    ) -> None:
        self.folder = folder
        self.configuration = configuration["dataset"]
        self.what = what
        self.dataset = self.create_dataset(what)
        self.tags = {"hxl"}
        self.start_date = default_enddate
        self.end_date = default_date
        self.sources = set()

    def create_dataset(self, what: str) -> Dataset:
        title = self.configuration["title"]
        title = f"{title} {what}"
        logger.info(f"Creating dataset: {title}")
        name = self.configuration["name"]
        name = f"{name}-{what}"
        slugified_name = slugify(name).lower()
        dataset = Dataset(
            {
                "name": slugified_name,
                "title": title,
            }
        )
        dataset.set_maintainer("196196be-6037-4488-8b71-d786adf4c081")
        dataset.set_organization("hdx")
        dataset.set_expected_update_frequency("Every day")
        return dataset

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

    def _add_resource(
        self,
        resource_name: str,
        resource_description: str,
        filename: str,
        hxltags: Dict,
        rows: List[Dict],
    ) -> bool:
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

    @abstractmethod
    def add_resource(
        self,
        resource_info: Dict,
        hxltags: Dict,
        rows: List[Dict],
    ) -> bool:
        pass
