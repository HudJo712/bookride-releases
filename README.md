# Book & Ride API (User & Developer Overview)

This README summarizes how the app works for users and developers, plus the major API endpoints for each flow.

How the app works
- Users register/login to get a Bearer token.
- Users can browse books and bikes, start loans/rentals, and return items.
- Book loans add an upfront fee and may add a late fine after 5 minutes.
- Bike rentals add a usage fee when the rental is stopped.
- All charges accumulate in the user balance; paying clears the balance.
- Developers use the Control Room to operate all endpoints, seed data, and test flows.

User side (Guest Dashboard)
- Shows available bikes and the user’s active rentals.
- Shows available books and the user’s active book loans.
- Lets the user start/stop rentals and book loans.
- Shows total due and allows balance payment.

Developer side (Control Room)
- Full access to:
  - Auth (register/login + access role)
  - Books (list/get/create/update)
  - Book loans (start/stop/active)
  - Bikes (list available + full catalog + CRUD)
  - Rentals (API-key flow + bearer flow + active)
  - Balance (get/pay)
  - System info/health/metrics

Base URL
- Default base URL: `/api`
- All requests and responses use JSON unless otherwise noted.

Auth & Access
- `POST /register`
  - Body: `{ "email": "user@example.com", "password": "Secret123" }`
  - Registers a new user.
- `POST /login`
  - Body: `{ "email": "user@example.com", "password": "Secret123" }`
  - Returns an access token used as a Bearer token.
- `GET /access`
  - Headers: `Authorization: Bearer <token>`
  - Returns role and user metadata.

Books (catalog)
- `GET /books`
  - Headers: `Authorization: Bearer <token>`
  - Returns all books.
- `GET /books/{book_id}`
  - Headers: `Authorization: Bearer <token>`
  - Returns a single book by ID.

Book Loans (lend/return)
- `POST /book-loans/start`
  - Headers: `Authorization: Bearer <token>`
  - Body: `{ "book_id": 101 }`
  - Starts a loan and applies the upfront fee to the user balance.
  - Rules:
    - Max 2 active loans per user.
    - Any outstanding fees block lending.
    - Late return fine applies after 5 minutes.
- `POST /book-loans/stop`
  - Headers: `Authorization: Bearer <token>`
  - Body: `{ "loan_id": 1 }`
  - Returns a book and applies late fee if overdue.
- `GET /book-loans/active`
  - Headers: `Authorization: Bearer <token>`
  - Returns active book loans for the user (also applies overdue fines if needed).

Bike Rentals
- `GET /bikes`
  - Headers: `Authorization: Bearer <token>`
  - Returns bikes available for rent.
- `POST /rentals/start-auth`
  - Headers: `Authorization: Bearer <token>`
  - Body: `{ "bike_id": "bike-101" }`
  - Starts a rental for the signed-in user.
- `POST /rentals/stop-auth`
  - Headers: `Authorization: Bearer <token>`
  - Body: `{ "rental_id": 1 }`
  - Stops a rental and adds the rental price to the user balance.
- `GET /rentals/active`
  - Headers: `Authorization: Bearer <token>`
  - Returns active rentals for the user.

Payments & Balance
- `GET /balance`
  - Headers: `Authorization: Bearer <token>`
  - Returns the current outstanding balance (overdue book fines may be applied here).
- `POST /balance/pay`
  - Headers: `Authorization: Bearer <token>`
  - Clears the outstanding balance.

Notes
- Some endpoints require a valid Bearer token. Use `/login` to obtain it.
- Book loans and bike rentals are separate systems but share the same user balance.
