<<<<<<< HEAD
# Book & Ride API

## Setup (≤6 steps)
1. `cp .env.example .env`
2. Fill in `DATABASE_URL`, `API_KEY_PEPPER`, `JWT_HS256_SECRET`, and optional `OIDC_*` values.
3. `pip install -r api/requirements.txt` (or rebuild your API container)
4. `docker compose up -d`
5. `docker compose ps` and wait until all containers are `healthy`
6. `curl http://localhost:8000/health` → `{"status":"ok","version":"1.0.0"}` (optional: `docker compose logs -f api`)

## 2-Minute Demo Script
1. Create a book in JSON, retrieve it as YAML, then repeat creation in XML to show content negotiation.
2. POST a partner rental payload and fetch it back as protobuf to demonstrate binary support.
3. Start and stop a rental with the API key to highlight authentication and pricing.
4. Open `http://localhost:9090` to display Prometheus scraping the `/metrics` endpoint.

## Authentication Quickstart
```bash
# Seed an API key (run inside repo; DB connection comes from env)
python scripts/seed_api_keys.py --name partner-a --key supersecret123

# Seed a JWT user with scopes
python scripts/seed_users.py --username admin --password changeme --scopes "books:write rentals:write"

# Fetch a JWT access token
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=admin&password=changeme&scope=books:write rentals:write' | jq -r .access_token)

# Partners can use their own IdP tokens if OIDC_* vars are configured.
```

### Logging note
- Local scrapes and `/metrics` are faster if you keep `BOOKRIDE_DISABLE_ELASTIC=true` (defaults in `.env.example`). This disables the Elasticsearch logging handler that can block requests when ES is slow/unreachable.

### OAuth / OIDC
1. Set `OIDC_ISS`, `OIDC_AUD`, and `OIDC_JWKS_URL` in `.env`.
2. Restart the API container so JWKS metadata is loaded.
3. Have partners request tokens from that issuer that include `partner.rentals`.
4. Call partner endpoints with `Authorization: Bearer <oidc_token>`.

## API Collection (curl)
```bash
# Health
curl http://localhost:8000/health

# Create book (JSON)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"id":1,"title":"1984","author":"George Orwell","price":8.99,"in_stock":true}'

# Get book (YAML response)
curl http://localhost:8000/books/1 \
  -H "Accept: application/x-yaml" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# Create book (XML)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '<book><id>2</id><title>Dune</title><author>Frank Herbert</author><price>14.5</price><in_stock>true</in_stock></book>'

# Partner rental ingest (JSON)
curl -X POST http://localhost:8000/rentals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARTNER_TOKEN" \
  -d '{"id":201,"user_id":5,"bike_id":"B-42","start_time":"2024-06-01T12:00:00Z","price_eur":9.5}'

# Retrieve partner rental (protobuf)
curl http://localhost:8000/rentals/201 \
  -H "Accept: application/x-protobuf" \
  -H "Authorization: Bearer $PARTNER_TOKEN" \
  --output rental-201.pb

# Convert payload to XML
curl -X POST "http://localhost:8000/convert?to=xml" \
  -H "Content-Type: application/json" \
  -d '{"sample": "value"}'

# Start rental (JWT)
curl -X POST http://localhost:8000/rentals/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"bike_id":"BIKE-01"}'

# Start rental (API key alternative)
curl -X POST http://localhost:8000/rentals/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"bike_id":"BIKE-02"}'

# Stop rental (JWT)
curl -X POST http://localhost:8000/rentals/stop \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"rental_id":1}'

# Stop rental (API key alternative)
curl -X POST http://localhost:8000/rentals/stop \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"rental_id":2}'

# Metrics snapshot
curl http://localhost:8000/metrics | head -n 20
```

## Extended Test Scenarios
### Books: Content Types & Validation
```bash
# Create book (JSON baseline)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"id":1,"title":"1984","author":"George Orwell","price":8.99,"in_stock":true}'

# Create book (XML)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -d '<book><id>2</id><title>Brave New World</title><author>Aldous Huxley</author><price>9.75</price><in_stock>false</in_stock></book>'

# Validation failures (JSON)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"id":11,"title":"No Author","price":5.0,"in_stock":true}'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"id":12,"title":"Genre Test","author":"Tester","price":7.5,"in_stock":true,"genre":"sci-fi"}'

# Validation failures (XML)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/json" \
  -d '<book><id>20</id><title>Faulty</title><author>Tester</author><price>free</price><in_stock>true</in_stock></book>'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/json" \
  -d '<book><id>21</id><title>No Author</title><price>5.0</price><in_stock>true</in_stock></book>'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/json" \
  -d '<book><id>22</id><title>Genre Test</title><author>Tester</author><price>7.5</price><in_stock>true</in_stock><genre>sci-fi</genre></book>'

# Null and zero price handling
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"id":30,"title":"Null Price","author":"Tester","price":null,"in_stock":true}'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"id":31,"title":"Free Book","author":"Tester","price":0,"in_stock":true}'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/json" \
  -d '<book><id>32</id><title>Null Price</title><author>Tester</author><price></price><in_stock>true</in_stock></book>'

curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/json" \
  -d '<book><id>33</id><title>Free Book</title><author>Tester</author><price>0</price><in_stock>true</in_stock></book>'

# Namespaced XML
curl -X POST http://localhost:8000/books \
  -H 'Content-Type: application/xml' \
  -H 'Accept: application/xml' \
  -d '<books xmlns:b="urn:book"><b:book><b:id>10</b:id><b:title>Namespaced</b:title><b:author>Mapper</b:author><b:price>5.5</b:price><b:in_stock>true</b:in_stock></b:book></books>'
```

### Partner Rentals: ISO-8601 Enforcement
```bash
# Valid timestamps
curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/json' \
  -d '{"id":301,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00Z","end_time":"2024-06-01T13:15:00Z","price_eur":75}'

curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/xml' \
  -d '<rental><id>303</id><user_id>5</user_id><bike_id>B-99</bike_id><start_time>2024-06-01T12:30:00Z</start_time><end_time>2024-06-01T13:15:00Z</end_time><price_eur>7.5</price_eur></rental>'

# Invalid timestamps
curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/json' \
  -d '{"id":302,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00","price_eur":7.5}'

curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/xml' \
  -d '<rental><id>304</id><user_id>5</user_id><bike_id>B-99</bike_id><start_time>2024-06-01T12:30:00</start_time><price_eur>7.5</price_eur></rental>'
```

### Converters & Collections
```bash
# JSON array passthrough
curl -X POST 'http://localhost:8000/convert?to=json' \
  -H 'Content-Type: application/json' \
  -d '[{"id":1,"title":"1984","author":"Orwell","price":9.99,"in_stock":true},{"id":2,"title":"Dune","author":"Herbert","price":14.5,"in_stock":false}]'

# Convert JSON array to XML
curl -X POST 'http://localhost:8000/convert?to=xml' \
  -H 'Content-Type: application/json' \
  -d '[{"id":1,"title":"1984","author":"Orwell","price":9.99,"in_stock":true},{"id":2,"title":"Dune","author":"Herbert","price":14.5,"in_stock":false}]'
```

### Security Hardening Checks
```bash
# Ensure safe XML parsing
curl -X POST http://localhost:8000/books \
  -H 'Content-Type: application/xml' \
  -d '<book><id>50</id><title>Safe</title><author>Tester</author><price>5.0</price><in_stock>true</in_stock></book>'
```

## Detailed Test Library
# application/xml vs JSON
xml Command:
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/xml" \
  -d '<book><id>2</id><title>Brave New World</title><author>Aldous Huxley</author><price>9.75</price><in_stock>false</in_stock></book>'

xml Result:
<?xml version="1.0" encoding="utf-8"?>
<book>
        <id>2</id>
        <title>Brave New World</title>
        <author>Aldous Huxley</author>
        <price>9.75</price>
        <in_stock>false</in_stock>
</book>

JSON Command:
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -H "Accept": "application/json" \
  -d '{"id":1,"title":"1984","author":"George Orwell","price":8.99,"in_stock":true}'

JSON Result:
{"id":1,"title":"1984","author":"George Orwell","price":8.99,"in_stock":true}

# Validation send an invalid price (string), missing author, extra field genre
# JSON
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -d '{"id":11,"title":"No Author","price":5.0,"in_stock":true}'

{"detail":{"error":"schema_validation","message":"'author' is a required property","path":[]}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -d '{"id":11,"title":"No Author","price":5.0,"in_stock":true}'

{"detail":{"error":"schema_validation","message":"'author' is a required property","path":[]}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -d '{"id":12,"title":"Genre Test","author":"Tester","price":7.5,"in_stock":true,"genre":"sci-fi"}'

{"detail":{"error":"schema_validation","message":"Additional properties are not allowed ('genre' was unexpected)","path":[]}}

# xml
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/json" \
  -d '<book><id>20</id><title>Faulty</title><author>Tester</author><price>free</price><in_stock>true</in_stock></book>'
{"detail":{"error":"invalid_xml","message":"XML payload has invalid field types"}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/json" \
  -d '<book><id>21</id><title>No Author</title><price>5.0</price><in_stock>true</in_stock></book>'
{"detail":{"error":"schema_validation","message":"'author' is a required property","path":[]}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/json" \
  -d '<book><id>22</id><title>Genre Test</title><author>Tester</author><price>7.5</price><in_stock>true</in_stock><genre>sci-fi</genre></book>'
{"detail":{"error":"schema_validation","message":"Additional properties are not allowed ('genre' was unexpected)","path":[]}}

# Nulls & Types - Try{"price":null} vs 0.
JSON
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -d '{"id":30,"title":"Null Price","author":"Tester","price":null,"in_stock":true}'
{"detail":{"error":"schema_validation","message":"None is not of type 'number'","path":["price"]}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/json" \
  -d '{"id":31,"title":"Free Book","author":"Tester","price":0,"in_stock":true}'
{"id":31,"title":"Free Book","author":"Tester","price":0.0,"in_stock":true}

XML
curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/json" \
  -d '<book><id>32</id><title>Null Price</title><author>Tester</author><price></price><in_stock>true</in_stock></book>'
{"detail":{"error":"invalid_xml","message":"XML payload has invalid field types"}}

curl -X POST http://localhost:8000/books \
  -H "Content-Type": "application/xml" \
  -H "Accept": "application/json" \
  -d '<book><id>33</id><title>Free Book</title><author>Tester</author><price>0</price><in_stock>true</in_stock></book>'
{"id":33,"title":"Free Book","author":"Tester","price":0.0,"in_stock":true}

# Dates - add ISO-8601 strings to rental and validate pattern
JSON
curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/json' \
  -d '{"id":301,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00Z","end_time":"2024-06-01T13:15:00Z","price_eur":75}'
{"id":301,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00Z","end_time":"2024-06-01T13:15:00Z","price_eur":75.0}

curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/json' \
  -d '{"id":302,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00","price_eur":7.5}'
{"detail":{"error":"schema_validation","message":"'2024-06-01T12:30:00' does not match '^\\\\d{4}-\\\\d{2}-\\\\d{2}T\\\\d{2}:\\\\d{2}:\\\\d{2}(?:\\\\.\\\\d+)?Z$'","path":["start_time"]}}

XML
curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/xml' \
  -d '<rental><id>303</id><user_id>5</user_id><bike_id>B-99</bike_id><start_time>2024-06-01T12:30:00Z</start_time><end_time>2024-06-01T13:15:00Z</end_time><price_eur>7.5</price_eur></rental>'
{"id":303,"user_id":5,"bike_id":"B-99","start_time":"2024-06-01T12:30:00Z","end_time":"2024-06-01T13:15:00Z","price_eur":7.5}

curl -X POST http://localhost:8000/rentals \
  -H 'Content-Type: application/xml' \
  -d '<rental><id>304</id><user_id>5</user_id><bike_id>B-99</bike_id><start_time>2024-06-01T12:30:00</start_time><price_eur>7.5</price_eur></rental>'
{"detail":{"error":"schema_validation","message":"'2024-06-01T12:30:00' does not match '^\\\\d{4}-\\\\d{2}-\\\\d{2}T\\\\d{2}:\\\\d{2}:\\\\d{2}(?:\\\\.\\\\d+)?Z$'","path":["start_time"]}}

# Arrays: Extend schema to accept a list of books: root JSON array vs XML<books><book/></books>. Normalize
curl -X POST 'http://localhost:8000/convert?to=json' \
  -H 'Content-Type: application/json' \
  -d '[{"id":1,"title":"1984","author":"Orwell","price":9.99,"in_stock":true}, {"id":2,"title":"Dune","author":"Herbert","price":14.5,"in_stock":false}]'
[{"id":1,"title":"1984","author":"Orwell","price":9.99,"in_stock":true},{"id":2,"title":"Dune","author":"Herbert","price":14.5,"in_stock":false}]

curl -X POST 'http://localhost:8000/convert?to=xml' \
  -H 'Content-Type: application/json' \
  -d '[{"id":1,"title":"1984","author":"Orwell","price":9.99,"in_stock":true}, {"id":2,"title":"Dune","author":"Herbert","price":14.5,"in_stock":false}]'
<?xml version="1.0" encoding="utf-8"?>
<root>
        <item>
                <id>1</id>
                <title>1984</title>
                <author>Orwell</author>
                <price>9.99</price>
                <in_stock>true</in_stock>
        </item>
        <item>
                <id>2</id>
                <title>Dune</title>
                <author>Herbert</author>
                <price>14.5</price>
                <in_stock>false</in_stock>
        </item>
</root>

# Namespaces (XML)
curl -X POST http://localhost:8000/books \
  -H 'Content-Type: application/xml' \
  -H 'Accept: application/xml' \
  -d '<books xmlns:b="urn:book"><b:book><b:id>10</b:id><b:title>Namespaced</b:title><b:author>Mapper</b:author><b:price>5.5</b:price><b:in_stock>true</b:in_stock></b:book></books>'
<?xml version="1.0" encoding="utf-8"?>
<b:book xmlns:b="urn:book">
        <b:id>10</b:id>
        <b:title>Namespaced</b:title>
        <b:author>Mapper</b:author>
        <b:price>5.5</b:price>
        <b:in_stock>true</b:in_stock>
</b:book>

# Security
curl -X POST http://localhost:8000/books \
  -H 'Content-Type: application/xml' \
  -d '<book><id>50</id><title>Safe</title><author>Tester</author><price>5.0</price><in_stock>true</in_stock></book>'
{
  "id": 50,
  "title": "Safe",
  "author": "Tester",
  "price": 5.0,
  "in_stock": true
}

curl -X POST http://localhost:8000/books \

### unit 07

# Register
curl -i -X POST http://localhost:8000/register   -H "Content-Type: application/json"   -d '{"email":"alice@example.com","password":"Secret123"}'

HTTP/1.1 201 Created
Server: nginx/1.29.2
Date: Tue, 25 Nov 2025 14:19:33 GMT
Content-Type: application/json
Content-Length: 336
Connection: keep-alive
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwic2NvcGUiOiIiLCJpYXQiOjE3NjQwODAzNzMsImV4cCI6MTc2NDEzNDM3MywiZW1haWwiOiJhbGljZUBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIiwiaXNzIjoiaHR0cHM6Ly9ib29rYW5kcmlkZS5sb2NhbCIsImF1ZCI6ImJvb2thbmRyaWRlLWNsaWVudHMifQ.nzn5NgYyigSj--_7P0pXvojTxyQ_HNx_CKww8KJYI_w","token_type":"bearer"}
# Login → get token
TOKEN=$(curl -s -X POST http://localhost:8000/login \
 -H "Content-Type: application/json" \
 -d '{"email":"alice@example.com","password":"Secret123"}' | jq -r .access_token)

~$ echo "Token: ${TOKEN:0:32}..."

Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...

# Try /books WITHOUT token → 401
curl -i http://localhost:8000/books
HTTP/1.1 401 Unauthorized
Server: nginx/1.29.2
Date: Tue, 25 Nov 2025 14:26:50 GMT
Content-Type: application/json
Content-Length: 30
Connection: keep-alive
www-authenticate: Bearer

{"detail":"Not authenticated"}

# Try /books WITH token → 200
create a book for now
curl -s -X POST http://localhost:8000/books \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":1,"title":"Demo","author":"Me","price":9.99,"in_stock":true}'

curl -s http://localhost:8000/books -H "Authorization: Bearer $TOKEN" | jq

{
  "author": "Me",
  "price": 9.99,
  "in_stock": true,
  "id": 1,
  "title": "Demo"
}[
  {
    "author": "Me",
    "price": 9.99,
    "in_stock": true,
    "id": 1,
    "title": "Demo"
  }
]

# pytest
docker compose exec api pytest -q

.........                                                                                                        [100%]
=================================================== warnings summary ===================================================
../usr/local/lib/python3.11/site-packages/passlib/utils/__init__.py:854
  /usr/local/lib/python3.11/site-packages/passlib/utils/__init__.py:854: DeprecationWarning: 'crypt' is deprecated and slated for removal in Python 3.13
    from crypt import crypt as _crypt

main.py:63
  /app/main.py:63: DeprecationWarning:
          on_event is deprecated, use lifespan event handlers instead.

          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).

    @app.on_event("startup")

../usr/local/lib/python3.11/site-packages/fastapi/applications.py:4575
  /usr/local/lib/python3.11/site-packages/fastapi/applications.py:4575: DeprecationWarning:
          on_event is deprecated, use lifespan event handlers instead.

          Read more about it in the
          [FastAPI docs for Lifespan Events](https://fastapi.tiangolo.com/advanced/events/).

    return self.router.on_event(event_type)

tests/test_books_api.py::test_create_book_rejects_unsupported_content_type
tests/test_rentals_api.py::test_create_rental_accepts_protobuf
  /usr/local/lib/python3.11/site-packages/httpx/_models.py:408: DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
    headers, stream = encode_request(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
9 passed, 5 warnings in 2.01s
=======
# Book & Ride API (DevOps conversion)

## What changed
- Switched to a `pyproject.toml`-driven, src-based package: code under `api/src/bookandride_api`, tests under `tests/`.
- Docker now installs the package directly from `pyproject.toml` and runs `uvicorn bookandride_api.main:app`.
- Extracted modules for concerns: `database.py` (engine/session/init), `auth.py` (API key verification), `schemas.py` (Pydantic models), `logging_config.py` (basic logger).
- Added helper exports and shims: `myproject` package re-exports `add_numbers`/`compute_total`; main `bookandride_api` exports `app`, `add_numbers`, `compute_total`.
- Hardened rental timestamp validation and protobuf handling; fixed UTC round-tripping and Accept/Content negotiation tests.
- Added basic logging in price/rental flows and pytest caplog coverage.
- Simplified test layout with shared FastAPI/SQLModel fixtures and additional targeted tests (auth, schemas, logging, pricing, rentals, books).

## Quickstart
```bash
python -m pip install -e ".[dev]"
pytest
```

## Running the API locally (Docker)
```bash
docker-compose build api_blue api_green
docker-compose up api_blue
# or api_green
```
Uvicorn entrypoint: `bookandride_api.main:app` on port 8080.

## Logging
- Basic console logger: `bookandride_api.logging_config.logger` (name: `bookandride`).
- App still configures the Elasticsearch handler via `logging_utils.configure_logging`; standalone helpers use the basic logger for lightweight messages.

## Tests of interest
- Pricing logic: `tests/test_pricing.py`, `tests/test_price.py`
- Books API validation: `tests/test_books_api.py`
- Rentals protobuf/Accept handling: `tests/test_rentals_api.py`
- Auth and schema validation: `tests/test_auth.py`, `tests/test_schemas.py`
- Logging behavior: `tests/test_logging.py`
- Simple helpers: `tests/test_core.py`
>>>>>>> origin/green

### Unit 08
## test trigger
# assuming you have an endpoint that returns 500 for test
for i in {1..50}; do
 curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/badendpoint
done

for testing
# Fetch a JWT access token

TOKEN=$(curl -s -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' \
  | jq -r .access_token)
echo "$TOKEN"

curl -i -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}'

HTTP/1.1 200 OK
Server: nginx/1.29.2
Date: Thu, 27 Nov 2025 14:04:14 GMT
Content-Type: application/json
Content-Length: 73
Connection: keep-alive

{"access_token":"b_nvSYY87MEtQ-0KhRarrGitM33m7Kv0","token_type":"bearer"}



see running rentals:
cd /home/hudjo712/DataDevOps2/bookride-releases
docker compose exec db psql -U app -d bookandride \
  -c "select id, user, bike_id, started_at from rentals where stopped_at is null;"

curl -X POST http://localhost:8080/rentals/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key-456" \
  -d '{"bike_id":"B-99"}'

see grafana

curl -X POST http://localhost:8080/rentals/stop \
  -H "Content-Type: application/json" \
  -H "X-API-Key: admin-key-456" \
  -d '{"rental_id":1}'

grafana webhook listener
curl -X POST http://localhost:8000/alerts \
  -H "Content-Type: application/json" \
  -d '{"status":"firing","commonLabels":{"alertname":"TestAlert"},"commonAnnotations":{"summary":"hi","description":"test"}}'
