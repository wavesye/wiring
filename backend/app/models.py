from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator

def utc_now() -> datetime: return datetime.now(timezone.utc)

class Direction(str, Enum):
    IN="IN"; OUT="OUT"; BIDIRECTIONAL="BIDIRECTIONAL"

class Position(BaseModel): x: float; y: float

class PinDefinition(BaseModel):
    number: int = Field(gt=0)
    name: str
    type: str
    direction: Direction = Direction.BIDIRECTIONAL
    allow_multiple: bool = False

class ConnectorDefinition(BaseModel):
    id: str
    name: str = ""
    pin_count: int = Field(gt=0)
    pins: list[PinDefinition]
    @model_validator(mode="after")
    def validate_pins(self):
        numbers=[pin.number for pin in self.pins]
        if len(numbers)!=len(set(numbers)): raise ValueError("Pin numbers must be unique within a connector")
        if any(number>self.pin_count for number in numbers): raise ValueError("Pin number exceeds pin_count")
        return self

class ComponentTemplateInput(BaseModel):
    id: str
    name: str
    description: str = ""
    connectors: list[ConnectorDefinition]

class ComponentTemplate(ComponentTemplateInput):
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class ComponentInstance(BaseModel):
    id: str
    template_id: str
    position: Position

class Endpoint(BaseModel):
    component: str
    connector: str
    pin: int = Field(gt=0)

class Connection(BaseModel):
    id: str = Field(default_factory=lambda:f"conn_{uuid4().hex[:12]}")
    from_: Endpoint = Field(alias="from")
    to: Endpoint
    model_config={"populate_by_name":True}

class ProjectInput(BaseModel):
    name: str
    instances: list[ComponentInstance] = []
    connections: list[Connection] = []

class Project(ProjectInput):
    id: str = Field(default_factory=lambda:f"project_{uuid4().hex[:12]}")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class SequentialChainRule(BaseModel):
    id: str
    type: str = "sequential_chain"
    component_type: str
    instance_order: str = "numeric_suffix"
    from_connector: str
    to_connector: str

class PathRule(BaseModel):
    id: str
    from_component_type: str
    to_component_type: str
    required: bool = True

class RuleConfig(BaseModel):
    pin_types: dict[str,list[str]]
    direction_exceptions: list[tuple[Direction,Direction]]=[]
    sequential_chains: list[SequentialChainRule]=[]
    paths: list[PathRule]=[]

class ValidationViolation(BaseModel):
    rule_id: str
    severity: str="error"
    message: str
    connection_id: str|None=None
    from_: Endpoint|None=Field(default=None,alias="from")
    to: Endpoint|None=None
    model_config={"populate_by_name":True}

class ValidationSummary(BaseModel): errors:int; warnings:int
class ValidationResult(BaseModel):
    valid: bool
    summary: ValidationSummary
    violations: list[ValidationViolation]
    graph: dict
