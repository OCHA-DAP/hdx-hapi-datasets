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
from hdx.scraper.framework.utilities.reader import Read
from hdx.scraper.hapi.datasets import Datasets
from hdx.scraper.hapi.subcategory_reader import SubcategoryReader
from hdx.utilities.compare import assert_files_same
from hdx.utilities.path import script_dir_plus_file, temp_dir
from hdx.utilities.useragent import UserAgent

from .country_results import result_country_dataset, result_country_resources
from .subcategory_results import (
    results_subcategory_datasets,
    results_subcategory_resources,
)

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
        ) as temp_folder:
            Read.create_readers(
                temp_folder,
                fixtures_dir,
                temp_folder,
                False,
                True,
            )
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
                countryiso3s = subcategory_reader.read_countries()
                datasets = Datasets(temp_folder, configuration, countryiso3s)
                # Generate test subcategory results by uncommenting the
                # commented lines. You will need to comment the asserts.
                # ds = {}
                # dsr = {}
                for subcategory in subcategories:
                    subcategory_reader.get_subcategory(subcategory, datasets)
                    subcategory_dataset = datasets.get_subcategory_dataset(
                        subcategory
                    )
                    dataset = subcategory_dataset.get_dataset()
                    # ds[subcategory] = dataset
                    # dsr[subcategory] = dataset.get_resources()
                    assert dataset == results_subcategory_datasets[subcategory]
                    assert (
                        dataset.get_resources()
                        == results_subcategory_resources[subcategory]
                    )
                    filename = f"hdx_hapi_{subcategory}_global.csv"
                    expected_file = join(fixtures_dir, filename)
                    actual_file = join(temp_folder, filename)
                    assert_files_same(expected_file, actual_file)
                for countryiso3 in countryiso3s:
                    country_dataset = datasets.get_country_dataset(countryiso3)
                    dataset = country_dataset.get_dataset()
                    assert dataset == result_country_dataset
                    assert dataset.get_resources() == result_country_resources
                    for subcategory in subcategories:
                        filename = f"hdx_hapi_{subcategory}_afg.csv"
                        expected_file = join(fixtures_dir, filename)
                        actual_file = join(temp_folder, filename)
                        assert_files_same(expected_file, actual_file)
            finally:
                database.cleanup()
