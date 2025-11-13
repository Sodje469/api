import os
import datetime
import jwt
import random
import string
from functools import wraps
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mi_clave_secreta_muy_segura_12345'
CORS(app)


usuarios = [
  { 
    "id": 1, 
    "email": "ana@example.com", 
    "password": "Clave2025", 
    "nombre": "Ana", 
    "apellidos": "García", 
    "intentos": 0, 
    "bloqueado": False,
    "rol": "admin" 
  },
  { 
    "id": 2, 
    "email": "cliente@example.com", 
    "password": "Cliente123", 
    "nombre": "Juan", 
    "apellidos": "Pérez", 
    "intentos": 0, 
    "bloqueado": False,
    "rol": "cliente"
  }
]
siguiente_id_usuario = 3

productos = [
  { "id": 1, "nombre": 'Hummus Tradicional', "descripcion": 'Cremoso hummus con tahini y aceite de oliva', "precio": 12990, "categoria": 'Aperitivos', "stock": 20, "imagen": 'https://buenprovecho.hn/wp-content/uploads/2022/12/Untitled-design.jpg' },
  { "id": 2, "nombre": 'Falafel (6 piezas)', "descripcion": 'Croquetas de garbanzos fritas con especias', "precio": 15500, "categoria": 'Aperitivos', "stock": 15, "imagen": 'https://th.bing.com/th/id/R.6d095ab49b5567e43f97e0321c6f6386?rik=RtQFiNVPOn%2fGWg&riu=http%3a%2f%2fcookingtheglobe.com%2fwp-content%2fuploads%2f2016%2f02%2fhow-to-make-falafel-4.jpg&ehk=dOfF7GCgvI6fOL95jzjmE6QTdo2VOcW%2fDoM%2b0TfUeG4%3d&risl=&pid=ImgRaw&r=0' },
  { "id": 3, "nombre": 'Shawarma de Pollo', "descripcion": 'Pollo marinado en pan pita con vegetales', "precio": 18750, "categoria": 'Platos Principales', "stock": 10, "imagen": 'https://i.blogs.es/f03b7f/shawarma/1366_2000.jpg' },
  { "id": 4, "nombre": 'Tabule', "descripcion": 'Ensalada fresca de perejil, tomate y bulgur', "precio": 14250, "categoria": 'Aperitivos', "stock": 12, "imagen": 'https://blog.dia.es/wp-content/uploads/2021/11/tabule-receta.jpg?x90137' },
  { "id": 5, "nombre": 'Kebab de Cordero', "descripcion": 'Brochetas de cordero con especias árabes', "precio": 24900, "categoria": 'Platos Principales', "stock": 8, "imagen": 'https://th.bing.com/th/id/R.ec35ec25cc2504678c871225529ed0d1?rik=F7yj7ohpLptNZw&pid=ImgRaw&r=0' },
  { "id": 6, "nombre": 'Baba Ganoush', "descripcion": 'Puré de berenjenas ahumadas con tahini', "precio": 13500, "categoria": 'Aperitivos', "stock": 14, "imagen": 'https://littlesunnykitchen.com/wp-content/uploads/2014/07/Baba-Ganoush-recipe-12.jpg' },
  { "id": 7, "nombre": 'Mansaf', "descripcion": 'Cordero en salsa de yogurt con arroz', "precio": 28750, "categoria": 'Platos Principales', "stock": 5, "imagen": 'https://www.seriouseats.com/thmb/P1mvGpryoxyKcwnoflRybvXBAd0=/1500x1125/20221208-Mansaf-Mai-Kakish-hero-ec9c515c00d24b5c9ef567854036f044.JPG' },
  { "id": 8, "nombre": 'Kibbeh (4 piezas)', "descripcion": 'Croquetas de bulgur rellenas de carne', "precio": 16250, "categoria": 'Aperitivos', "stock": 10, "imagen": 'https://imag.bonviveur.com/kibbeh-listo-para-comer.jpg' },
  { "id": 9, "nombre": 'Baklava', "descripcion": 'Postre de hojaldre con nueces y miel', "precio": 8500, "categoria": 'Postres', "stock": 30, "imagen": 'https://tse3.mm.bing.net/th/id/OIP.USb085NT0p5ENKGlToC2uwHaFZ?cb=ucfimg2ucfimg=1&rs=1&pid=ImgDetMain&o=7&rm=3' },
  { "id": 10, "nombre": 'Té Árabe', "descripcion": 'Té negro con cardamomo y canela', "precio": 5750, "categoria": 'Bebidas', "stock": 40, "imagen": 'https://img.freepik.com/foto-gratis/te-arabe-vasos-tetera-sobre-tela-roja_23-2148088409.jpg?size=626&ext=jpg' },
]


pedidos = [
  { "numero": 101, "cliente_email": "cliente@example.com", "fecha": "2025-10-01", "estado": "Entregada", 
    "productos": [
        {"id": 1, "nombre": "Hummus Tradicional", "cantidad": 2, "precio_unitario": 12990},
        {"id": 2, "nombre": "Falafel (6 piezas)", "cantidad": 1, "precio_unitario": 15500}
    ], 
    "total": (12990 * 2) + 15500
  },
  { "numero": 102, "cliente_email": "ana@example.com", "fecha": "2025-10-02", "estado": "En Preparación", 
    "productos": [
        {"id": 3, "nombre": "Shawarma de Pollo", "cantidad": 1, "precio_unitario": 18750},
        {"id": 10, "nombre": "Té Árabe", "cantidad": 2, "precio_unitario": 5750}
    ], 
    "total": 18750 + (5750 * 2)
  },
  { "numero": 103, "cliente_email": "cliente@example.com", "fecha": "2025-10-03", "estado": "Pendiente", 
    "productos": [
        {"id": 5, "nombre": "Kebab de Cordero", "cantidad": 1, "precio_unitario": 24900},
        {"id": 9, "nombre": "Baklava", "cantidad": 1, "precio_unitario": 8500}
    ], 
    "total": 24900 + 8500
  },
]
siguiente_numero_pedido = 104


tokens_recuperacion = {} 


def decorador_token_requerido(f):
    """
    Decorador para verificar que un token JWT válido esté presente.
    """
    @wraps(f)
    def decorado(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            partes = auth_header.split()
            if len(partes) == 2 and partes[0].lower() == 'bearer':
                token = partes[1]

        if not token:
            return jsonify({'mensaje': 'Falta el token de autorización'}), 401

        try:
            
            datos = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            usuario_actual = next((u for u in usuarios if u['id'] == datos['id']), None)
            if not usuario_actual:
                 return jsonify({'mensaje': 'Usuario del token no encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'mensaje': 'El token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'mensaje': 'Token inválido'}), 401

        
        return f(usuario_actual, *args, **kwargs)
    return decorado

def decorador_admin_requerido(f):
   
    @wraps(f)
    def decorado(usuario_actual, *args, **kwargs):
        if usuario_actual['rol'] != 'admin':
            return jsonify({'mensaje': 'Acceso denegado. Se requiere rol de administrador'}), 403
        return f(usuario_actual, *args, **kwargs)
    return decorado


@app.route('/api/auth/registrar', methods=['POST'])
def registrar_usuario():
   
    global siguiente_id_usuario
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({'mensaje': 'Faltan email o contraseña'}), 400

    if any(u['email'] == email for u in usuarios):
        return jsonify({'mensaje': 'El email ya está en uso'}), 409

    if not (len(password) >= 8 and any(c.isupper() for c in password) and any(c.isdigit() for c in password)):
         return jsonify({'mensaje': 'La contraseña debe tener al menos 8 caracteres, una mayúscula y un número'}), 400

    nuevo_usuario = {
        "id": siguiente_id_usuario,
        "email": email,
        "password": password,
        "nombre": "Nuevo",
        "apellidos": "Usuario",
        "intentos": 0,
        "bloqueado": False,
        "rol": "cliente" 
    }
    usuarios.append(nuevo_usuario)
    siguiente_id_usuario += 1
    
    return jsonify({'mensaje': 'Usuario registrado con éxito'}), 201

@app.route('/api/auth/login', methods=['POST'])
def login_usuario():
    
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({'mensaje': 'Faltan email o contraseña'}), 400

    usuario = next((u for u in usuarios if u['email'] == email), None)

    if not usuario:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404

    if usuario['bloqueado']:
        return jsonify({'mensaje': 'Cuenta temporalmente bloqueada'}), 403

    if usuario['password'] == password:
        
        usuario['intentos'] = 0
        
        
        token = jwt.encode({
            'id': usuario['id'],
            'email': usuario['email'],
            'rol': usuario['rol'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            'mensaje': 'Inicio de sesión exitoso',
            'token': token,
            'usuario': {
                'email': usuario['email'],
                'nombre': usuario['nombre'],
                'rol': usuario['rol']
            }
        }), 200
    else:
        usuario['intentos'] += 1
        if usuario['intentos'] >= 5:
            usuario['bloqueado'] = True
            return jsonify({'mensaje': 'Cuenta temporalmente bloqueada'}), 403
        else:
            return jsonify({'mensaje': f'Credenciales incorrectas (intento {usuario["intentos"]}/5)'}), 401

@app.route('/api/auth/recuperar/solicitar', methods=['POST'])
def solicitar_token_recuperacion():
   
    email = request.json.get('email')
    if not email or not any(u['email'] == email for u in usuarios):
        return jsonify({'mensaje': 'Email no encontrado'}), 404
        
    
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    expiracion = datetime.datetime.utcnow() + datetime.timedelta(minutes=20) 
    
    tokens_recuperacion[email] = {
        "token": token,
        "expira": expiracion
    }
    
    
    print(f"Token para {email}: {token}") 
    return jsonify({'mensaje': f'Se ha enviado un token (simulado) a {email}.', 'token_simulado': token}), 200

@app.route('/api/auth/recuperar/validar', methods=['POST'])
def validar_token_y_cambiar_clave():
    
    datos = request.json
    email = datos.get('email')
    token_ingresado = datos.get('token')
    nueva_clave = datos.get('nueva_clave')

    if not email or not token_ingresado or not nueva_clave:
        return jsonify({'mensaje': 'Faltan datos (email, token, nueva_clave)'}), 400

    token_info = tokens_recuperacion.get(email)

    if not token_info or token_info['token'] != token_ingresado:
        return jsonify({'mensaje': 'Token incorrecto'}), 400
    
    if datetime.datetime.utcnow() > token_info['expira']:
        del tokens_recuperacion[email] 
        return jsonify({'mensaje': 'El token ha expirado'}), 400

    
    usuario = next((u for u in usuarios if u['email'] == email), None)
    if usuario:
        usuario['password'] = nueva_clave
        usuario['intentos'] = 0
        usuario['bloqueado'] = False
        del tokens_recuperacion[email] # Token usado
        return jsonify({'mensaje': 'Contraseña restablecida con éxito'}), 200
    else:
        return jsonify({'mensaje': 'Error al encontrar el usuario'}), 500


@app.route('/api/productos', methods=['GET'])
def obtener_productos():
    
    categoria_filtro = request.args.get('categoria')
    
    if categoria_filtro:
        productos_filtrados = [p for p in productos if p['categoria'] == categoria_filtro]
    else:
        productos_filtrados = productos
        
    return jsonify(productos_filtrados), 200

@app.route('/api/productos/<int:id_producto>', methods=['GET'])
def obtener_producto_por_id(id_producto):
    
    producto = next((p for p in productos if p['id'] == id_producto), None)
    if producto:
        return jsonify(producto), 200
    else:
        return jsonify({'mensaje': 'Producto no encontrado'}), 404


@app.route('/api/usuario/perfil', methods=['GET'])
@decorador_token_requerido
def obtener_perfil_usuario(usuario_actual):
   

    perfil = {
        "nombre": usuario_actual['nombre'],
        "apellidos": usuario_actual['apellidos'],
        "email": usuario_actual['email'],
    }
    
    return jsonify(perfil), 200

@app.route('/api/usuario/historial-pedidos', methods=['GET'])
@decorador_token_requerido
def obtener_historial_pedidos(usuario_actual):
    
    email_usuario = usuario_actual['email']
    pedidos_usuario = [p for p in pedidos if p['cliente_email'] == email_usuario]
    
    
    historial_formateado = [
        {
            "id": p['numero'],
            "items": [item['nombre'] for item in p['productos']],
            "total": p['total'],
            "fecha": p['fecha']
        }
        for p in pedidos_usuario
    ]
    return jsonify(historial_formateado), 200

@app.route('/api/pedidos/crear', methods=['POST'])
@decorador_token_requerido
def crear_pedido(usuario_actual):
   
    global siguiente_numero_pedido
    datos = request.json
    items_carrito = datos.get('items') 
    
    if not items_carrito:
        return jsonify({'mensaje': 'El carrito está vacío'}), 400

    productos_pedido = []
    total_calculado = 0
    
    try:
        for item in items_carrito:
            producto = next((p for p in productos if p['id'] == item['id']), None)
            if not producto:
                return jsonify({'mensaje': f'Producto ID {item["id"]} no encontrado'}), 404
            
            cantidad = int(item['cantidad'])
            if producto['stock'] < cantidad:
                return jsonify({'mensaje': f'Stock insuficiente para {producto["nombre"]}'}), 409
                
            
            productos_pedido.append({
                "id": producto['id'],
                "nombre": producto['nombre'],
                "cantidad": cantidad,
                "precio_unitario": producto['precio']
            })
            total_calculado += producto['precio'] * cantidad

    except (KeyError, TypeError, ValueError):
        return jsonify({'mensaje': 'Formato de items incorrecto. Se espera [{"id": X, "cantidad": Y}, ...]'}), 400

    nuevo_pedido = {
        "numero": siguiente_numero_pedido,
        "cliente_email": usuario_actual['email'],
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
        "estado": "Pendiente", 
        "productos": productos_pedido,
        "total": total_calculado
    }
    
    pedidos.append(nuevo_pedido)
    siguiente_numero_pedido += 1
    
    return jsonify({'mensaje': 'Pedido creado con éxito', 'pedido': nuevo_pedido}), 201


@app.route('/api/admin/usuarios', methods=['GET'])
@decorador_token_requerido
@decorador_admin_requerido
def admin_obtener_usuarios(usuario_actual):
   
    
    lista_usuarios = [
        {"email": u['email'], "nombre": u['nombre'], "rol": u['rol']}
        for u in usuarios
    ]
    return jsonify(lista_usuarios), 200

@app.route('/api/admin/usuarios/crear', methods=['POST'])
@decorador_token_requerido
@decorador_admin_requerido
def admin_crear_usuario(usuario_actual):
    
    global siguiente_id_usuario
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({'mensaje': 'Faltan email o contraseña'}), 400

    if any(u['email'] == email for u in usuarios):
        return jsonify({'mensaje': 'El email ya está en uso'}), 409

    nuevo_usuario = {
        "id": siguiente_id_usuario,
        "email": email,
        "password": password,
        "nombre": "Nuevo (Admin)",
        "apellidos": "Creado",
        "intentos": 0,
        "bloqueado": False,
        "rol": "cliente" 
    }
    usuarios.append(nuevo_usuario)
    siguiente_id_usuario += 1
    
    return jsonify({'mensaje': 'Usuario creado con éxito por admin', 'usuario': {"email": email}}), 201

@app.route('/api/admin/reporte-ventas', methods=['GET'])
@decorador_token_requerido
@decorador_admin_requerido
def admin_reporte_ventas(usuario_actual):
    
    reporte = []
    ingresos_totales = 0
    
    for p in pedidos:
        nombres_productos = ", ".join([item['nombre'] for item in p['productos']])
        cantidades = sum(item['cantidad'] for item in p['productos'])
        reporte.append({
            "numero_venta": p['numero'],
            "productos": nombres_productos,
            "cantidad": cantidades,
            "total": p['total']
        })
        ingresos_totales += p['total']
        
    return jsonify({
        "reporte": reporte,
        "ingresos_totales": ingresos_totales
    }), 200

@app.route('/api/admin/metricas', methods=['GET'])
@decorador_token_requerido
@decorador_admin_requerido
def admin_metricas_ventas(usuario_actual):
    
    
    ventas_por_pedido = {
        "labels": [f"Venta #{p['numero']}" for p in pedidos],
        "data": [p['total'] for p in pedidos]
    }
    
    
    conteo_productos = {}
    for p in pedidos:
        for item in p['productos']:
            nombre = item['nombre']
            cantidad = item['cantidad']
            conteo_productos[nombre] = conteo_productos.get(nombre, 0) + cantidad
            
    
    productos_mas_vendidos = sorted(conteo_productos.items(), key=lambda x: x[1], reverse=True)
    
    productos_mas_vendidos_lista = [f"{nombre}: {cant} unidades" for nombre, cant in productos_mas_vendidos]
    
    return jsonify({
        "ventas_por_pedido": ventas_por_pedido,
        "productos_mas_vendidos": productos_mas_vendidos_lista
    }), 200

@app.route('/api/admin/ordenes-despacho', methods=['GET'])
@decorador_token_requerido
@decorador_admin_requerido
def admin_ordenes_despacho(usuario_actual):
    
    ordenes_por_estado = {
        "pendientes": [],
        "preparacion": [],
        "camino": [],
        "entregadas": []
    }
    
    
    lista_completa_ordenes = []
    
    for p in pedidos:
        
        lista_completa_ordenes.append({
            "cliente": p['cliente_email'],
            "ubicacion": "Simulada", 
            "total": p['total'],
            "estado": p['estado']
        })
        
        
        orden_simple = f"Pedido #{p['numero']} - {p['cliente_email']}"
        
        if p['estado'] == 'Pendiente':
            ordenes_por_estado['pendientes'].append(orden_simple)
        elif p['estado'] == 'En Preparación':
            ordenes_por_estado['preparacion'].append(orden_simple)
        elif p['estado'] == 'En Camino':
            ordenes_por_estado['camino'].append(orden_simple)
        elif p['estado'] == 'Entregada':
            ordenes_por_estado['entregadas'].append(orden_simple)
            
    return jsonify({
        "tarjetas_estado": ordenes_por_estado,
        "tabla_ordenes": lista_completa_ordenes
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
