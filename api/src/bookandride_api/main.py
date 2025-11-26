from __future__ import annotations

import json
<<<<<<< HEAD:api/main.py
<<<<<<< HEAD
=======
import logging
>>>>>>> origin/green:api/src/bookandride_api/main.py
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import xmltodict
import yaml
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
=======
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import xmltodict
import yaml
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
>>>>>>> temp-repo-b-branch
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import DecodeError
from jsonschema import ValidationError, validate
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
<<<<<<< HEAD:api/main.py
from pydantic import BaseModel, Field, field_validator
<<<<<<< HEAD
from sqlmodel import Session, SQLModel, create_engine

from book_pb2 import Book as PbBook
from rental_pb2 import PartnerRental as PbPartnerRental
from models import BookRecord, PartnerRentalRecord, RentalRecord
=======
from sqlmodel import Session, select

try:
    from .auth import (
        create_access_token,
        get_current_user,
        hash_password,
        require_partner_token,
        require_user_actor,
        verify_password,
    )
    from .book_pb2 import Book as PbBook
    from .rental_pb2 import PartnerRental as PbPartnerRental
    from .models import BookRecord, PartnerRentalRecord, RentalRecord, User, get_session, init_db
    from .schemas import LoginIn, MeOut, RegisterIn, TokenOut
except ImportError:  # Fallback when running as a top-level module
    from auth import (
        create_access_token,
        get_current_user,
        hash_password,
        require_partner_token,
        require_user_actor,
        verify_password,
    )
    from book_pb2 import Book as PbBook
    from rental_pb2 import PartnerRental as PbPartnerRental
    from models import BookRecord, PartnerRentalRecord, RentalRecord, User, get_session, init_db
    from schemas import LoginIn, MeOut, RegisterIn, TokenOut
>>>>>>> temp-repo-b-branch
=======
from sqlmodel import Session

from .auth import verify_api_key
from .book_pb2 import Book as PbBook
from .config_loader import load_config
from .database import engine, get_session, init_db
from .logging_utils import configure_logging, log_user_action
from .logging_config import logger as basic_logger
from .models import BookRecord, PartnerRentalRecord, RentalRecord
from .rental_pb2 import PartnerRental as PbPartnerRental
from .schemas import Book, PartnerRental, RentalStartRequest, RentalStartResponse, RentalStopRequest, RentalStopResponse
>>>>>>> origin/green:api/src/bookandride_api/main.py


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Book & Ride API", version="1.0.0", lifespan=lifespan)


BASE_DIR = Path(__file__).resolve().parent
BOOK_SCHEMA_PATH = BASE_DIR / "schemas" / "book.schema.json"
RENTAL_SCHEMA_PATH = BASE_DIR / "schemas" / "rental.schema.json"
BOOK_JSON_SCHEMA = json.loads(BOOK_SCHEMA_PATH.read_text())
RENTAL_SCHEMA = json.loads(RENTAL_SCHEMA_PATH.read_text())


SUPPORTED_MEDIA_TYPES: Dict[str, str] = {
    "application/json": "json",
    "application/xml": "xml",
    "application/x-yaml": "yaml",
    "application/x-protobuf": "proto",
}

<<<<<<< HEAD:api/main.py
<<<<<<< HEAD
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bookandride.db")
CONNECT_ARGS: dict[str, Any] = {}
if DATABASE_URL.startswith("sqlite"):
    CONNECT_ARGS["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)
=======
@app.on_event("startup")
def on_startup() -> None:
    init_db()
>>>>>>> temp-repo-b-branch


class Book(BaseModel):
    id: int = Field(gt=0)
    title: str
    author: str
    price: float = Field(ge=0)
    in_stock: bool


class PartnerRental(BaseModel):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    bike_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    price_eur: float = Field(ge=0)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def ensure_iso8601(cls, value: Any):
        if value is None:
            return value
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix") from exc
            return parsed.astimezone(timezone.utc)
        raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix")


class RentalStartRequest(BaseModel):
    bike_id: str = Field(min_length=1)


class RentalStartResponse(BaseModel):
    rental_id: int
    started_at: datetime


class RentalStopRequest(BaseModel):
    rental_id: int = Field(gt=0)


class RentalStopResponse(BaseModel):
    duration_min: int
    price_eur: float


<<<<<<< HEAD
API_KEYS: Dict[str, str] = {
    "dev-key-123": "user1",
    "admin-key-456": "admin",
}
=======
configure_logging()
LOGGER = logging.getLogger("bookride.api")
CONFIG = load_config()
CURRENT_ENV = os.getenv("APP_ENV", "dev")


@app.get("/info", tags=["system"])
def info():
    return {
        "environment": CURRENT_ENV,
        "db": CONFIG["DB_URL"],
        "service_url": CONFIG["SERVICE_URL"],
        "debug": CONFIG["DEBUG"],
    }
>>>>>>> origin/green:api/src/bookandride_api/main.py


=======
>>>>>>> temp-repo-b-branch
REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests served")


@app.middleware("http")
async def observability_logging(request: Request, call_next):
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        LOGGER.error(
            "request failed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": 500,
                "response_time_ms": duration_ms,
            },
            exc_info=True,
        )
        raise
    duration_ms = int((time.perf_counter() - start_time) * 1000)
    log_fn = LOGGER.error if response.status_code >= 500 else LOGGER.info
    log_fn(
        "request completed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "response_time_ms": duration_ms,
        },
    )
    return response


@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/metrics":
        REQUEST_COUNT.inc()
    return response


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


<<<<<<< HEAD:api/main.py
<<<<<<< HEAD
def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    user = API_KEYS.get(x_api_key)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return user


=======
>>>>>>> temp-repo-b-branch
=======
>>>>>>> origin/green:api/src/bookandride_api/main.py
def coerce_book_payload(payload: dict[str, Any]) -> None:
    try:
        payload["id"] = int(payload["id"])
        payload["price"] = float(payload["price"])
        payload["in_stock"] = str(payload["in_stock"]).lower() in {"true", "1"}
    except KeyError:
        return
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_xml", "message": "XML payload has invalid field types"},
        ) from exc


def coerce_partner_rental_payload(payload: dict[str, Any]) -> None:
    try:
        if "id" in payload:
            payload["id"] = int(payload["id"])
        if "user_id" in payload:
            payload["user_id"] = int(payload["user_id"])
        if "price_eur" in payload:
            payload["price_eur"] = float(payload["price_eur"])
        for key in ("start_time", "end_time"):
            if key in payload and payload[key] is not None:
                payload[key] = str(payload[key])
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_xml", "message": "XML payload has invalid field types"},
        ) from exc


XML_COERCERS: dict[str, Callable[[dict[str, Any]], None]] = {
    "book": coerce_book_payload,
    "rental": coerce_partner_rental_payload,
}


def parse_pretty_flag(raw: Optional[str]) -> bool:
    if raw is None:
        return True
    normalized = raw.strip().lower()
    if normalized in {"false", "0", "no", "compact"}:
        return False
    if normalized in {"true", "1", "yes", "pretty"}:
        return True
    return True


def size_headers(pretty_body: str, compact_body: str, actual_body: str) -> dict[str, str]:
    pretty_len = len(pretty_body.encode("utf-8"))
    compact_len = len(compact_body.encode("utf-8"))
    actual_len = len(actual_body.encode("utf-8"))
    return {
        "X-Pretty-Length": str(pretty_len),
        "X-Compact-Length": str(compact_len),
        "X-Body-Length": str(actual_len),
        "X-Length-Diff": str(pretty_len - compact_len),
    }


def negotiate_book_accept(accept_header: Optional[str]) -> str:
    if not accept_header:
        return "application/json"
    accepts = [value.strip().lower() for value in accept_header.split(",") if value.strip()]
    for media_type in SUPPORTED_MEDIA_TYPES:
        if any(value.startswith(media_type) for value in accepts):
            return media_type
    if "*/*" in accepts:
        return "application/json"
    raise HTTPException(status_code=406, detail="Not Acceptable")


UNSAFE_XML_TOKENS = (b"<!DOCTYPE", b"<!ENTITY", b"<![CDATA[")


def enforce_safe_xml(raw_body: bytes) -> None:
    sample = raw_body.upper()
    if any(token in sample for token in UNSAFE_XML_TOKENS):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_xml", "message": "XML DTDs and entities are not supported"},
        )


def strip_namespaces(value: Any) -> Any:
    if isinstance(value, dict):
        stripped: dict[str, Any] = {}
        for key, item in value.items():
            if key.startswith("@"):
                continue
            local_key = key.split(":", 1)[1] if ":" in key else key
            stripped[local_key] = strip_namespaces(item)
        return stripped
    if isinstance(value, list):
        return [strip_namespaces(item) for item in value]
    return value


def normalize_mapping_or_sequence(value: Any, root_tag: Optional[str]) -> dict[str, Any] | list[dict[str, Any]]:
    tag = f"<{root_tag}>" if root_tag else "object"
    if isinstance(value, list):
        normalized: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=422,
                    detail={"error": "invalid_xml", "message": f"XML payload must contain dictionaries under {tag}"},
                )
            normalized.append(dict(item))
        return normalized
    if isinstance(value, dict):
        return dict(value)
    raise HTTPException(
        status_code=422,
        detail={"error": "invalid_xml", "message": f"XML payload must map to {tag} elements"},
    )


def _parse_payload(
    request_body: bytes,
    content_type: Optional[str],
    root_tag: Optional[str],
) -> dict[str, Any] | list[dict[str, Any]]:
    if not content_type:
        raise HTTPException(status_code=415, detail="Content-Type header required")

    if content_type == "application/json":
        try:
            return json.loads(request_body)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_json", "message": str(exc)},
            ) from exc

    if content_type == "application/xml":
        enforce_safe_xml(request_body)
        try:
            obj = xmltodict.parse(request_body)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_xml", "message": str(exc)},
            ) from exc

        parsed_obj = strip_namespaces(obj)

        value: Any
        if root_tag:
            if root_tag in parsed_obj:
                value = parsed_obj[root_tag]
            elif f"{root_tag}s" in parsed_obj:
                container = parsed_obj[f"{root_tag}s"]
                if isinstance(container, dict) and root_tag in container:
                    value = container[root_tag]
                else:
                    value = container
            else:
                value = parsed_obj
        else:
            if isinstance(parsed_obj, dict) and len(parsed_obj) == 1:
                sole_value = next(iter(parsed_obj.values()))
                if isinstance(sole_value, (dict, list)):
                    value = sole_value
                else:
                    value = parsed_obj
            else:
                value = parsed_obj

        payload = normalize_mapping_or_sequence(value, root_tag)

        coercer = XML_COERCERS.get(root_tag or "")
        if coercer:
            if isinstance(payload, list):
                for item in payload:
                    coercer(item)
            else:
                coercer(payload)

        return payload

    if content_type == "application/x-yaml":
        try:
            data = yaml.safe_load(request_body)
        except yaml.YAMLError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_yaml", "message": str(exc)},
            ) from exc
        if not isinstance(data, (dict, list)):
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_yaml", "message": "YAML payload must decode to an object or list"},
            )
        return data

    if content_type == "application/x-protobuf":
        if root_tag == "rental":
            pb = PbPartnerRental()
        else:
            pb = PbBook()
        try:
            pb.ParseFromString(request_body)
        except DecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_protobuf", "message": str(exc)},
            ) from exc
        return MessageToDict(pb, preserving_proto_field_name=True)

    raise HTTPException(status_code=415, detail="Unsupported Media Type")


def parse_body(raw: bytes, content_type: str) -> dict[str, Any]:
    if not content_type:
        raise HTTPException(status_code=415, detail="Content-Type header required")

    if content_type not in SUPPORTED_MEDIA_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")

    if content_type == "application/json":
        try:
            data: Any = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_json", "message": str(exc)},
            ) from exc
    elif content_type == "application/xml":
        payload = _parse_payload(raw, content_type, "book")
        if isinstance(payload, list):
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_xml", "message": "XML payload must describe a single book"},
            )
        data = payload
    elif content_type == "application/x-yaml":
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_yaml", "message": str(exc)},
            ) from exc
    elif content_type == "application/x-protobuf":
        pb = PbBook()
        try:
            pb.ParseFromString(raw)
        except DecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_protobuf", "message": str(exc)},
            ) from exc
        data = MessageToDict(pb, preserving_proto_field_name=True)
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_payload", "message": "Book payload must be a mapping"},
        )

    try:
        validate(instance=data, schema=BOOK_JSON_SCHEMA)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "schema_validation", "message": exc.message, "path": list(exc.path)},
        ) from exc

    book = Book(**data)
    return book.model_dump()


def render_book(book: dict[str, Any], accept: str, pretty: bool) -> Response:
    if accept == "application/json":
        pretty_json = json.dumps(book, ensure_ascii=False, indent=2)
        compact_json = json.dumps(book, ensure_ascii=False, separators=(",", ":"))
        body = pretty_json if pretty else compact_json
        return Response(
            content=body,
            media_type=accept,
            headers=size_headers(pretty_json, compact_json, body),
        )
    if accept == "application/xml":
        xml_payload = {"book": book}
        pretty_xml = xmltodict.unparse(xml_payload, pretty=True)
        compact_xml = xmltodict.unparse(xml_payload, pretty=False)
        body = pretty_xml if pretty else compact_xml
        return Response(
            content=body,
            media_type=accept,
            headers=size_headers(pretty_xml, compact_xml, body),
        )
    if accept == "application/x-yaml":
        yaml_body = yaml.safe_dump(book, sort_keys=False)
        return Response(
            content=yaml_body,
            media_type=accept,
            headers=size_headers(yaml_body, yaml_body, yaml_body),
        )
    if accept == "application/x-protobuf":
        pb = PbBook()
        ParseDict(book, pb, ignore_unknown_fields=True)
        payload = pb.SerializeToString()
        return Response(
            content=payload,
            media_type=accept,
            headers={"X-Body-Length": str(len(payload))},
        )
    raise HTTPException(status_code=500, detail="Unsupported Accept header")


def render(data: dict[str, Any] | list[dict[str, Any]], accept: str, root_tag: str, pretty: bool) -> Response:
    if accept == "application/xml":
        namespace = "urn:book" if root_tag == "book" else None

        def namespace_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
            if not namespace:
                return mapping
            namespaced: dict[str, Any] = {}
            for key, value in mapping.items():
                if key.startswith("@") or key.startswith("#"):
                    namespaced[key] = value
                    continue
                namespaced_key = f"b:{key}"
                if isinstance(value, dict):
                    namespaced[namespaced_key] = namespace_mapping(value)
                elif isinstance(value, list):
                    namespaced[namespaced_key] = [
                        namespace_mapping(item) if isinstance(item, dict) else item for item in value
                    ]
                else:
                    namespaced[namespaced_key] = value
            return namespaced

        if isinstance(data, list):
            if namespace:
                payload_list = [namespace_mapping(item) for item in data]
                container_tag = f"{root_tag}s"
                xml_payload: dict[str, Any] = {
                    container_tag: {
                        "@xmlns:b": namespace,
                        "b:book": payload_list,
                    }
                }
            else:
                payload_list = data
                xml_payload = {f"{root_tag}s": {root_tag: payload_list}}
        else:
            if namespace:
                payload = namespace_mapping(data)
                xml_payload = {
                    "b:book": {
                        "@xmlns:b": namespace,
                        **payload,
                    }
                }
            else:
                xml_payload = {root_tag: data}

        pretty_xml = xmltodict.unparse(xml_payload, pretty=True)
        compact_xml = xmltodict.unparse(xml_payload, pretty=False)
        body = pretty_xml if pretty else compact_xml
        return Response(
            content=body,
            media_type="application/xml",
            headers=size_headers(pretty_xml, compact_xml, body),
        )

    if accept == "application/json":
        pretty_json = json.dumps(data, ensure_ascii=False, indent=2)
        compact_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        body = pretty_json if pretty else compact_json
        return Response(
            content=body,
            media_type="application/json",
            headers=size_headers(pretty_json, compact_json, body),
        )

    if accept == "application/x-yaml":
        yaml_body = yaml.safe_dump(data, sort_keys=False)
        return Response(
            content=yaml_body,
            media_type="application/x-yaml",
            headers=size_headers(yaml_body, yaml_body, yaml_body),
        )

    if accept == "application/x-protobuf":
        if root_tag != "rental":
            raise HTTPException(status_code=500, detail="Unsupported Accept header")
        if not isinstance(data, dict):
            raise HTTPException(status_code=500, detail="Unsupported payload shape for protobuf rendering")
        pb = PbPartnerRental()
        ParseDict(data, pb, ignore_unknown_fields=True)
        payload = pb.SerializeToString()
        return Response(
            content=payload,
            media_type="application/x-protobuf",
            headers={"X-Body-Length": str(len(payload))},
        )

    raise HTTPException(status_code=500, detail="Unsupported Accept header")



def negotiate_accept(accept_header: Optional[str]) -> str:
    if not accept_header:
        return "application/json"
    accepts = [value.strip().lower() for value in accept_header.split(",") if value.strip()]
    for media_type in SUPPORTED_MEDIA_TYPES:
        if any(value.startswith(media_type) for value in accepts):
            return media_type
    if "*/*" in accepts:
        return "application/json"
    raise HTTPException(status_code=406, detail="Not Acceptable")


@app.post("/books")
<<<<<<< HEAD
async def create_book(request: Request, session: Session = Depends(get_session)) -> Response:
=======
async def create_book(
    request: Request,
    _user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
>>>>>>> temp-repo-b-branch
    content_type = (request.headers.get("Content-Type") or "").split(";")[0]
    body = await request.body()
    payload = parse_body(body, content_type)

    record = session.get(BookRecord, payload["id"])
    if record:
        for key, value in payload.items():
            setattr(record, key, value)
    else:
        record = BookRecord(**payload)
        session.add(record)
    session.commit()
    session.refresh(record)
    stored_payload = record.model_dump()

    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_book_accept(request.headers.get("Accept"))
    response = render_book(stored_payload, accept, pretty)
    response.status_code = status.HTTP_201_CREATED
    return response


<<<<<<< HEAD
@app.get("/books/{book_id}")
async def get_book(book_id: int, request: Request, session: Session = Depends(get_session)) -> Response:
=======
@app.get("/books")
async def list_books(
    request: Request,
    _user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
    records = session.exec(select(BookRecord)).all()
    books = [record.model_dump() for record in records]
    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_book_accept(request.headers.get("Accept"))
    if accept == "application/x-protobuf":
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, detail="Protobuf not supported for book lists")
    return render(books, accept, "book", pretty)


@app.get("/books/{book_id}")
async def get_book(
    book_id: int,
    request: Request,
    _user=Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Response:
>>>>>>> temp-repo-b-branch
    record = session.get(BookRecord, book_id)
    if not record:
        raise HTTPException(status_code=404, detail="Book not found")
    book = record.model_dump()
    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_book_accept(request.headers.get("Accept"))
    return render_book(book, accept, pretty)


@app.post("/rentals")
<<<<<<< HEAD
async def create_partner_rental(request: Request, session: Session = Depends(get_session)) -> Response:
=======
async def create_partner_rental(
    request: Request,
    _claims: Dict[str, Any] = Depends(require_partner_token(["partner.rentals"])),
    session: Session = Depends(get_session),
) -> Response:
>>>>>>> temp-repo-b-branch
    content_type = (request.headers.get("Content-Type") or "").split(";")[0]
    body = await request.body()
    data = _parse_payload(body, content_type, "rental")

    try:
        validate(instance=data, schema=RENTAL_SCHEMA)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "schema_validation", "message": exc.message, "path": list(exc.path)},
        ) from exc

    rental = PartnerRental(**data)
    record_data = rental.model_dump()

    record = session.get(PartnerRentalRecord, rental.id)
    if record:
        for key, value in record_data.items():
            setattr(record, key, value)
    else:
        record = PartnerRentalRecord(**record_data)
        session.add(record)
    session.commit()
    session.refresh(record)
    payload = PartnerRental.model_validate(record.model_dump()).model_dump(mode="json")

    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_accept(request.headers.get("Accept"))
    return render(payload, accept, "rental", pretty)


@app.get("/rentals/{rental_id}")
<<<<<<< HEAD
async def get_partner_rental(rental_id: int, request: Request, session: Session = Depends(get_session)) -> Response:
=======
async def get_partner_rental(
    rental_id: int,
    request: Request,
    _claims: Dict[str, Any] = Depends(require_partner_token(["partner.rentals"])),
    session: Session = Depends(get_session),
) -> Response:
>>>>>>> temp-repo-b-branch
    record = session.get(PartnerRentalRecord, rental_id)
    if not record:
        raise HTTPException(status_code=404, detail="Rental not found")
    rental = PartnerRental.model_validate(record.model_dump()).model_dump(mode="json")
    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_accept(request.headers.get("Accept"))
    return render(rental, accept, "rental", pretty)


def calculate_price(minutes: int) -> float:
    basic_logger.info("Calculating price for %d minutes", minutes)
    base = minutes * 0.25
    return min(base, 12.0)


@app.post("/rentals/start", response_model=RentalStartResponse)
def start_rental(
    payload: RentalStartRequest,
<<<<<<< HEAD
    user: str = Depends(verify_api_key),
    session: Session = Depends(get_session),
) -> RentalStartResponse:
    basic_logger.info("User %s started rental on %s", user, payload.bike_id)
    started_at = datetime.now(tz=timezone.utc)
    record = RentalRecord(user=user, bike_id=payload.bike_id, started_at=started_at)
=======
    principal: str = Depends(require_user_actor(["rentals:write"])),
    session: Session = Depends(get_session),
) -> RentalStartResponse:
    started_at = datetime.now(tz=timezone.utc)
    record = RentalRecord(user=principal, bike_id=payload.bike_id, started_at=started_at)
>>>>>>> temp-repo-b-branch
    session.add(record)
    session.commit()
    session.refresh(record)

    log_user_action(
        LOGGER,
        action="rental_start",
        user_id=user,
        bike_id=payload.bike_id,
        rental_id=record.id,
    )

    return RentalStartResponse(rental_id=record.id, started_at=record.started_at)


@app.post("/rentals/stop", response_model=RentalStopResponse)
def stop_rental(
    payload: RentalStopRequest,
<<<<<<< HEAD
    user: str = Depends(verify_api_key),
    session: Session = Depends(get_session),
) -> RentalStopResponse:
    record = session.get(RentalRecord, payload.rental_id)
    if record is None or record.user != user:
=======
    principal: str = Depends(require_user_actor(["rentals:write"])),
    session: Session = Depends(get_session),
) -> RentalStopResponse:
    record = session.get(RentalRecord, payload.rental_id)
    if record is None or record.user != str(principal):
>>>>>>> temp-repo-b-branch
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")

    if record.stopped_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rental already stopped")

    stopped_at = datetime.now(tz=timezone.utc)
    started_at = record.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    duration_minutes = max(1, int((stopped_at - started_at).total_seconds() // 60))
    price = calculate_price(duration_minutes)
    record.stopped_at = stopped_at
    record.total_minutes = duration_minutes
    record.price_eur = price
    session.add(record)
    session.commit()

    basic_logger.info(
        "Stopping rental",
        extra={
            "user": user,
            "rental_id": record.id,
            "duration_min": duration_minutes,
            "price_eur": price,
        },
    )
    log_user_action(
        LOGGER,
        action="rental_stop",
        user_id=user,
        rental_id=record.id,
        duration_min=duration_minutes,
        price_eur=price,
    )

    return RentalStopResponse(duration_min=duration_minutes, price_eur=price)


@app.post("/convert")
async def convert(request: Request, to: str, pretty: bool = Query(True)) -> Response:
    content_type = (request.headers.get("Content-Type") or "").split(";")[0]
    body = await request.body()
    data = _parse_payload(body, content_type, None)

    target = to.lower()
    if target == "json":
        pretty_json = json.dumps(data, ensure_ascii=False, indent=2)
        compact_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        body_content = pretty_json if pretty else compact_json
        return Response(
            content=body_content,
            media_type="application/json",
            headers=size_headers(pretty_json, compact_json, body_content),
        )
    if target == "xml":
        xml_payload: dict[str, Any]
        if isinstance(data, list):
            xml_payload = {"root": {"item": data}}
        elif isinstance(data, dict):
            xml_payload = {"root": data}
        else:
            raise HTTPException(status_code=400, detail="Unsupported payload type for XML conversion")
        pretty_xml = xmltodict.unparse(xml_payload, pretty=True)
        compact_xml = xmltodict.unparse(xml_payload, pretty=False)
        body_content = pretty_xml if pretty else compact_xml
        return Response(
            content=body_content,
            media_type="application/xml",
            headers=size_headers(pretty_xml, compact_xml, body_content),
        )
    if target == "yaml":
        yaml_body = yaml.safe_dump(data, sort_keys=False)
        return Response(
            content=yaml_body,
            media_type="application/x-yaml",
            headers=size_headers(yaml_body, yaml_body, yaml_body),
        )
    if target == "protobuf":
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Protobuf conversion requires a single object payload")
        pb = PbBook()
        try:
            ParseDict(data, pb, ignore_unknown_fields=True)
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_payload", "message": f"Cannot map payload to Book protobuf: {exc}"},
            ) from exc
        payload = pb.SerializeToString()
        return Response(
            content=payload,
            media_type="application/x-protobuf",
            headers={"X-Body-Length": str(len(payload))},
        )
    raise HTTPException(status_code=400, detail="to must be 'json', 'xml', 'yaml', or 'protobuf'")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "version": app.version}
<<<<<<< HEAD
=======
@app.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterIn,
    session: Session = Depends(get_session),
) -> TokenOut:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
    password_hash = hash_password(payload.password)
    user = User(
        username=payload.email,
        email=payload.email,
        password_hash=password_hash,
        role="user",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(user_id=user.id, email=user.email, role=user.role, scopes=(user.scopes or "").split())
    return TokenOut(access_token=token, token_type="bearer")


@app.post("/login", response_model=TokenOut)
@app.post("/auth/login", response_model=TokenOut)
def login(
    payload: LoginIn,
    session: Session = Depends(get_session),
) -> TokenOut:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user_id=user.id, email=user.email, role=user.role, scopes=(user.scopes or "").split())
    return TokenOut(access_token=token, token_type="bearer")


@app.get("/me", response_model=MeOut)
def me(current: User = Depends(get_current_user)) -> MeOut:
    return MeOut(id=current.id, email=current.email, role=current.role)
>>>>>>> temp-repo-b-branch
