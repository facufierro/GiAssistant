# path: src/daos/clientes_dao.py
import logging
from pymongo.errors import PyMongoError
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId  # Import ObjectId to work with MongoDB _id
from typing import Optional, List, Dict
from src.models.cliente import Cliente
from .db_manager import DBManager


class ClientesDAO(DBManager):
    def __init__(self) -> None:
        try:
            super().__init__()
        except Exception as e:
            logging.error(f"An error occurred during ClientesDAO initialization: {e}")
            raise

    def create_one(self, cliente: Cliente) -> Optional[InsertOneResult]:
        try:
            result = self.db['clientes'].insert_one({
                "id_fiscal": cliente.id_fiscal,
                "razon_social": cliente.razon_social,
                "nombre": cliente.nombre,
                "apellido": cliente.apellido,
                "direccion": cliente.direccion,
                "telefono": cliente.telefono,
                "mail": cliente.mail,
                "categoria_fiscal": cliente.categoria_fiscal
            })
            return result
        except PyMongoError as e:
            logging.error(f"Error creating Cliente: {e}")
            return None

    def get_one(self, client_id: str) -> Optional[Dict]:
        try:
            result = self.db['clientes'].find_one({"_id": ObjectId(client_id)})  # Use ObjectId for _id
            return result
        except PyMongoError as e:
            logging.error(f"Error getting Cliente: {e}")
            return None

    def get_all(self) -> Optional[List[Dict]]:
        try:
            # Return a list of all clients, including the MongoDB _id field
            result = list(self.db['clientes'].find({}))
            return result
        except PyMongoError as e:
            logging.error(f"Error getting all clients: {e}")
            return None

    def update_one(self, client_id: str, cliente: Cliente) -> bool:
        try:
            result = self.db['clientes'].update_one(
                {"_id": ObjectId(client_id)},  # Use ObjectId for _id
                {"$set": {
                    "id_fiscal": cliente.id_fiscal,
                    "razon_social": cliente.razon_social,
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido,
                    "direccion": cliente.direccion,
                    "telefono": cliente.telefono,
                    "mail": cliente.mail,
                    "categoria_fiscal": cliente.categoria_fiscal
                }}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logging.error(f"Error updating Cliente: {e}")
            return False

    def delete_one(self, client_id: str) -> bool:
        try:
            result = self.db['clientes'].delete_one({"_id": ObjectId(client_id)})  # Use ObjectId for _id
            return result.deleted_count > 0
        except PyMongoError as e:
            logging.error(f"Error deleting Cliente: {e}")
            return False
