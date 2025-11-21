from __future__ import annotations

import json
import logging
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
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.message import DecodeError
from jsonschema import ValidationError, validate
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
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
async def create_book(request: Request, session: Session = Depends(get_session)) -> Response:
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


@app.get("/books/{book_id}")
async def get_book(book_id: int, request: Request, session: Session = Depends(get_session)) -> Response:
    record = session.get(BookRecord, book_id)
    if not record:
        raise HTTPException(status_code=404, detail="Book not found")
    book = record.model_dump()
    pretty = parse_pretty_flag(request.query_params.get("pretty"))
    accept = negotiate_book_accept(request.headers.get("Accept"))
    return render_book(book, accept, pretty)


@app.post("/rentals")
async def create_partner_rental(request: Request, session: Session = Depends(get_session)) -> Response:
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
async def get_partner_rental(rental_id: int, request: Request, session: Session = Depends(get_session)) -> Response:
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
    user: str = Depends(verify_api_key),
    session: Session = Depends(get_session),
) -> RentalStartResponse:
    basic_logger.info("User %s started rental on %s", user, payload.bike_id)
    started_at = datetime.now(tz=timezone.utc)
    record = RentalRecord(user=user, bike_id=payload.bike_id, started_at=started_at)
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
    user: str = Depends(verify_api_key),
    session: Session = Depends(get_session),
) -> RentalStopResponse:
    record = session.get(RentalRecord, payload.rental_id)
    if record is None or record.user != user:
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
