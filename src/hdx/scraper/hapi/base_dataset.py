import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from slugify import slugify

from hdx.api.configuration import Configuration
from hdx.data.dataset import Dataset
from hdx.utilities.dateparse import default_date, default_enddate
from hdx.utilities.dictandlist import dict_of_sets_add

logger = logging.getLogger(__name__)


class BaseDataset(ABC):
    def __init__(
        self,
        folder: str,
        configuration: Configuration,
        title: str,
        name: str,
    ) -> None:
        self.folder = folder
        self.configuration = configuration
        self.dataset = self.create_dataset(title, name)
        self.tags = {"hxl"}
        self.start_date = default_enddate
        self.end_date = default_date
        self.sources = {}
        self.licenses = {}
        self.multiple_licenses = None

    @staticmethod
    def create_dataset(title: str, name: str) -> Dataset:
        logger.info(f"Creating dataset: {title}")
        slugified_name = slugify(name).lower()
        dataset = Dataset(
            {
                "name": slugified_name,
                "title": title,
            }
        )
        dataset.set_maintainer("196196be-6037-4488-8b71-d786adf4c081")
        dataset.set_organization("40d10ece-49de-4791-9aed-e164f1d16dd1")
        dataset.set_expected_update_frequency("Every day")
        dataset.preview_off()
        return dataset

    def update_start_date(self, date: datetime) -> None:
        if date < self.start_date:
            self.start_date = date

    def update_end_date(self, date: datetime) -> None:
        if date > self.end_date:
            self.end_date = date

    def add_tags(self, tags: List[str]) -> None:
        self.tags.update(tags)

    def add_source(self, subcategory: str, source: Tuple[str, str]) -> None:
        dict_of_sets_add(self.sources, subcategory, source)

    def add_license(self, subcategory: str, license: Tuple[str, str, str, str]) -> None:
        dict_of_sets_add(self.licenses, subcategory, license)

    def get_dataset(self) -> Optional[Dataset]:
        if len(self.dataset.get_resources()) == 0:
            return None
        self.dataset.add_tags(sorted(self.tags))
        self.dataset.set_time_period(self.start_date, self.end_date)
        all_sources = set()
        for _, sources in self.sources.items():
            for _, hdx_provider_name in sources:
                all_sources.add(hdx_provider_name)
        if len(all_sources) == 0:
            all_sources.add(self.configuration["default_source"])
        self.dataset["dataset_source"] = ", ".join(sorted(all_sources))
        all_licenses = set()
        for _, licenses in self.licenses.items():
            all_licenses.update(licenses)
        match len(all_licenses):
            case 0:
                self.dataset["license_id"] = self.configuration["default_license"]
            case 1:
                (
                    license_id,
                    license_title,
                    license_url,
                    license_description,
                ) = next(iter(all_licenses))
                self.dataset["license_id"] = license_id
                if license_id == "hdx-other":
                    self.dataset["license_other"] = license_description
            case _:
                self.dataset["license_id"] = "hdx-other"
                if self.multiple_licenses:
                    licenses = [self.multiple_licenses]
                else:
                    licenses = []
                    for (
                        license_id,
                        license_title,
                        license_url,
                        license_description,
                    ) in sorted(all_licenses):
                        if license_id == "hdx-other":
                            licenses.append(f"{license_description}")
                        else:
                            licenses.append(f"[{license_title}]({license_url})")
                self.dataset["license_other"] = "  \n".join(licenses)
        return self.dataset

    def _add_resource(
        self,
        resource_name: str,
        resource_description: str,
        filename: str,
        hxltags: Dict,
        rows: List[Dict],
        p_coded: Optional[bool],
    ) -> bool:
        resourcedata = {
            "name": resource_name,
            "description": resource_description,
        }
        if p_coded is not None:
            resourcedata["p_coded"] = p_coded
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
        subcategory: str,
        subcategory_info: Dict,
        rows: List[Dict],
    ) -> bool:
        pass
