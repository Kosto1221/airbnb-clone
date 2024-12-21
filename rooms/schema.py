import strawberry
import typing
from . import types
from . import queries

@strawberry.type
class Query:
    all_rooms: typing.List[types.Room] = strawberry.field(resolver=queries.get_all_rooms)
