# src/models/cliente.py
class Cliente:
    def __init__(self, id_fiscal, razon_social, nombre, apellido, direccion, telefono, mail, categoria_fiscal):
        self.id_fiscal = id_fiscal
        self.razon_social = razon_social
        self.nombre = nombre
        self.apellido = apellido
        self.direccion = direccion
        self.telefono = telefono
        self.mail = mail
        self.categoria_fiscal = categoria_fiscal
