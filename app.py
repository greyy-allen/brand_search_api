from flask import Flask, request, Response, abort
from flask_cors import CORS
from pymongo import MongoClient
from bson.json_util import dumps
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

# ENV VAR
mongo_uri = os.getenv(
    "MONGODB_URI", "mongodb+srv://michael:hdb12821az@cpgrv3.7mwy8pv.mongodb.net/"
)
frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,https://cpg-brand-search.onrender.com,https://signals-ui.onrender.com,http://127.0.0.1:5000",
)
allowed_origins = [origin.strip() for origin in frontend_origins.split(",") if origin]

CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

client = MongoClient(mongo_uri)
db = client.brands
brands = db.brand_profile


@app.before_request
def check_wall_param():
    """Allow further processing only if ?wall=78 is present"""
    wall = request.args.get("wall")
    if wall != "78":
        abort(403)  # Forbidden


@app.route("/api/brands/search", methods=["POST"])
def search_brands():
    body = request.get_json(silent=True) or {}
    limit = min(int(body.get("limit", 25)), 100)
    skip = int(body.get("skip", 0))
    projection = {
        "_id": 1,
        "name": 1,
        "categories": 1,
        "product_philosophy": 1,
        "annual_volume": 1,
    }

    if not body:
        results = list(brands.find({}, projection).skip(skip).limit(limit))
        return Response(
            dumps({"results": results, "count": len(results)}),
            mimetype="application/json",
        )

    # AND logic: Accumulate all subqueries
    query = []

    # 1. Categories (must have all)
    categories = body.get("categories")
    if categories:
        query.append({"categories": {"$all": categories}})

    # 2. Market Metrics (dict of conditions, supports mongo operators)
    market_metrics = body.get("market_metrics")
    if market_metrics:
        for k, v in market_metrics.items():
            query.append({f"market_metrics.{k}": v})

    # 3. Filters (nested dict: each key is a section, array of features)
    filters = body.get("filters")
    if filters:
        for section, wanted in filters.items():
            if wanted:
                query.append({f"filters.{section}": {"$in": wanted}})

    # Build AND query
    if len(query) == 1:
        mongo_query = query[0]
    elif query:
        mongo_query = {"$and": query}
    else:
        mongo_query = {}

    results = list(brands.find(mongo_query, projection).skip(skip).limit(limit))
    return Response(
        dumps({"results": results, "count": len(results)}), mimetype="application/json"
    )


if __name__ == "__main__":
    app.run(debug=True)
