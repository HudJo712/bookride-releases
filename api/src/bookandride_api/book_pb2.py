from __future__ import annotations

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, symbol_database


def _build_descriptor() -> descriptor_pb2.FileDescriptorProto:
    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "book.proto"
    file_proto.package = "bookandride"
    file_proto.syntax = "proto3"

    message = file_proto.message_type.add()
    message.name = "Book"

    field_id = message.field.add()
    field_id.name = "id"
    field_id.number = 1
    field_id.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_id.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32

    field_title = message.field.add()
    field_title.name = "title"
    field_title.number = 2
    field_title.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_title.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field_author = message.field.add()
    field_author.name = "author"
    field_author.number = 3
    field_author.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_author.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field_price = message.field.add()
    field_price.name = "price"
    field_price.number = 4
    field_price.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_price.type = descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE

    field_in_stock = message.field.add()
    field_in_stock.name = "in_stock"
    field_in_stock.number = 5
    field_in_stock.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_in_stock.type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL

    return file_proto


_POOL = descriptor_pool.Default()
_SYM_DB = symbol_database.Default()

_serialized = _build_descriptor().SerializeToString()
try:
    DESCRIPTOR = _POOL.AddSerializedFile(_serialized)
except (TypeError, ValueError):
    DESCRIPTOR = _POOL.FindFileByName("book.proto")

_BOOK_DESCRIPTOR = DESCRIPTOR.message_types_by_name["Book"]
Book = message_factory.GetMessageClass(_BOOK_DESCRIPTOR)
_SYM_DB.RegisterMessage(Book)

__all__ = ["Book"]
