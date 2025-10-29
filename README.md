# Book & Ride API

## Setup (≤5 steps)
1. `cp .env.example .env`
2. `docker compose up -d`
3. `docker compose ps` and wait until all containers are `healthy`
4. `curl http://localhost:8000/health` → `{"status":"ok","version":"1.0.0"}`
5. Optional: `docker compose logs -f api` to watch requests

## 2-Minute Demo Script
1. Create a book in JSON, retrieve it as YAML, then repeat creation in XML to show content negotiation.
2. POST a partner rental payload and fetch it back as protobuf to demonstrate binary support.
3. Start and stop a rental with the API key to highlight authentication and pricing.
4. Open `http://localhost:9090` to display Prometheus scraping the `/metrics` endpoint.

## API Collection (curl)
```bash
# Health
curl http://localhost:8000/health

# Create book (JSON)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"id":1,"title":"1984","author":"George Orwell","price":8.99,"in_stock":true}'

# Get book (YAML response)
curl http://localhost:8000/books/1 \
  -H "Accept: application/x-yaml"

# Create book (XML)
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  -d '<book><id>2</id><title>Dune</title><author>Frank Herbert</author><price>14.5</price><in_stock>true</in_stock></book>'

# Partner rental ingest (JSON)
curl -X POST http://localhost:8000/rentals \
  -H "Content-Type: application/json" \
  -d '{"id":201,"user_id":5,"bike_id":"B-42","start_time":"2024-06-01T12:00:00Z","price_eur":9.5}'

# Retrieve partner rental (protobuf)
curl http://localhost:8000/rentals/201 \
  -H "Accept: application/x-protobuf" \
  --output rental-201.pb

# Convert payload to XML
curl -X POST "http://localhost:8000/convert?to=xml" \
  -H "Content-Type: application/json" \
  -d '{"sample": "value"}'

# Start rental (API key)
curl -X POST http://localhost:8000/rentals/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"bike_id":"BIKE-01"}'

# Stop rental (API key)
curl -X POST http://localhost:8000/rentals/stop \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{"rental_id":1}'

# Metrics snapshot
curl http://localhost:8000/metrics | head -n 20
```

## Architecture Snapshot
- [Architecture Brief](Architecture-Brief.md) — rationale for the monolith and deployment slice.
- ADRs: [`ADR-001`](adr/ADR-001-architecture.md), [`ADR-002`](adr/ADR-002-DatabaseSchema.md), [`ADR-003`](adr/ADR-003-Authentication.md)

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

# Pretty toggle

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
