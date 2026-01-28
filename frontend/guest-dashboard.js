const state = {
  baseUrl: localStorage.getItem("br.baseUrl") || "/api",
  bearerToken: sessionStorage.getItem("br.bearerToken") || "",
  apiKey: localStorage.getItem("br.apiKey") || "",
};

const logoutButton = document.getElementById("logout");
const tabBikesButton = document.getElementById("tab-bikes");
const tabBooksButton = document.getElementById("tab-books");
const panelBikes = document.getElementById("panel-bikes");
const panelBooks = document.getElementById("panel-books");
const bikeList = document.getElementById("bike-list");
const rentedList = document.getElementById("rented-list");
const bookList = document.getElementById("book-list");
const loanedList = document.getElementById("loaned-list");
const bikeModalEl = document.getElementById("bike-modal");
const bikeModalTitle = document.getElementById("bike-modal-title");
const bikeModalSubhead = document.getElementById("bike-modal-subhead");
const bikeModalDetails = document.getElementById("bike-modal-details");
const bikeRentAction = document.getElementById("bike-rent-action");
const bookModalEl = document.getElementById("book-modal");
const bookModalTitle = document.getElementById("book-modal-title");
const bookModalSubhead = document.getElementById("book-modal-subhead");
const bookModalDetails = document.getElementById("book-modal-details");
const bookLoanAction = document.getElementById("book-loan-action");
const guestEmail = document.getElementById("guest-email");
const guestUserId = document.getElementById("guest-user-id");
const guestBaseUrl = document.getElementById("guest-base-url");
const guestNotice = document.getElementById("guest-notice");
const guestTotalDue = document.getElementById("guest-total-due");
const payBalanceButton = document.getElementById("pay-balance");

if (!state.bearerToken) {
  window.location.href = "index.html";
}

if (logoutButton) {
  logoutButton.addEventListener("click", () => {
    sessionStorage.removeItem("br.bearerToken");
    window.location.href = "index.html";
  });
}

let activeBike = null;
let activeRentals = [];
let balanceDue = 0;
let activeBook = null;
let activeBookLoans = [];

function renderList(listEl, items, emptyMessage, clickHandler) {
  if (!listEl) {
    return;
  }
  listEl.innerHTML = "";
  if (!items.length) {
    const empty = document.createElement("li");
    empty.className = "item-empty";
    empty.textContent = emptyMessage;
    listEl.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "item-row";
    if (clickHandler) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "item-button";
      const label = document.createElement("span");
      label.className = "item-label";
      label.textContent = item.label;
      button.appendChild(label);
      if (item.right) {
        const right = document.createElement("span");
        right.className = "item-right";
        right.textContent = item.right;
        button.appendChild(right);
      }
      button.addEventListener("click", () => clickHandler(item));
      li.appendChild(button);
    } else {
      li.textContent = item;
    }
    listEl.appendChild(li);
  });
}

function renderDetail(key, value) {
  if (!bikeModalDetails) {
    return;
  }
  const row = document.createElement("div");
  row.className = "detail-row";
  const label = document.createElement("span");
  label.className = "detail-label";
  label.textContent = key;
  const content = document.createElement("span");
  content.className = "detail-value";
  content.textContent = value;
  row.appendChild(label);
  row.appendChild(content);
  bikeModalDetails.appendChild(row);
}

function renderBookDetail(key, value) {
  if (!bookModalDetails) {
    return;
  }
  const row = document.createElement("div");
  row.className = "detail-row";
  const label = document.createElement("span");
  label.className = "detail-label";
  label.textContent = key;
  const content = document.createElement("span");
  content.className = "detail-value";
  content.textContent = value;
  row.appendChild(label);
  row.appendChild(content);
  bookModalDetails.appendChild(row);
}

function openBikeModal(bike) {
  if (!bikeModalEl || !bikeModalDetails) {
    return;
  }
  activeBike = bike;
  bikeModalDetails.innerHTML = "";
  if (bikeModalTitle) {
    bikeModalTitle.textContent = `Bike ${bike.id}`;
  }
  if (bikeModalSubhead) {
    bikeModalSubhead.textContent = bike.model;
  }
  renderDetail("Model", bike.model);
  renderDetail("Color", bike.color);
  renderDetail("Year", String(bike.year));
  renderDetail(
    "Pricing",
    `EUR ${Number(bike.rate_per_minute).toFixed(2)} / min (cap ${Number(bike.price_cap_eur).toFixed(2)})`,
  );
  setRentalState(activeRentals.some((rental) => rental.bike_id === bike.id));
  const modal = window.bootstrap?.Modal.getOrCreateInstance(bikeModalEl);
  modal?.show();
}

function openBookModal(book) {
  if (!bookModalEl || !bookModalDetails) {
    return;
  }
  activeBook = book;
  bookModalDetails.innerHTML = "";
  if (bookModalTitle) {
    bookModalTitle.textContent = `Book ${book.id}`;
  }
  if (bookModalSubhead) {
    bookModalSubhead.textContent = book.title;
  }
  renderBookDetail("Title", book.title);
  renderBookDetail("Author", book.author);
  renderBookDetail("Upfront fee", `EUR ${Number(book.price).toFixed(2)}`);
  setBookLoanState(activeBookLoans.some((loan) => loan.book_id === book.id));
  const modal = window.bootstrap?.Modal.getOrCreateInstance(bookModalEl);
  modal?.show();
}

function setRentalState(isRented) {
  if (bikeRentAction) {
    bikeRentAction.disabled = isRented;
  }
}

function setBookLoanState(isLoaned) {
  if (bookLoanAction) {
    bookLoanAction.disabled = isLoaned;
  }
}

function updateAccountSnapshot(email, userId) {
  if (guestEmail) {
    guestEmail.textContent = email || "--";
  }
  if (guestUserId) {
    guestUserId.textContent = userId || "--";
  }
  if (guestBaseUrl) {
    guestBaseUrl.textContent = state.baseUrl;
  }
}

function showNotice(message, variant = "info") {
  if (!guestNotice) {
    return;
  }
  guestNotice.textContent = message;
  guestNotice.classList.remove("hidden", "notice-info", "notice-success", "notice-error");
  guestNotice.classList.add(`notice-${variant}`);
}

async function fetchAvailableBikes() {
  if (!state.bearerToken) {
    return null;
  }
  try {
    const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/bikes`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    if (Array.isArray(payload)) {
      return payload;
    }
  } catch (err) {
    // Fallback to defaults.
  }
  return null;
}

async function fetchActiveRentals() {
  if (!state.bearerToken) {
    return null;
  }
  try {
    const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/rentals/active`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    if (Array.isArray(payload)) {
      return payload;
    }
  } catch (err) {
    // Ignore errors.
  }
  return null;
}

async function fetchBooks() {
  if (!state.bearerToken) {
    return null;
  }
  try {
    const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/books`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    if (Array.isArray(payload)) {
      return payload;
    }
  } catch (err) {
    // Ignore errors.
  }
  return null;
}

async function fetchActiveBookLoans() {
  if (!state.bearerToken) {
    return null;
  }
  try {
    const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/book-loans/active`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    if (!response.ok) {
      return null;
    }
    const payload = await response.json();
    if (Array.isArray(payload)) {
      return payload;
    }
  } catch (err) {
    // Ignore errors.
  }
  return null;
}

async function startRental(bikeId) {
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/rentals/start-auth`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.bearerToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ bike_id: bikeId }),
  });
  if (!response.ok) {
    throw new Error("Unable to start rental.");
  }
}

async function stopRental(rentalId) {
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/rentals/stop-auth`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.bearerToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rental_id: rentalId }),
  });
  if (!response.ok) {
    throw new Error("Unable to stop rental.");
  }
  return response.json();
}

async function startBookLoan(bookId) {
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/book-loans/start`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.bearerToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ book_id: bookId }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload?.detail || "Unable to lend book.";
    throw new Error(message);
  }
  return response.json();
}

async function stopBookLoan(loanId) {
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/book-loans/stop`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.bearerToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ loan_id: loanId }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload?.detail || "Unable to return book.";
    throw new Error(message);
  }
  return response.json();
}

function renderRentedList() {
  if (!rentedList) {
    return;
  }
  rentedList.innerHTML = "";
  if (!activeRentals.length) {
    const empty = document.createElement("li");
    empty.className = "item-empty";
    empty.textContent = "No rentals yet for this account.";
    rentedList.appendChild(empty);
    return;
  }
  activeRentals.forEach((rental) => {
    const li = document.createElement("li");
    li.className = "item-row item-row-split";
    const label = document.createElement("span");
    label.className = "item-label";
    const bikeLabel = rental.bike_model ? `${rental.bike_model} (${rental.bike_id})` : `Bike ${rental.bike_id}`;
    label.textContent = bikeLabel;
    const price = computeRentalPrice(rental);
    const priceTag = document.createElement("span");
    priceTag.className = "item-right";
    priceTag.textContent = price ? `${price} EUR` : "--";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mini-action";
    button.textContent = "Return";
    button.addEventListener("click", async () => {
      try {
        const summary = await stopRental(rental.rental_id);
        await refreshBalance();
        await renderBikes();
        const rawPrice = summary?.price_eur;
        const priceValue = Number(rawPrice);
        const modalText = Number.isNaN(priceValue)
          ? "Rental ended."
          : `Rental ended. Amount due: EUR ${priceValue.toFixed(2)}.`;
        showNotice(modalText, "success");
      } catch (err) {
        showNotice("Unable to return the bike right now.", "error");
      }
    });
    li.appendChild(label);
    li.appendChild(priceTag);
    li.appendChild(button);
    rentedList.appendChild(li);
  });
}

function renderLoanedList() {
  if (!loanedList) {
    return;
  }
  loanedList.innerHTML = "";
  if (!activeBookLoans.length) {
    const empty = document.createElement("li");
    empty.className = "item-empty";
    empty.textContent = "No active book loans yet.";
    loanedList.appendChild(empty);
    return;
  }
  activeBookLoans.forEach((loan) => {
    const li = document.createElement("li");
    li.className = "item-row item-row-split";
    const label = document.createElement("span");
    label.className = "item-label";
    const title = loan.title ? `${loan.title} (${loan.book_id})` : `Book ${loan.book_id}`;
    label.textContent = title;
    const dueAt = loan.due_at ? new Date(loan.due_at) : null;
    const dueLabel = document.createElement("span");
    dueLabel.className = "item-right";
    dueLabel.textContent = dueAt && !Number.isNaN(dueAt.getTime())
      ? `Due ${dueAt.toLocaleTimeString()}`
      : "--";
    const button = document.createElement("button");
    button.type = "button";
    button.className = "mini-action";
    button.textContent = "Return";
    button.addEventListener("click", async () => {
      try {
        const summary = await stopBookLoan(loan.loan_id);
        await refreshBalance();
        await renderBooks();
        const fineNote = summary?.fine_applied ? ` Fine: EUR ${Number(summary.fine_eur).toFixed(2)}.` : "";
        showNotice(`Book returned.${fineNote}`, "success");
      } catch (err) {
        showNotice(err.message || "Unable to return the book right now.", "error");
      }
    });
    li.appendChild(label);
    li.appendChild(dueLabel);
    li.appendChild(button);
    loanedList.appendChild(li);
  });
}

function computeRentalPrice(rental) {
  const rate = Number(rental.rate_per_minute);
  if (Number.isNaN(rate)) {
    return "";
  }
  const start = new Date(rental.started_at);
  if (Number.isNaN(start.getTime())) {
    return "";
  }
  const minutes = Math.max(1, Math.floor((Date.now() - start.getTime()) / 60000));
  const cap = Number(rental.price_cap_eur);
  const raw = rate * minutes;
  const total = Number.isNaN(cap) ? raw : Math.min(raw, cap);
  return total.toFixed(2);
}

function updateTotalDue() {
  if (!guestTotalDue) {
    return;
  }
  const activeTotal = activeRentals.reduce((sum, rental) => {
    const price = Number(computeRentalPrice(rental));
    if (Number.isNaN(price)) {
      return sum;
    }
    return sum + price;
  }, 0);
  const total = Number(balanceDue) + activeTotal;
  guestTotalDue.textContent = `EUR ${total.toFixed(2)}`;
}

async function renderBikes() {
  const [bikeResult, rentalResult] = await Promise.all([
    fetchAvailableBikes(),
    fetchActiveRentals(),
  ]);
  const available = bikeResult === null ? [] : bikeResult;
  activeRentals = rentalResult === null ? [] : rentalResult;
  const availableItems = available.map((bike) => ({
    bike,
    label: bike.model || `Bike ${bike.id}`,
    right: `${(Number(bike.rate_per_minute) * 60).toFixed(2)} EUR/hour`,
  }));
  renderList(bikeList, availableItems, "No bikes available right now.", (item) => {
    openBikeModal(item.bike);
  });

  renderRentedList();
  updateTotalDue();
}

renderBikes();

async function renderBooks() {
  const [booksResult, loansResult] = await Promise.all([
    fetchBooks(),
    fetchActiveBookLoans(),
  ]);
  const allBooks = booksResult === null ? [] : booksResult;
  activeBookLoans = loansResult === null ? [] : loansResult;
  const available = allBooks.filter((book) => book.in_stock);
  const availableItems = available.map((book) => ({
    book,
    label: book.title || `Book ${book.id}`,
    right: book.author || "",
  }));
  renderList(bookList, availableItems, "No books available right now.", (item) => {
    openBookModal(item.book);
  });
  renderLoanedList();
}

renderBooks();

async function ensureGuestAccess() {
  if (!state.bearerToken) {
    return;
  }
  try {
    const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/access`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    const payload = await response.json();
    const email = payload?.email || "";
    const userId = payload?.user_id || "";
    updateAccountSnapshot(email, userId);
  } catch (err) {
    // Ignore access errors here.
  }
}

updateAccountSnapshot("", "");
ensureGuestAccess();

async function fetchBalance() {
  if (!state.bearerToken) {
    return 0;
  }
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/balance`, {
    headers: { Authorization: `Bearer ${state.bearerToken}` },
  });
  if (!response.ok) {
    return 0;
  }
  const payload = await response.json();
  return Number(payload?.balance_due) || 0;
}

async function payBalance() {
  const response = await fetch(`${state.baseUrl.replace(/\/$/, "")}/balance/pay`, {
    method: "POST",
    headers: { Authorization: `Bearer ${state.bearerToken}` },
  });
  if (!response.ok) {
    throw new Error("Unable to pay balance.");
  }
  const payload = await response.json();
  return Number(payload?.balance_due) || 0;
}

async function refreshBalance() {
  balanceDue = await fetchBalance();
  updateTotalDue();
}

if (payBalanceButton) {
  payBalanceButton.addEventListener("click", async () => {
    try {
      balanceDue = await payBalance();
      updateTotalDue();
      showNotice("Balance paid. Thank you.", "success");
    } catch (err) {
      showNotice("Unable to process payment right now.", "error");
    }
  });
}

refreshBalance();

if (bikeRentAction) {
  bikeRentAction.addEventListener("click", async () => {
    if (!activeBike) {
      return;
    }
    try {
      await startRental(activeBike.id);
      await renderBikes();
      setRentalState(true);
    } catch (err) {
      // No-op for now.
    }
  });
}

if (bookLoanAction) {
  bookLoanAction.addEventListener("click", async () => {
    if (!activeBook) {
      return;
    }
    const confirmed = window.confirm("Lend this book? An upfront fee may apply.");
    if (!confirmed) {
      return;
    }
    try {
      await startBookLoan(activeBook.id);
      await refreshBalance();
      await renderBooks();
      setBookLoanState(true);
    } catch (err) {
      showNotice(err.message || "Unable to lend the book right now.", "error");
    }
  });
}

function setActiveTab(tab) {
  if (!panelBikes || !panelBooks || !tabBikesButton || !tabBooksButton) {
    return;
  }
  const showingBikes = tab === "bikes";
  panelBikes.classList.toggle("hidden", !showingBikes);
  panelBooks.classList.toggle("hidden", showingBikes);
  tabBikesButton.classList.toggle("btn-primary", showingBikes);
  tabBikesButton.classList.toggle("btn-outline-light", !showingBikes);
  tabBooksButton.classList.toggle("btn-primary", !showingBikes);
  tabBooksButton.classList.toggle("btn-outline-light", showingBikes);
}

if (tabBikesButton) {
  tabBikesButton.addEventListener("click", () => setActiveTab("bikes"));
}

if (tabBooksButton) {
  tabBooksButton.addEventListener("click", () => setActiveTab("books"));
}

setActiveTab("bikes");
