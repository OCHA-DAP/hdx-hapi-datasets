import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select

from hdx.api.configuration import Configuration
from hdx.database import Database
from hdx.scraper.hapi.country_dataset import CountryDataset
from hdx.utilities.dateparse import (
    iso_string_from_datetime,
)
from hdx.utilities.errors_onexit import ErrorsOnExit

logger = logging.getLogger(__name__)


class SubcategoryReader:
    def __init__(
        self,
        configuration: Configuration,
        database: Database,
        country_dataset: CountryDataset,
        today: datetime,
        errors_on_exit: Optional[ErrorsOnExit] = None,
    ):
        self.configuration = configuration
        self.session = database.get_session()
        self.views = database.get_prepare_results()
        self.country_dataset = country_dataset
        self.today = today
        self.errors_on_exit = errors_on_exit

    def view_by_location(
        self, subcategory_info: Dict, countryiso3: str
    ) -> bool:
        view_name = subcategory_info["view"]
        logger.info(f"Processing subcategory {view_name}")
        view = self.views[subcategory_info["view"]]
        headers_to_index = {col.name: i for i, col in enumerate(view.c)}
        if "origin_location_code" in headers_to_index:
            results = self.session.execute(
                select(view).where(
                    view.c.origin_location_code == countryiso3
                    or view.c.asylum_location_code == countryiso3
                )
            )
        else:
            results = self.session.execute(
                select(view).where(view.c.location_code == countryiso3)
            )

        hxltags = subcategory_info["hxltags"]
        rows = []
        for result in results:
            row = {}
            for header, hxltag in hxltags.items():
                value = result[headers_to_index[header]]
                if hxltag == "#date+start":
                    self.country_dataset.update_start_date(value)
                    value = iso_string_from_datetime(value)
                elif hxltag == "#date+end":
                    self.country_dataset.update_end_date(value)
                    value = iso_string_from_datetime(value)
                row[header] = str(value)
            rows.append(row)
        if len(rows) == 0:
            return False
        self.country_dataset.add_tags(subcategory_info["tags"])
        resource_info = subcategory_info["resource"]
        return self.country_dataset.add_resource(resource_info, hxltags, rows)
