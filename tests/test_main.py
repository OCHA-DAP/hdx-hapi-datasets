import logging
from os.path import join

import pytest
from hapi_schema.views import prepare_hapi_views

from hdx.api.configuration import Configuration
from hdx.api.locations import Locations
from hdx.data.vocabulary import Vocabulary
from hdx.database import Database
from hdx.database.dburi import get_params_from_connection_uri
from hdx.database.postgresql import PostgresError
from hdx.scraper.hapi.country_dataset import CountryDataset
from hdx.scraper.hapi.subcategory_reader import SubcategoryReader
from hdx.utilities.compare import assert_files_same
from hdx.utilities.path import script_dir_plus_file, temp_dir
from hdx.utilities.useragent import UserAgent

logger = logging.getLogger(__name__)


class TestHAPIPipelineHNO:
    @pytest.fixture(scope="function")
    def configuration(self):
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
                )
            ],
            "id": "b891512e-9516-4bf5-962a-7a289772a2a1",
            "name": "approved",
        }
        return Configuration.read()

    @pytest.fixture(scope="class")
    def fixtures_dir(self):
        return join("tests", "fixtures")

    @pytest.fixture(scope="function")
    def input_database(self, fixtures_dir):
        return join(fixtures_dir, "hapi_db.pg_restore")

    @pytest.fixture(scope="function")
    def db_uri(self):
        return "postgresql+psycopg://postgres:postgres@localhost:5432/hapirestoretest"

    def test_main(
        self,
        configuration,
        fixtures_dir,
        input_database,
        db_uri,
    ):
        with temp_dir(
            "TestHAPIDatasets",
            delete_on_success=True,
            delete_on_failure=False,
        ) as tempdir:
            params = get_params_from_connection_uri(db_uri)
            params["pg_restore_file"] = input_database
            params["prepare_fn"] = prepare_hapi_views
            try:
                database = Database(**params)
            except PostgresError as ex:
                if 'table "location" does not exist' in str(ex):
                    database = Database(**params)
                else:
                    raise ex
            subcategories = configuration["subcategories"]
            try:
                subcategory_reader = SubcategoryReader(
                    configuration,
                    database,
                )
                for countryiso3 in subcategory_reader.get_all_countries():
                    country_dataset = CountryDataset(
                        tempdir, configuration, countryiso3
                    )
                    for _, subcategory_info in subcategories.items():
                        subcategory_reader.view_by_location(
                            country_dataset, subcategory_info, countryiso3
                        )
                    dataset = country_dataset.get_dataset()
                    assert dataset == {
                        "name": "hdx-hapi-afg",
                        "title": "HDX HAPI data for Afghanistan",
                        "maintainer": "196196be-6037-4488-8b71-d786adf4c081",
                        "owner_org": "hdx",
                        "dataset_source": "Test Provider",
                        "data_update_frequency": "1",
                        "groups": [{"name": "afg"}],
                        "subnational": "1",
                        "tags": [
                            {
                                "name": "baseline population",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "conflict-violence",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "displacement",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "economics",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "education",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "food security",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "funding",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "hazards and risk",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "health",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "humanitarian needs overview-hno",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "hxl",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "indicators",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "internally displaced persons-idp",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "markets",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "migration",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "operational presence",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "people in need-pin",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "poverty",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "refugees",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "returnees",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                            {
                                "name": "who is doing what and where-3w-4w-5w",
                                "vocabulary_id": "b891512e-9516-4bf5-962a-7a289772a2a1",
                            },
                        ],
                        "dataset_date": "[2024-01-01T00:00:00 TO 2024-12-31T23:59:59]",
                    }
                    resources = dataset.get_resources()
                    assert resources == [
                        {
                            "name": "Funding Data for Afghanistan",
                            "description": "Curated Funding Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Population Data for Afghanistan",
                            "description": "Curated Population Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Humanitarian Needs Data for Afghanistan",
                            "description": "Curated Humanitarian Needs Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Operational Presence Data for Afghanistan",
                            "description": "Curated Operational Presence Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Food Price Data for Afghanistan",
                            "description": "Curated Food Price Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Food Security Data for Afghanistan",
                            "description": "Curated Food Security Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Conflict Event Data for Afghanistan",
                            "description": "Curated Conflict Event Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "IDPs Data for Afghanistan",
                            "description": "Curated IDPs Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "National Risk Data for Afghanistan",
                            "description": "Curated National Risk Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Refugees Data for Afghanistan",
                            "description": "Curated Refugees Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Returnees Data for Afghanistan",
                            "description": "Curated Returnees Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Poverty Rate Data for Afghanistan",
                            "description": "Curated Poverty Rate with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                        {
                            "name": "Data Availability Data for Afghanistan",
                            "description": "Data Availability Data with HXL hashtags",
                            "format": "csv",
                            "resource_type": "file.upload",
                            "url_type": "upload",
                        },
                    ]
                    for subcategory in subcategories:
                        filename = f"hdx_hapi_{subcategory}_afg.csv"
                        expected_file = join(fixtures_dir, filename)
                        actual_file = join(tempdir, filename)
                        assert_files_same(expected_file, actual_file)
            finally:
                database.cleanup()
