from __future__ import annotations

from pydantic import BaseModel, Field


class RouteOption(BaseModel):
    option_id: str
    distance_nm: float = Field(gt=0)
    notes: str = ""


class Route(BaseModel):
    id: str
    origin: str
    destination: str
    distance_nm: float = Field(gt=0)
    route_options: list[RouteOption] = Field(default_factory=list)
    source_ref: str = "synthetic_demo"
