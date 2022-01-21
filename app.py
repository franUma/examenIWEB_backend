from flask_cors import CORS
from flask import Flask, request
from flask_pymongo import PyMongo, ObjectId
from flask.json import jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)
app.config['MONGO_URI']='mongodb+srv://pass123:pass123@cluster0.hmc2h.mongodb.net/examenWEB?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE'
# &ssl=true&ssl_cert_reqs=CERT_NONE
CORS(app)

    # Creamos la conexión
mongo = PyMongo(app)
usuarios = mongo.db.usuarios
photoNet = mongo.db.photoNet

cloudinary.config( 
  cloud_name = "webfgp", 
  api_key = "512441435645679", 
  api_secret = "mngOOhQ5nU_zfZjqj6I2Q6lUVUg" 
)

#################################################################################################################################
CLIENT_ID = "821030033510-0rlhbtj2eaofuc0q6k6lpalg8qj0c5iu.apps.googleusercontent.com"

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


@app.route('/subirFotoBD', methods=['POST'])
def subirFotoBD():
    datos = request.get_json()
    token = request.headers["Authorization"].split(' ')[1]
    if (id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)):
        try:
            foto = photoNet.find_one({"email": str(datos["email"]), 
                                "url": str(datos["url"])})
            if foto is None:
                res = photoNet.insert_one({
                    "email": str(datos["email"]),
                    "descripcion": str(datos["descripcion"]),
                    "url": str(datos["url"]),
                    "likes": 0
                })
                return jsonify(msg="Post creado", new_id=str(res.inserted_id))
            else:
                return jsonify(msg="Foto ya subida")
        except:
            respuesta = jsonify(msg="Petición no válida, faltan campos o no son del tipo correcto")
            return respuesta
    else:
        return jsonify(msg="Token no válido")
    
    
@app.route('/fotos', methods=['GET'])
def getFotos():
    resultado = []
    for d in photoNet.find().sort("likes", -1):
        d["_id"] = str(d["_id"])
        resultado.append(d)
    return jsonify(resultado)


@app.route('/like/<id>', methods=['PUT'])
def darLike(id):
    token = request.headers["Authorization"].split(' ')[1]
    if (id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)):
        oid = ObjectId(id)
        resultado = photoNet.find_one({"_id" : oid})
        if resultado is not None:
            if request.is_json:
                datos = request.get_json()
                nuevos_valores = {}
                try:
                    if "likes" in datos:
                        nuevos_valores["likes"] = int(datos["likes"])
                except Exception:
                    respuesta = jsonify(msg="Petición no válida, hay campos que no son del tipo correcto")
                    return respuesta

                photoNet.update_one({"_id": oid}, {"$set": nuevos_valores})
                return jsonify(msg='Usuario actualizado')
            else:
                respuesta = jsonify(msg="Petición no válida, se requiere JSON")
                return respuesta
        else:
            respuesta = jsonify(msg="No existe ningún usuario con id = %s" % id)
            return respuesta
    else:
        return jsonify(msg="Token no válido")


if __name__ == "__main__":
    app.run(debug=True)