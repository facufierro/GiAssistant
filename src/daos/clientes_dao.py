# path: src/daos/clientes_dao.py
import logging
from pymongo.errors import PyMongoError
from pymongo.results import InsertOneResult
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

    def get_all(self) -> Optional[List[Dict]]:
        try:
            # Return a list of all clients, excluding the MongoDB _id field
            result = list(self.db['clientes'].find({}, {"_id": 0}))
            return result
        except PyMongoError as e:
            logging.error(f"Error getting all clients: {e}")
            return None
