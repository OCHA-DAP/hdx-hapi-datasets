import logging
from os.path import join

import pytest
from hapi_schema.views import prepare_hapi_views

from hdx.database import Database
from hdx.database.dburi import get_params_from_connection_uri
from hdx.database.postgresql import PostgresError
from hdx.scraper.framework.utilities.reader import Read
from hdx.scraper.hapi.datasets import Datasets
from hdx.scraper.hapi.subcategory_reader import SubcategoryReader
from hdx.utilities.compare import assert_files_same
from hdx.utilities.path import temp_dir

from .country_results import result_country_dataset, result_country_resources
from .subcategory_results import (
    results_subcategory_datasets,
    results_subcategory_resources,
)

logger = logging.getLogger(__name__)


class TestHDXHAPIDatasets:
    @pytest.fixture(scope="function")
    def input_database(self, input_dir):
        return join(input_dir, "hapi_db.pg_restore.xz")

    @pytest.fixture(scope="function")
    def db_uri(self):
        return "postgresql+psycopg://postgres:postgres@localhost:5432/hapirestoretest"

    def test_main(
        self,
        configuration,
        fixtures_dir,
        input_dir,
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
                input_dir,
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
                    subcategory_dataset = datasets.get_subcategory_dataset(subcategory)
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
                country_dataset = datasets.get_country_dataset("AFG")
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
