# path: src/controllers/clientes_controller.py
from flask import Blueprint, request, jsonify, make_response, render_template, redirect, url_for
from src.models.cliente import Cliente
from src.daos.clientes_dao import ClientesDAO
from bson.objectid import ObjectId

client_blueprint = Blueprint('clientes', __name__, url_prefix='/gestal')
clientes_dao = ClientesDAO()


@client_blueprint.route('/clientes', methods=['GET'])
def index():
    clients = clientes_dao.get_all()

    if clients is None:
        return make_response(jsonify({"message": "Error fetching clients"}), 500)

    return render_template('clientes.html', clients=clients)


@client_blueprint.route('/clientes/<client_id>', methods=['GET'])
def get_one(client_id):
    client = clientes_dao.get_one(client_id)

    if client is None:
        return make_response(jsonify({"message": "Error fetching client"}), 500)

    return render_template('cliente.html', client=client)


@client_blueprint.route('/clientes/create_one', methods=['POST'])
def create_one():
    data = request.form

    if not all(key in data for key in ['razon_social', 'nombre', 'apellido', 'direccion', 'telefono', 'mail', 'categoria_fiscal']):
        return make_response(jsonify({"message": "Missing required fields"}), 400)

    cliente = Cliente(
        id_fiscal=data.get('id_fiscal'),  # Optional field
        razon_social=data['razon_social'],
        nombre=data['nombre'],
        apellido=data['apellido'],
        direccion=data['direccion'],
        telefono=data['telefono'],
        mail=data['mail'],
        categoria_fiscal=data['categoria_fiscal']
    )

    insert_result = clientes_dao.create_one(cliente)

    if insert_result and insert_result.inserted_id:
        return redirect(url_for('clientes.index'))
    else:
        return make_response(jsonify({"message": "Failed to create cliente"}), 500)
