import strawberry
from strawberry import auto
from . import models

@strawberry.django.type(models.Room)
class Room:
    id: auto
    name: auto
    kind: auto