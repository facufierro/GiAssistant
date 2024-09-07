# path: src/daos/db_manager.py
import pymongo
import os
import logging
from pymongo.errors import PyMongoError, ConfigurationError
from pymongo.database import Database, Collection
from dotenv import load_dotenv

load_dotenv()


class DBManager:
    def __init__(self) -> None:
        try:
            MONGO_URI: str = os.getenv('MONGO_URI')
            if not MONGO_URI:
                raise ConfigurationError("MONGO_URI environment variable is not set.")

            self.client: pymongo.MongoClient = pymongo.MongoClient(MONGO_URI)
            self.db: Database = self.client["dev"]

        except ConfigurationError as ce:
            logging.error(f"Configuration error: {ce}")
            raise
        except PyMongoError as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred during DBManager initialization: {e}")
            raise

    def get_collection(self, collection_name: str) -> Collection:
        try:
            return self.db[collection_name]
        except PyMongoError as e:
            logging.error(f"Failed to retrieve collection '{collection_name}': {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while retrieving collection '{collection_name}': {e}")
            raise
