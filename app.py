from flask_cors import CORS
from flask import Flask, request
from flask_pymongo import PyMongo, ObjectId
from flask.json import jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime

app = Flask(__name__)
app.config['MONGO_URI']='mongodb+srv://pass123:pass123@cluster0.hmc2h.mongodb.net/examenWEB?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE'
# &ssl=true&ssl_cert_reqs=CERT_NONE
CORS(app)

    # Creamos la conexión
mongo = PyMongo(app)
usuarios = mongo.db.usuarios
articulos = mongo.db.articulos
pujas = mongo.db.pujas

cloudinary.config( 
  cloud_name = "webfgp", 
  api_key = "512441435645679", 
  api_secret = "mngOOhQ5nU_zfZjqj6I2Q6lUVUg" 
)

#################################################################################################################################
CLIENT_ID = "821030033510-lcn1p8r2bbidgcib19fln358pqvc9f4o.apps.googleusercontent.com"

@app.route('/api/google-login', methods=['POST'])
def login():
    token = request.json['token']
    res = None
    try:
        id = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        
        # Comprobar si el usuario está en la BD
        resultado = usuarios.find_one({"email" : id['email']})
        if resultado is None:
            resultado = usuarios.insert_one({
                "nombre": str(id["name"]),
                "email": str(id["email"]),
            })
            idRes = str(resultado.inserted_id)
        else:
            idRes = str(resultado['_id'])
        res = {'email':id['email'], 'name':id['name'], 'id':idRes, 'token':token}
        return jsonify(res)
    except ValueError:
        print("Token no valido")
        pass # Token no valido
    return jsonify(res)


@app.route('/subirFoto', methods=['POST'])
def subirFoto():
    foto = request.files['file']
    res = cloudinary.uploader.upload(foto)
    url = res["url"]
    return jsonify({"url":url})
#################################################################################################################################

@app.route('/articulos', methods=['POST'])
def añadirArticulo():
    datos = request.get_json()
    token = request.headers["Authorization"].split(' ')[1]
    if (id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)):
        idArticulo = articulos.insert_one({
            "vendedor": str(datos["vendedor"]),
            "descripcion": str(datos["descripcion"]),
            "precio_salida": datos["precio_salida"],
            "imagenes": str(datos["imagenes"]),
            "comprador": "null"
        })
        return jsonify(msg="Articulo añadido", new_id=str(idArticulo.inserted_id))
    else:
        return jsonify(msg="Token no válido")
    
    
@app.route('/articulos', methods=['GET'])
def getArticulos():
    resultado = []
    for d in articulos.find():
        d["_id"] = str(d["_id"])
        # Puja mayor
        res = 0
        for p in pujas.find({"identificador": d["_id"]}).sort("cantidad_ofrecida", -1):
            res = p["cantidad_ofrecida"]
            break
        d["pujaMayor"] = str(res)
        resultado.append(d)
    return jsonify(resultado)
    

@app.route('/pujar', methods=['POST'])
def pujar():
    datos = request.get_json()
    token = request.headers["Authorization"].split(' ')[1]
    if (id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)):
        # Añadir nueva puja
        now = datetime.now()
        idPuja = pujas.insert_one({
            "identificador": str(ObjectId(datos["identificador"])),
            "comprador": str(datos["comprador"]),
            "timestamp": str(now.strftime("%d/%m/%Y %H:%M")),
            "cantidad_ofrecida": datos["cantidad_ofrecida"],
        })
        return jsonify(msg="Puja añadida", new_id=str(idPuja.inserted_id))
    else:
        return jsonify(msg="Token no válido")


@app.route('/pujaMasAlta/<id>', methods=['GET'])
def getPujaMayor(id):
    token = request.headers["Authorization"].split(' ')[1]
    if (id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)):
        res = "None"
        for p in pujas.find({"identificador": id}).sort("cantidad_ofrecida", -1):
            res = p["cantidad_ofrecida"]
            break
        return jsonify(msg=res)
    else:
        return jsonify(msg="Token no válido")
    

if __name__ == "__main__":
    app.run(debug=True)