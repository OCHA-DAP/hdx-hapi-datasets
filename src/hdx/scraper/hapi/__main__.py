"""Entry point to start HAPI pipelines"""

import argparse
import logging
from os import getenv
from os.path import expanduser, join
from typing import Optional

from hapi_schema.views import prepare_hapi_views

from hdx.api.configuration import Configuration
from hdx.database import Database
from hdx.database.dburi import (
    get_params_from_connection_uri,
)
from hdx.database.postgresql import PostgresError
from hdx.facades.keyword_arguments import facade
from hdx.utilities.dictandlist import args_to_dict
from hdx.utilities.downloader import Download
from hdx.utilities.path import (
    script_dir_plus_file,
    wheretostart_tempdir_batch,
)
from hdx.utilities.retriever import Retrieve

from ._version import __version__
from .country_dataset import CountryDataset
from .subcategory_reader import SubcategoryReader

logger = logging.getLogger(__name__)


lookup = "hdx-hapi-datasets"
updated_by_script = "HDX Scraper: HAPI Datasets"


def parse_args():
    parser = argparse.ArgumentParser(description="HDX HAPI dataset pipeline")
    parser.add_argument(
        "-db", "--db-uri", default=None, help="Database connection string"
    )
    parser.add_argument(
        "-dp",
        "--db-params",
        default=None,
        help="Database connection parameters. Overrides --db-uri.",
    )
    parser.add_argument(
        "-ru",
        "--restore_url",
        default=None,
        help="URL from which to restore database",
    )
    parser.add_argument(
        "-s",
        "--save",
        default=False,
        action="store_true",
        help="Save data for testing",
    )
    parser.add_argument(
        "-usv",
        "--use-saved",
        default=False,
        action="store_true",
        help="Use saved data",
    )
    return parser.parse_args()


def main(
    restore_url: str,
    db_uri: Optional[str] = None,
    db_params: Optional[str] = None,
    save: bool = False,
    use_saved: bool = False,
    **ignore,
) -> None:
    """Run HAPI. Either a database connection string (db_uri) or database
    connection parameters (db_params) can be supplied. If neither is supplied,
    a local Postgres database "localhost:5432/hapirestore" is assumed.

    Args:
        restore_url (str): URL from which to restore database.
        db_uri (Optional[str]): Database connection URI. Defaults to None.
        db_params (Optional[str]): Database connection parameters. Defaults to None.
        save (bool): Whether to save state for testing. Defaults to False.
        use_saved (bool): Whether to use saved state for testing. Defaults to False.

    Returns:
        None
    """
    logger.info(f"##### {lookup} version {__version__} ####")
    configuration = Configuration.read()
    if db_params:
        params = args_to_dict(db_params)
    else:
        if not db_uri:
            db_uri = configuration["default_db_uri"]
        params = get_params_from_connection_uri(db_uri)
    with wheretostart_tempdir_batch(lookup) as info:
        folder = info["folder"]
        batch = info["batch"]
        with Download() as downloader:
            retriever = Retrieve(
                downloader,
                folder,
                "saved_data",
                folder,
                save,
                use_saved,
            )
            path = retriever.download_file(restore_url)
            if "pg_restore_file" not in params:
                params["pg_restore_file"] = path
            if "prepare_fn" not in params:
                params["prepare_fn"] = prepare_hapi_views
            logger.info(f"> Database parameters: {params}")
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
                #for countryiso3 in subcategory_reader.get_all_countries():
                for countryiso3 in ["LBN"]:
                    country_dataset = CountryDataset(
                        folder, configuration, countryiso3
                    )
                    for _, subcategory_info in subcategories.items():
                        subcategory_reader.view_by_location(
                            country_dataset, subcategory_info, countryiso3
                        )

                    dataset = country_dataset.get_dataset()
                    if dataset:
                        dataset.update_from_yaml(
                            script_dir_plus_file(
                                join("config", "hdx_dataset_static.yaml"),
                                main,
                            )
                        )
                        dataset.create_in_hdx(
                            remove_additional_resources=True,
                            hxl_update=False,
                            updated_by_script=updated_by_script,
                            batch=batch,
                        )

            finally:
                database.cleanup()
    logger.info("HDX HAPI datasets completed!")


if __name__ == "__main__":
    args = parse_args()
    db_uri = args.db_uri
    if db_uri is None:
        db_uri = getenv("DB_URI")
    if db_uri and "://" not in db_uri:
        db_uri = f"postgresql://{db_uri}"
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=lookup,
        project_config_yaml=script_dir_plus_file(
            join("config", "project_configuration.yaml"), main
        ),
        restore_url=args.restore_url,
        db_uri=db_uri,
        db_params=args.db_params,
        save=args.save,
        use_saved=args.use_saved,
    )
