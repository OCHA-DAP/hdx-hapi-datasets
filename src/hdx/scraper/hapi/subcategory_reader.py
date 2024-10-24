import logging
from typing import Dict, List, Tuple

from sqlalchemy import select

from hdx.api.configuration import Configuration
from hdx.database import Database
from hdx.location.country import Country
from hdx.scraper.framework.utilities.reader import Read
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
        (
            self.resource_hdx_id_to_hdx_provider,
            self.resource_hdx_id_to_license,
        ) = self.get_mappings()
        self.countryiso3s = self.read_countries()

    def get_mappings(self) -> Tuple[Dict, Dict]:
        view = self.views["resource"]
        results = self.session.execute(
            select(
                view.c.hdx_id,
                view.c.dataset_hdx_id,
                view.c.dataset_hdx_provider_stub,
                view.c.dataset_hdx_provider_name,
            )
        ).all()
        resource_hdx_id_to_hdx_provider = {}
        resource_hdx_id_to_license = {}
        for (
            hdx_id,
            dataset_hdx_id,
            hdx_provider_stub,
            hdx_provider_name,
        ) in results:
            resource_hdx_id_to_hdx_provider[hdx_id] = (
                hdx_provider_stub,
                hdx_provider_name,
            )
            dataset = Read.get_reader("hdx").read_dataset(dataset_hdx_id)
            license_id = dataset["license_id"]
            title = dataset.get("license_title")
            url = dataset.get("license_url")
            description = dataset.get("license_other")
            license = (license_id, title, url, description)
            resource_hdx_id_to_license[hdx_id] = license
        return resource_hdx_id_to_hdx_provider, resource_hdx_id_to_license

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
        subcategory: str,
        subcategory_info: Dict,
        dataset: BaseDataset,
        rows: List[Dict],
    ) -> bool:
        if len(rows) == 0:
            return False
        tags = subcategory_info["tags"]
        dataset.add_tags(tags)
        return dataset.add_resource(subcategory, subcategory_info, rows)

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
            if index is None:
                index_origin = headers_to_index.get("origin_location_code")
                countryiso3_origin = result[index_origin]
                index_asylum = headers_to_index.get("asylum_location_code")
                countryiso3_asylum = result[index_asylum]
                if countryiso3_origin == countryiso3_asylum:
                    countryiso3s = [countryiso3_origin]
                else:
                    countryiso3s = [countryiso3_origin, countryiso3_asylum]
            else:
                countryiso3s = [result[index]]
            country_datasets = []
            for countryiso3 in countryiso3s:
                if countryiso3 in self.countryiso3s:
                    country_datasets.append(
                        datasets.get_country_dataset(countryiso3)
                    )

            index = headers_to_index.get("resource_hdx_id")
            if index is not None:
                resource_hdx_id = result[index]
                hdx_provider = self.resource_hdx_id_to_hdx_provider[
                    resource_hdx_id
                ]
                license = self.resource_hdx_id_to_license[resource_hdx_id]
                subcategory_dataset.add_source(subcategory, hdx_provider)
                subcategory_dataset.add_license(subcategory, license)
                for country_dataset in country_datasets:
                    country_dataset.add_source(subcategory, hdx_provider)
                    country_dataset.add_license(subcategory, license)
            hxltags = subcategory_info["hxltags"]
            row = {}
            for header, hxltag in hxltags.items():
                value = result[headers_to_index[header]]
                if hxltag == "#date+start":
                    subcategory_dataset.update_start_date(value)
                    for country_dataset in country_datasets:
                        country_dataset.update_start_date(value)
                    value = iso_string_from_datetime(value)
                elif hxltag == "#date+end":
                    subcategory_dataset.update_end_date(value)
                    for country_dataset in country_datasets:
                        country_dataset.update_end_date(value)
                    value = iso_string_from_datetime(value)
                elif hxltag == "#date+updated":
                    # data availability table only has an update date
                    subcategory_dataset.update_start_date(value)
                    subcategory_dataset.update_end_date(value)
                    value = iso_string_from_datetime(value)
                row[header] = str(value)
            rows.append(row)
            for countryiso3 in countryiso3s:
                subcategory_dataset.add_country(countryiso3)
                if countryiso3 not in self.countryiso3s:
                    continue
                dict_of_lists_add(rows_by_countryiso3, countryiso3, row)
        success = self.add_resource(
            subcategory, subcategory_info, subcategory_dataset, rows
        )
        if not success:
            return False
        for countryiso3, country_rows in rows_by_countryiso3.items():
            country_dataset = datasets.get_country_dataset(countryiso3)
            subcategory_info["subcategory"] = subcategory
            success = self.add_resource(
                subcategory, subcategory_info, country_dataset, country_rows
            )
            if not success:
                return False
        return True
