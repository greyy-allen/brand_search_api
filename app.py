from flask import Flask, request, Response, abort
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
from dotenv import load_dotenv
import re
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
    cursor = body.get("cursor")

    projection = {
        "_id": 1,
        "name": 1,
        "categories": 1,
        "product_philosophy": 1,
        "annual_volume": 1,
    }

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
            if not wanted:
                continue
            if len(wanted) == 1:
                # one value → exact match
                query.append({f"filters.{section}": wanted[0]})
            else:
                # require ALL values present in that section
                query.append({f"filters.{section}": {"$all": wanted}})

    # 4. Ingredient Filter to include/exclude
    ing_any = body.get("include")
    ing_exclude_any = body.get("exclude")

    if ing_any:
        query.append({"ingredients": {"$in": ing_any}})
    if ing_exclude_any:
        query.append({"ingredients": {"$nin": ing_exclude_any}})

    # Build AND query
    if len(query) == 1:
        mongo_query = query[0]
    elif query:
        mongo_query = {"$and": query}
    else:
        mongo_query = {}

    if cursor:
        try:
            cursor_oid = ObjectId(cursor)
            if mongo_query:
                mongo_query = {"$and": [mongo_query, {"_id": {"$gt": cursor_oid}}]}
            else:
                mongo_query = {"_id": {"$gt": cursor_oid}}
        except Exception:
            pass

    docs = list(
        brands.find(mongo_query, projection).sort([("_id", 1)]).limit(limit + 1)
    )

    has_more = len(docs) > limit
    visible = docs[:limit] if has_more else docs
    next_cursor = str(visible[-1]["_id"]) if has_more else None

    return Response(
        dumps(
            {
                "results": visible,
                "limit": limit,
                "has_more": has_more,
                "next_cursor": next_cursor,
            }
        ),
        mimetype="application/json",
    )


@app.route("/api/ingredients/autocomplete", methods=["POST"])
def ingredients_autocomplete():
    body = request.get_json(silent=True) or {}
    q = (body.get("q") or "").strip()

    stages = []

    if len(q) >= 2:
        rx = f"^{re.escape(q)}"
        stages.append({"$match": {"ingredients": {"$regex": rx, "$options": "i"}}})

    stages += [{"$unwind": "$ingredients"}]

    if len(q) >= 2:
        stages.append({"$match": {"ingredients": {"$regex": rx, "$options": "i"}}})

    stages += [{"$group": {"_id": "$ingredients"}}, {"$sort": {"_id": 1}}]

    docs = list(brands.aggregate(stages, allowDiskUse=False))
    results = [d["_id"] for d in docs]
    return Response(dumps({"results": results}), mimetype="application/json")


if __name__ == "__main__":
    app.run(debug=True)
