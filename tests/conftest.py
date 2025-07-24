from os.path import join

import pytest

from hdx.api.configuration import Configuration
from hdx.api.locations import Locations
from hdx.data.vocabulary import Vocabulary
from hdx.scraper.hapi.subcategory_reader import SubcategoryReader
from hdx.utilities.path import script_dir_plus_file
from hdx.utilities.useragent import UserAgent


@pytest.fixture(scope="session")
def configuration():
    UserAgent.set_global("test")
    Configuration._create(
        hdx_read_only=True,
        hdx_site="prod",
        project_config_yaml=script_dir_plus_file(
            join("config", "project_configuration.yaml"), SubcategoryReader
        ),
    )
    Locations.set_validlocations(
        [
            {"name": "AFG", "title": "Afghanistan"},
            {"name": "SDN", "title": "Sudan"},
        ]
    )
    Vocabulary._approved_vocabulary = {
        "tags": [
            {"name": tag}
            for tag in (
                "hxl",
                "funding",
                "baseline population",
                "operational presence",
                "who is doing what and where-3w-4w-5w",
                "humanitarian needs overview-hno",
                "people in need-pin",
                "economics",
                "markets",
                "food security",
                "conflict-violence",
                "displacement",
                "internally displaced persons-idp",
                "migration",
                "hazards and risk",
                "refugees",
                "returnees",
                "education",
                "health",
                "indicators",
                "poverty",
                "climate-weather",
            )
        ],
        "id": "b891512e-9516-4bf5-962a-7a289772a2a1",
        "name": "approved",
    }
    return Configuration.read()


@pytest.fixture(scope="session")
def fixtures_dir():
    return join("tests", "fixtures")


@pytest.fixture(scope="session")
def input_dir(fixtures_dir):
    return join(fixtures_dir, "input")
