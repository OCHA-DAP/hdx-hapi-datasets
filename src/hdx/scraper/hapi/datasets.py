from typing import List

from hdx.api.configuration import Configuration
from hdx.scraper.hapi.country_dataset import CountryDataset
from hdx.scraper.hapi.subcategory_dataset import SubcategoryDataset


class Datasets:
    def __init__(
        self,
        folder: str,
        configuration: Configuration,
        countryiso3s: List[str],
    ):
        self.subcategory_datasets = {}
        for subcategory in configuration["subcategories"]:
            subcategory_dataset = SubcategoryDataset(
                folder, configuration, subcategory
            )
            self.subcategory_datasets[subcategory] = subcategory_dataset

        self.country_datasets = {}
        for countryiso3 in countryiso3s:
            country_dataset = CountryDataset(
                folder, configuration, countryiso3
            )
            self.country_datasets[countryiso3] = country_dataset

    def get_country_dataset(self, countryiso3: str) -> CountryDataset:
        return self.country_datasets[countryiso3]

    def get_subcategory_dataset(self, subcategory: str) -> SubcategoryDataset:
        return self.subcategory_datasets[subcategory]
