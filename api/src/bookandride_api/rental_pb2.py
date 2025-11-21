from __future__ import annotations

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, symbol_database


def _build_descriptor() -> descriptor_pb2.FileDescriptorProto:
    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = "rental.proto"
    file_proto.package = "bookandride"
    file_proto.syntax = "proto3"

    message = file_proto.message_type.add()
    message.name = "PartnerRental"

    field_id = message.field.add()
    field_id.name = "id"
    field_id.number = 1
    field_id.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_id.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32

    field_user_id = message.field.add()
    field_user_id.name = "user_id"
    field_user_id.number = 2
    field_user_id.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_user_id.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32

    field_bike_id = message.field.add()
    field_bike_id.name = "bike_id"
    field_bike_id.number = 3
    field_bike_id.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_bike_id.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field_start_time = message.field.add()
    field_start_time.name = "start_time"
    field_start_time.number = 4
    field_start_time.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_start_time.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field_end_time = message.field.add()
    field_end_time.name = "end_time"
    field_end_time.number = 5
    field_end_time.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_end_time.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    field_price_eur = message.field.add()
    field_price_eur.name = "price_eur"
    field_price_eur.number = 6
    field_price_eur.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field_price_eur.type = descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE

    return file_proto


_POOL = descriptor_pool.Default()
_SYM_DB = symbol_database.Default()

_serialized = _build_descriptor().SerializeToString()
try:
    DESCRIPTOR = _POOL.AddSerializedFile(_serialized)
except (TypeError, ValueError):
    DESCRIPTOR = _POOL.FindFileByName("rental.proto")

_RENTAL_DESCRIPTOR = DESCRIPTOR.message_types_by_name["PartnerRental"]
PartnerRental = message_factory.GetMessageClass(_RENTAL_DESCRIPTOR)
_SYM_DB.RegisterMessage(PartnerRental)

__all__ = ["PartnerRental"]
