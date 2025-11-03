from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os, datetime, uuid

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tienda.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(120), unique=True, nullable=False)
    correo = db.Column(db.String(200), unique=True, nullable=False)
    contrasena = db.Column(db.String(256), nullable=False)
    telefono = db.Column(db.String(50))
    direccion = db.Column(db.String(300))
    fecha_registro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    def to_dict(self):
        return { "id": self.id, "nombre_usuario": self.nombre_usuario, "correo": self.correo, "telefono": self.telefono, "direccion": self.direccion }

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.String(500))
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    def to_dict(self):
        return { "id": self.id, "nombre": self.nombre, "descripcion": self.descripcion, "precio": self.precio, "stock": self.stock, "imagen": self.imagen }

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    total = db.Column(db.Float, default=0.0)
    direccion_envio = db.Column(db.String(300))
    estado = db.Column(db.String(50), default="PENDIENTE")
    fecha = db.Column(db.DateTime, default=datetime.datetime.utcnow)
class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_snapshot = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto')
Pedido.items = db.relationship('PedidoItem', backref='pedido', lazy=True)


def obtener_campo(datos, *posibles):
    for p in posibles:
        if p in datos and datos[p] is not None:
            return datos[p]
    return None


@app.route('/')
def root():
    index_path = os.path.join(BASE_DIR, 'static', 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(os.path.join(BASE_DIR, 'static'), 'index.html')
    return jsonify({
        "mensaje": "API Tienda - Restaurante arabe",
        "endpoints": [
            "/api/registro (POST)",
            "/register (alias)",
            "/api/login (POST)",
            "/login (alias)",
            "/api/productos (GET)",
            "/api/pedidos (POST/GET)",
            "/api/historial/<id_usuario> (GET)"
        ]
    })


@app.route('/api/registro', methods=['POST'])
@app.route('/register', methods=['POST'])
def registro():
    datos = request.get_json() or {}
    nombre_usuario = obtener_campo(datos, 'nombre_usuario', 'username')
    correo = obtener_campo(datos, 'correo', 'email')
    contrasena = obtener_campo(datos, 'contrasena', 'password')
    telefono = datos.get('telefono') or datos.get('phone')
    direccion = datos.get('direccion') or datos.get('address')
    if not (nombre_usuario and correo and contrasena):
        return jsonify({"error": "Faltan datos: nombre_usuario/correo/contrasena"}), 400
    if Usuario.query.filter((Usuario.correo==correo)|(Usuario.nombre_usuario==nombre_usuario)).first():
        return jsonify({"error": "Usuario o correo ya registrado"}), 400
    usuario = Usuario(nombre_usuario=nombre_usuario, correo=correo, telefono=telefono, direccion=direccion, contrasena=generate_password_hash(contrasena))
    db.session.add(usuario); db.session.commit()
    return jsonify({"mensaje": "Usuario registrado", "usuario": usuario.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
@app.route('/login', methods=['POST'])
def login():
    datos = request.get_json() or {}
    correo = obtener_campo(datos, 'correo', 'email')
    contrasena = obtener_campo(datos, 'contrasena', 'password')
    if not (correo and contrasena):
        return jsonify({"error":"Faltan correo/contrasena"}), 400
    usuario = Usuario.query.filter((Usuario.correo==correo)|(Usuario.nombre_usuario==correo)).first()
    if not usuario or not check_password_hash(usuario.contrasena, contrasena):
        return jsonify({"error":"Credenciales incorrectas"}), 401
    return jsonify({"mensaje":"Login correcto", "usuario": usuario.to_dict(), "id_usuario": usuario.id}), 200

@app.route('/api/recuperar', methods=['POST'])
def recuperar():
    datos = request.get_json() or {}
    correo = obtener_campo(datos, 'correo', 'email')
    if not correo:
        return jsonify({"error":"Enviar correo"}), 400
    usuario = Usuario.query.filter_by(correo=correo).first()

    return jsonify({"mensaje":"Si el correo existe, se enviarán instrucciones"}), 200


@app.route('/api/productos', methods=['GET'])
@app.route('/products', methods=['GET'])
def listar_productos():
    return jsonify([p.to_dict() for p in Producto.query.order_by(Producto.created_at.desc()).all()])

@app.route('/api/productos', methods=['POST'])
@app.route('/products', methods=['POST'])
def crear_producto():
    datos = request.get_json() or {}
    nombre = obtener_campo(datos, 'nombre', 'name')
    precio = obtener_campo(datos, 'precio', 'price')
    descripcion = datos.get('descripcion', '')
    stock = int(datos.get('stock', 0))
    imagen = datos.get('imagen', '')
    if not nombre or precio is None:
        return jsonify({"error":"nombre y precio obligatorios"}), 400
    p = Producto(nombre=nombre, descripcion=descripcion, precio=float(precio), stock=stock, imagen=imagen)
    db.session.add(p); db.session.commit()
    return jsonify({"mensaje":"Producto creado", "producto": p.to_dict()}), 201


@app.route('/api/pedidos', methods=['POST'])
@app.route('/cart', methods=['POST'])
def crear_pedido():
    datos = request.get_json() or {}
    items = datos.get('items') or datos.get('carrito') or datos.get('cart')
    id_usuario = obtener_campo(datos, 'id_usuario', 'user_id', 'usuario_id')
    direccion = datos.get('direccion', datos.get('direccion_envio', ''))
    if not items or not id_usuario:
        return jsonify({"error":"Se requieren items y id_usuario"}), 400
    usuario = Usuario.query.get(int(id_usuario))
    if not usuario:
        return jsonify({"error":"Usuario no encontrado"}), 404
    pedido = Pedido(id_usuario=usuario.id, direccion_envio=direccion)
    db.session.add(pedido); db.session.flush()
    total = 0.0
    for it in items:
        pid = obtener_campo(it, 'producto_id', 'id', 'product_id')
        cantidad = obtener_campo(it, 'cantidad', 'qty', 'quantity') or 1
        producto = Producto.query.get(int(pid))
        if not producto:
            db.session.rollback(); return jsonify({"error":f"Producto {pid} no encontrado"}), 404
        if producto.stock is not None and producto.stock < int(cantidad):
            db.session.rollback(); return jsonify({"error":f"No hay stock suficiente para {producto.nombre}"}), 400
        if producto.stock is not None:
            producto.stock -= int(cantidad)
        item = PedidoItem(pedido_id=pedido.id, producto_id=producto.id, cantidad=int(cantidad), precio_snapshot=float(producto.precio))
        db.session.add(item)
        total += float(producto.precio) * int(cantidad)
    pedido.total = total
    db.session.commit()
    return jsonify({"mensaje":"Pedido creado", "pedido_id": pedido.id, "codigo": pedido.codigo}), 201

@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    usuario_q = request.args.get('usuario')
    admin_q = request.args.get('admin')
    if admin_q == '1':
        pedidos = Pedido.query.order_by(Pedido.fecha.desc()).all()
    elif usuario_q:
        pedidos = Pedido.query.filter_by(id_usuario=int(usuario_q)).order_by(Pedido.fecha.desc()).all()
    else:
        pedidos = Pedido.query.order_by(Pedido.fecha.desc()).limit(50).all()
    salida = []
    for p in pedidos:
        items = []
        for it in p.items:
            items.append({"producto": it.producto.nombre, "cantidad": it.cantidad, "precio_snapshot": it.precio_snapshot})
        salida.append({"id": p.id, "codigo": p.codigo, "id_usuario": p.id_usuario, "total": p.total, "direccion_envio": p.direccion_envio, "estado": p.estado, "fecha": p.fecha.isoformat(), "items": items})
    return jsonify(salida)

@app.route('/api/historial/<int:id_usuario>', methods=['GET'])
def historial(id_usuario):
    pedidos = Pedido.query.filter_by(id_usuario=id_usuario).order_by(Pedido.fecha.desc()).all()
    respuesta = []
    for p in pedidos:
        respuesta.append({"id": p.id, "codigo": p.codigo, "total": p.total, "fecha": p.fecha.isoformat()})
    return jsonify(respuesta)


@app.route('/static/<path:filename>')
def servir_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)


with app.app_context():
    db.create_all()
    if Producto.query.count() == 0:
        ejemplos = [
            Producto(nombre="Shawarma", descripcion="Carne con especias", precio=6000, stock=10, imagen=""),
            Producto(nombre="Falafel", descripcion="Bolas de garbanzo", precio=4500, stock=15, imagen=""),
            Producto(nombre="Hummus", descripcion="Puré de garbanzos", precio=3000, stock=20, imagen="")
        ]
        db.session.bulk_save_objects(ejemplos); db.session.commit()

if __name__ == '__main__':
    print("Iniciando API. DB:", os.path.join(BASE_DIR, 'tienda.db'))
    app.run(debug=True)
