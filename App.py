from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import json

app = Flask(__name__)

# Conectar a MongoDB (asegúrate de que el servidor de Mongo esté en ejecución)
client = MongoClient("mongodb://localhost:27017/")
db = client["nobel"]
winners_collection = db["winners"]

# Cargar datos en MongoDB desde un archivo JSON si la colección está vacía
def load_data():
    if winners_collection.count_documents({}) == 0:
        with open(r"C:\Users\HP\Documents\App\nobel_winners.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, dict):
                data = data.get("winners", [])  # Si el JSON tiene una clave principal
            winners_collection.insert_many(data)

load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/nobel', methods=['GET'])
def get_nobel_winners():
    winners = list(winners_collection.aggregate([{ "$sample": { "size": 5 } }]))
    for winner in winners:
        winner["_id"] = str(winner["_id"])  # Convertir ObjectId a string para JSON
        winner["name"] = winner.get("name", "Desconocido")
        winner["country"] = winner.get("country", "Sin país")
    
    return jsonify(winners)

@app.route('/api/countries', methods=['GET'])
def get_winners_by_country():
    pipeline = [
        { "$group": { "_id": "$country", "count": { "$sum": 1 } } },
        { "$sort": { "count": -1 } }
    ]
    result = list(winners_collection.aggregate(pipeline))
    return jsonify(result)

@app.route('/api/categories_by_country', methods=['GET'])
def get_categories_by_country():
    pipeline = [
        { "$group": { "_id": { "country": "$country", "category": "$category" }, "count": { "$sum": 1 } } },
        { "$sort": { "_id.country": 1, "_id.category": 1 } }
    ]
    result = list(winners_collection.aggregate(pipeline))

    formatted_result = {}
    for entry in result:
        country = entry["_id"]["country"]
        category = entry["_id"]["category"]
        count = entry["count"]
        
        if country not in formatted_result:
            formatted_result[country] = {}
        
        formatted_result[country][category] = count

    return jsonify(formatted_result)

if __name__ == '__main__':
    app.run(debug=True)



