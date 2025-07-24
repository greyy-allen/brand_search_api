from flask import Flask, request, Response
from pymongo import MongoClient
from bson.json_util import dumps
import os

app = Flask(__name__)

mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)
db = client.brands
brands = db.brand_profile


@app.route("/api/brands/search", methods=["POST"])
def search_brands():
    body = request.get_json()

    # If no payload, return first 25 results
    if not body:
        results = list(brands.find().limit(25))
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
            # In Mongo, assuming e.g. unique_selling_points is a list of dicts with "title"
            # Be flexible: user can pass either scalar or dict for matching
            section_path = section  # e.g. "unique_selling_points"
            sub_q = []
            for value in wanted:
                # try to match on dicts' 'title' fields or just the string
                # assumes in DB: e.g. unique_selling_points: [{title: ...}]
                sub_q.append({f"filters.{section_path}": value})
                # OR: try direct match if field stored as string
                # sub_q.append({section: value})
            # For each filter, require at least one match for the wanted list.
            query.append({"$or": sub_q})

    # Build AND query
    mongo_query = {"$and": query} if query else {}

    results = list(brands.find(mongo_query))
    return Response(
        dumps({"results": results, "count": len(results)}), mimetype="application/json"
    )


if __name__ == "__main__":
    app.run(debug=True)
