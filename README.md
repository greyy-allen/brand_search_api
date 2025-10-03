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
- **Annual Volume Slider Filtering** with default range `[0, global_max]` and `annual_volume_max` returned in responses.
- **Count field** returned in responses to indicate number of results in the current page.

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
- **annual_volume** (dict, optional): Range filter with keys:
  - `min` (float, optional): Minimum annual volume. Defaults to `0` if not provided.
  - `max` (float, optional): Maximum annual volume. Defaults to `annual_volume_max` (the global maximum across all brands) if not provided.

#### Quick Guide: Annual Volume min/max

- If `annual_volume` is **not provided**, the API defaults to `[0, annual_volume_max]`.
- If only `min` is provided, it defaults to `[min, annual_volume_max]`.
- If only `max` is provided, it defaults to `[0, max]`.
- If both are provided, it enforces `[min, max]`.

#### Sample Request Bodies for `annual_volume`

**1. No min/max provided**

```json
{
  "limit": 5
}
```

**2. Only min provided**

```json
{
  "limit": 5,
  "annual_volume": {
    "min": 2000
  }
}
```

**3. Only max provided**

```json
{
  "limit": 5,
  "annual_volume": {
    "max": 10000
  }
}
```

**4. Both min and max provided**

```json
{
  "limit": 5,
  "annual_volume": {
    "min": 1000,
    "max": 5000
  }
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
  "count": 1,
  "limit": 5,
  "has_more": true,
  "next_cursor": "685d4d949689d39d94274242",
  "annual_volume_max": 500000
}
```

---

### Pagination Guide

- Pagination is **cursor-based** using MongoDB `_id` values.
- Each response includes:
  - `count`: Number of results in this page.
  - `has_more`: Boolean indicating if more pages exist.
  - `next_cursor`: Pass this value in the next request to fetch the following page.
  - `annual_volume_max`: Global maximum value for the slider.

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

---

## Notes, Caveats, and Best Practices

- **Security:**  
  The crude use of a `wall=78` parameter offers only minimal protection; consider implementing proper authentication for production.
- **Environment Variables:**  
  Store sensitive information such as database URIs securely.
- **Performance:**  
  Use MongoDB indexes on commonly searched fields (`ingredients`, `categories`, `annual_volume`, etc.) for best performance.
- **Pagination:**  
  Cursor-based pagination is used instead of `skip` for efficiency on large datasets.
- **Input Validation:**  
  The API does not strictly validate request bodies; ensure that client applications send correctly structured JSON.
- **Field Limitations:**  
  Only specific fields are returned by `/brands/search` for efficiency.
- **Annual Volume Defaults:**  
  If no `annual_volume` filter is supplied, the API defaults to `{"min": 0, "max": annual_volume_max}`.

---

## License

This example is provided "as is" for documentation purposes. Please adapt, extend, and secure according to your project requirements.
