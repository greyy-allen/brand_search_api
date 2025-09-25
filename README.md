# Brands API

A Flask-based REST API that provides endpoints for searching and filtering brand data as well as ingredient auto-completion for frontend UIs. The API uses MongoDB for data storage and is secured via CORS and a wall parameter.

---

## Overview

This project implements a backend service for brand search and ingredient auto-complete features. It is suitable for use by frontend applications requiring efficient, flexible brand data retrieval and ingredient lookup (e.g., in e-commerce or CPG tools).

### Features

- **Brand search endpoint** with complex query filtering and cursor-based pagination.
- **Ingredient auto-complete** powered by MongoDB aggregation.
- **CORS Support** for configurable frontend origins.
- **Protected Endpoints** by requiring `?wall=78` parameter on each request.

---

## Installation

### Requirements

- Python 3.8+
- MongoDB database
- pip (Python package manager)

### Setup

1. Clone the repository or copy the provided code into your project directory.

2. Install dependencies:

   ```bash
   pip install flask flask_cors pymongo python-dotenv bson
   ```

3. Configure environment variables in a `.env` file (optional, default values provided):

   ```dotenv
   # MongoDB connection URI (replace with your credentials as needed)
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/
   # Allowed frontend origins (comma-separated)
   FRONTEND_ORIGINS=http://localhost:5173,https://cpg-brand-search.onrender.com,https://signals-ui.onrender.com,http://127.0.0.1:5000
   ```

4. Start the Flask app:

   ```bash
   python app.py
   ```

---

## API Documentation

### Global Request Requirement

Every API request must include the query parameter `?wall=78`. Otherwise, a `403 Forbidden` status code is returned.

#### Example

```
POST /api/brands/search?wall=78
```

---

### 1. `POST /api/brands/search`

**Purpose:**  
Perform complex, multi-criteria searches on the `brand_profile` collection.

#### Request Body

- **limit** (int, optional): Max number of results (default 25, max 100).
- **cursor** (string, optional): The `_id` of the last document from the previous page. Used for cursor-based pagination.
- **categories** (list, optional): Categories to match. All provided categories must be present in the brand's categories.
- **market_metrics** (dict, optional): Direct MongoDB queries on the `market_metrics` sub-document.
- **filters** (dict, optional): User feature filters, nested by section, with each value being an array of strings. A brand passes if it matches any value inside each section.
- **include** (list, optional): Ingredients to include (brand must contain at least one).
- **exclude** (list, optional): Ingredients to exclude (brand must not contain any).

#### Example Request (First Page)

```http
POST /api/brands/search?wall=78
Content-Type: application/json

{
  "limit": 5,
  "categories": ["Immune Health"]
}
```

#### Example Response

```json
{
  "results": [
    {
      "_id": "685d4d949689d39d94274242",
      "name": "Oregon's Wild Harvest",
      "categories": ["Stress & Mood", "Digestive Health"],
      "product_philosophy": "...",
      "annual_volume": 2325
    }
  ],
  "limit": 5,
  "has_more": true,
  "next_cursor": "685d4d949689d39d94274242"
}
```

#### Example Request (Next Page)

```http
POST /api/brands/search?wall=78
Content-Type: application/json

{
  "limit": 5,
  "categories": ["Immune Health"],
  "cursor": "685d4d949689d39d94274242"
}
```

---

### Pagination Guide

- Pagination is **cursor-based** using MongoDB `_id` values.
- Each response includes:
  - `has_more`: Boolean indicating if more pages exist.
  - `next_cursor`: Pass this value in the next request to fetch the following page.
- Frontend developers can implement an **infinite scroll** or **Load More button** using this pattern.

#### Frontend Example (pseudo-code)

```js
let cursor = null;
async function fetchPage() {
  const res = await fetch("/api/brands/search?wall=78", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit: 10, categories: ["Immune Health"], cursor }),
  });
  const data = await res.json();
  renderResults(data.results);
  cursor = data.next_cursor; // update cursor for next call
  if (!data.has_more) disableLoadMoreButton();
}
```

---

### 2. `POST /api/ingredients/autocomplete`

**Purpose:**  
Returns distinct matching ingredient names starting with the given prefix (case-insensitive, minimum 2 characters).

#### Request Body

- **q** (string, required): Ingredient prefix to search for.

#### Example Request

```http
POST /api/ingredients/autocomplete?wall=78
Content-Type: application/json

{
  "q": "Alo"
}
```

#### Response

```json
{
  "results": ["Aloe Vera", "Aloe Barbadensis Leaf Juice"]
}
```

#### Notes

- The search is triggered only if `q` has at least 2 characters.
- Returns alphabetically sorted ingredient names.

---

## Code Structure and Explanation

### Main Components

- **Flask App Initialization:**  
  Initializes and configures Flask, loads environment variables, sets up MongoDB client, and configures CORS.

- **Security Middleware:**  
  All requests must contain `?wall=78` as a query parameter, enforced via `@app.before_request`.

- **Database:**  
  Uses MongoDB. Collection: `brand_profile` in database `brands`.

- **Endpoints:**
  - `/api/brands/search` — for searching brands with cursor pagination.
  - `/api/ingredients/autocomplete` — for autocompleting ingredient names.

### CORS

- Only specified frontend origins (`FRONTEND_ORIGINS` env var) are allowed to access `/api/*` endpoints.

### MongoDB Connection

- Connection string and DB configuration are read from environment, allowing for secure and flexible deployments.

---

## Usage Examples (with `curl`)

### Search Brands (First Page)

```bash
curl -X POST "http://localhost:5000/api/brands/search?wall=78"      -H "Content-Type: application/json"      -d '{"limit": 5, "categories": ["Immune Health"]}'
```

### Search Brands (Next Page)

```bash
curl -X POST "http://localhost:5000/api/brands/search?wall=78"      -H "Content-Type: application/json"      -d '{"limit": 5, "categories": ["Immune Health"], "cursor": "685d4d949689d39d94274242"}'
```

### Ingredient Autocomplete

```bash
curl -X POST "http://localhost:5000/api/ingredients/autocomplete?wall=78"      -H "Content-Type: application/json"      -d '{"q": "Alo"}'
```

---

## Notes, Caveats, and Best Practices

- **Security:**  
  The crude use of a `wall=78` parameter offers only minimal protection; consider implementing proper authentication for production.
- **Environment Variables:**  
  Store sensitive information such as database URIs securely.
- **Performance:**  
  Use MongoDB indexes on commonly searched fields (`ingredients`, `categories`, etc.) for best performance.
- **Pagination:**  
  Cursor-based pagination is used instead of `skip` for efficiency on large datasets.
- **Input Validation:**  
  The API does not strictly validate request bodies; ensure that client applications send correctly structured JSON.
- **Field Limitations:**  
  Only specific fields are returned by `/brands/search` for efficiency.

---

## License

This example is provided "as is" for documentation purposes. Please adapt, extend, and secure according to your project requirements.
