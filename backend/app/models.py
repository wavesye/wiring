from enum import Enum
from pydantic import BaseModel, Field, model_validator

class Direction(str, Enum):
    IN = "IN"
    OUT = "OUT"
    BIDIRECTIONAL = "BIDIRECTIONAL"

class PinDefinition(BaseModel):
    pin: int = Field(gt=0)
    name: str
    type: str
    direction: Direction = Direction.BIDIRECTIONAL
    allow_multiple: bool = False

class ConnectorDefinition(BaseModel):
    id: str
    pin_count: int = Field(gt=0)
    pins: list[PinDefinition]

    @model_validator(mode="after")
    def unique_pins(self):
        numbers = [pin.pin for pin in self.pins]
        if len(numbers) != len(set(numbers)):
            raise ValueError("Pin numbers must be unique within a connector")
        if any(pin > self.pin_count for pin in numbers):
            raise ValueError("Pin number exceeds pin_count")
        return self

class ComponentTemplate(BaseModel):
    id: str
    name: str
    connectors: list[ConnectorDefinition]

class ComponentInstance(BaseModel):
    id: str
    template: str

class Endpoint(BaseModel):
    component: str
    connector: str
    pin: int = Field(gt=0)

class Connection(BaseModel):
    from_: Endpoint = Field(alias="from")
    to: Endpoint

    model_config = {"populate_by_name": True}

class RuleDefinition(BaseModel):
    can_connect_to: list[str]

class RuleConfig(BaseModel):
    pin_types: dict[str, RuleDefinition]
    direction_exceptions: list[tuple[str, str]] = []

class Project(BaseModel):
    templates: list[ComponentTemplate]
    instances: list[ComponentInstance]
    connections: list[Connection]

class ValidationIssue(BaseModel):
    code: str
    message: str
    connection_index: int | None = None
    severity: str = "error"

class ValidationResult(BaseModel):
    valid: bool
    issues: list[ValidationIssue]
    graph: dict
