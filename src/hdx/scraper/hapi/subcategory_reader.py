import logging
from typing import Dict, List

from sqlalchemy import select

from hdx.api.configuration import Configuration
from hdx.database import Database
from hdx.location.country import Country
from hdx.utilities.dateparse import (
    iso_string_from_datetime,
)
from hdx.utilities.dictandlist import dict_of_lists_add

from .base_dataset import BaseDataset
from .datasets import Datasets

logger = logging.getLogger(__name__)


class SubcategoryReader:
    def __init__(
        self,
        configuration: Configuration,
        database: Database,
    ):
        self.configuration = configuration
        self.session = database.get_session()
        self.views = database.get_prepare_results()
        self.resource_hdx_id_to_hdx_provider_name = (
            self.get_resource_hdx_id_to_hdx_provider_name_mapping()
        )
        self.countryiso3s = self.read_countries()

    def get_resource_hdx_id_to_hdx_provider_name_mapping(self) -> Dict:
        view = self.views["resource"]
        results = self.session.execute(
            select(view.c.hdx_id, view.c.dataset_hdx_provider_name)
        ).all()
        return {
            hdx_id: dataset_hdx_provider_name
            for hdx_id, dataset_hdx_provider_name in results
        }

    def read_countries(self) -> List[str]:
        view = self.views["data_availability"]
        countryiso3s = []
        for countryiso3 in self.session.scalars(
            select(view.c.location_code).distinct()
        ).all():
            country_info = Country.get_country_info_from_iso3(countryiso3)
            if country_info["#indicator+incomelevel"].lower() == "high":
                continue
            countryiso3s.append(countryiso3)
        return sorted(countryiso3s)

    @staticmethod
    def add_resource(
        subcategory_info: Dict, dataset: BaseDataset, rows: List[Dict]
    ) -> bool:
        if len(rows) == 0:
            return False
        resource_info = subcategory_info["resource"]
        tags = subcategory_info["tags"]
        dataset.add_tags(tags)
        hxltags = subcategory_info["hxltags"]
        return dataset.add_resource(resource_info, hxltags, rows)

    def get_countries(self) -> List[str]:
        return self.countryiso3s

    def get_subcategory(
        self,
        subcategory: str,
        datasets: Datasets,
    ) -> bool:
        subcategory_info = self.configuration["subcategories"][subcategory]
        subcategory_dataset = datasets.get_subcategory_dataset(subcategory)
        logger.info(f"Processing subcategory {subcategory}")
        view = self.views[subcategory]
        headers_to_index = {col.name: i for i, col in enumerate(view.c)}
        results = self.session.execute(select(view))
        rows = []
        rows_by_countryiso3 = {}
        for result in results:
            index = headers_to_index.get("location_code")
            countryiso3 = result[index]
            if countryiso3 in self.countryiso3s:
                country_dataset = datasets.get_country_dataset(countryiso3)
            else:
                country_dataset = None
            index = headers_to_index.get("resource_hdx_id")
            if index is not None:
                resource_hdx_id = result[index]
                dataset_provider_name = (
                    self.resource_hdx_id_to_hdx_provider_name[resource_hdx_id]
                )
                subcategory_dataset.add_sources(dataset_provider_name)
                if country_dataset:
                    country_dataset.add_sources(dataset_provider_name)
            hxltags = subcategory_info["hxltags"]
            row = {}
            for header, hxltag in hxltags.items():
                value = result[headers_to_index[header]]
                if hxltag == "#date+start":
                    subcategory_dataset.update_start_date(value)
                    if country_dataset:
                        country_dataset.update_start_date(value)
                    value = iso_string_from_datetime(value)
                elif hxltag == "#date+end":
                    subcategory_dataset.update_end_date(value)
                    if country_dataset:
                        country_dataset.update_end_date(value)
                    value = iso_string_from_datetime(value)
                row[header] = str(value)
            rows.append(row)
            subcategory_dataset.add_country(countryiso3)
            if country_dataset:
                dict_of_lists_add(rows_by_countryiso3, countryiso3, row)
        success = self.add_resource(
            subcategory_info, subcategory_dataset, rows
        )
        if not success:
            return False
        for countryiso3, country_rows in rows_by_countryiso3.items():
            country_dataset = datasets.get_country_dataset(countryiso3)
            success = self.add_resource(
                subcategory_info, country_dataset, country_rows
            )
            if not success:
                return False
        return True
