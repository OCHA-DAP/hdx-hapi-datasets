from datetime import datetime
from typing import Optional

from sqlalchemy import select

from hdx.api.configuration import Configuration
from hdx.database import Database
from hdx.scraper.hapi.country_dataset import CountryDataset
from hdx.utilities.dateparse import (
    iso_string_from_datetime,
)
from hdx.utilities.errors_onexit import ErrorsOnExit


class ViewReader:
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

    def view_by_location(self, view_name: str, countryiso3: str) -> bool:
        view_info = self.configuration[view_name]
        view = self.views[view_info["view"]]
        results = self.session.execute(
            select(view).where(view.c.location_code == countryiso3)
        )
        headers_to_index = {col.name: i for i, col in enumerate(view.c)}
        hxltags = view_info["hxltags"]
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
        self.country_dataset.add_tags(view_info["tags"])
        resource_info = view_info["resource"]
        return self.country_dataset.add_resource(resource_info, hxltags, rows)
