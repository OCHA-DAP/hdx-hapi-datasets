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
        self.countryname = Country.get_country_name_from_iso3(countryiso3)
        title = configuration["country_dataset_title"].format(suffix=self.countryname)
        name = configuration["dataset_name"].format(suffix=countryiso3)
        super().__init__(folder, configuration, title, name)
        self.dataset.add_country_location(countryiso3)
        self.dataset.set_subnational(True)
        self.site_url = configuration.get_hdx_site_url()
        self.multiple_licenses = configuration["country_multiple_licenses"]

    def add_resource(
        self,
        subcategory: str,
        subcategory_info: Dict,
        rows: List[Dict],
    ) -> bool:
        resource_info = subcategory_info["resource"]
        resource_name = resource_info["name"]
        resource_name = f"{resource_name} for {self.countryname}"
        resource_description = resource_info["description"]
        source_override = subcategory_info.get("source_override")
        if source_override:
            resource_description = (
                f"{resource_description}  \nSource: {source_override}"
            )
        else:
            hdx_providers = self.sources.get(subcategory)
            if hdx_providers:
                if len(hdx_providers) == 1:
                    hdx_provider_stub, hdx_provider_name = next(iter(hdx_providers))
                    site_url = self.configuration.get_hdx_site_url()
                    source = f"[{hdx_provider_name}]({site_url}/organization/{hdx_provider_stub})"
                    resource_description = f"{resource_description}  \nSource: {source}"
                else:
                    raise ValueError(
                        f"Too many sources for {self.countryiso3}: {resource_name}!"
                    )
        license_override = subcategory_info.get("license_override")
        if license_override:
            resource_description = (
                f"{resource_description}  \nLicense: {license_override}"
            )
        else:
            licenses = self.licenses.get(subcategory)
            if licenses:
                if len(licenses) == 1:
                    (
                        license_id,
                        license_title,
                        license_url,
                        license_description,
                    ) = next(iter(licenses))
                    if license_id == "hdx-other":
                        license = license_description
                    else:
                        license = f"[{license_title}]({license_url})"
                    resource_description = (
                        f"{resource_description}  \nLicense: {license}"
                    )
                else:
                    raise ValueError(
                        f"Too many licenses for {self.countryiso3}: {resource_name}!"
                    )
        filename = resource_info["filename"]
        filename = f"{filename}_{self.countryiso3.lower()}.csv"
        hxltags = subcategory_info["hxltags"]
        p_coded = resource_info.get("p_coded")
        return self._add_resource(
            resource_name, resource_description, filename, hxltags, rows, p_coded
        )
