import json
from collections import Counter
from pathlib import Path
import networkx as nx
from .models import Direction, Endpoint, PinDefinition, Project, RuleConfig, ValidationIssue, ValidationResult

DEFAULT_RULES = RuleConfig.model_validate(json.loads((Path(__file__).parent / "rules.json").read_text()))

class RuleEngine:
    def __init__(self, project: Project, rules: RuleConfig = DEFAULT_RULES):
        self.project, self.rules = project, rules
        self.templates = {template.id: template for template in project.templates}
        self.instances = {instance.id: instance for instance in project.instances}

    def resolve(self, endpoint: Endpoint) -> PinDefinition | None:
        instance = self.instances.get(endpoint.component)
        template = self.templates.get(instance.template) if instance else None
        connector = next((x for x in template.connectors if x.id == endpoint.connector), None) if template else None
        return next((x for x in connector.pins if x.pin == endpoint.pin), None) if connector else None

    @staticmethod
    def key(endpoint: Endpoint) -> str:
        return f"{endpoint.component}.{endpoint.connector}.{endpoint.pin}"

    def validate(self) -> ValidationResult:
        issues: list[ValidationIssue] = []
        graph = nx.DiGraph()
        graph.add_nodes_from(self.instances)
        incoming: Counter[str] = Counter()
        for index, connection in enumerate(self.project.connections):
            source, target = self.resolve(connection.from_), self.resolve(connection.to)
            if not source:
                issues.append(ValidationIssue(code="SOURCE_NOT_FOUND", message=f"Source {self.key(connection.from_)} does not exist", connection_index=index))
            if not target:
                issues.append(ValidationIssue(code="TARGET_NOT_FOUND", message=f"Target {self.key(connection.to)} does not exist", connection_index=index))
            if not source or not target:
                continue
            allowed = target.type in self.rules.pin_types.get(source.type, type("Empty", (), {"can_connect_to": []})()).can_connect_to
            reverse = source.type in self.rules.pin_types.get(target.type, type("Empty", (), {"can_connect_to": []})()).can_connect_to
            if not (allowed or reverse or source.type == target.type):
                issues.append(ValidationIssue(code="TYPE_MISMATCH", message=f"{source.type} cannot connect to {target.type}", connection_index=index))
            pair = (source.direction.value, target.direction.value)
            if source.direction == target.direction and source.direction != Direction.BIDIRECTIONAL and pair not in self.rules.direction_exceptions:
                issues.append(ValidationIssue(code="DIRECTION_MISMATCH", message=f"{pair[0]} to {pair[1]} is not allowed", connection_index=index))
            incoming[self.key(connection.to)] += 1
            graph.add_edge(connection.from_.component, connection.to.component, index=index)
        for endpoint, count in incoming.items():
            if count > 1:
                issues.append(ValidationIssue(code="DUPLICATE_INCOMING", message=f"{endpoint} has {count} incoming connections"))
        cycles = list(nx.simple_cycles(graph))
        for cycle in cycles:
            issues.append(ValidationIssue(code="CYCLE", message=f"Cycle detected: {' -> '.join(cycle + [cycle[0]])}"))
        disconnected = list(nx.isolates(graph))
        return ValidationResult(valid=not any(x.severity == "error" for x in issues), issues=issues, graph={"cycles": cycles, "disconnected_nodes": disconnected, "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()})

def export_rows(project: Project) -> list[dict]:
    engine = RuleEngine(project)
    rows = []
    for connection in project.connections:
        source, target = engine.resolve(connection.from_), engine.resolve(connection.to)
        if not source or not target:
            continue
        rows.append({"From Device": connection.from_.component, "From Connector": connection.from_.connector, "From Pin": connection.from_.pin, "From Signal": source.name, "From Type": source.type, "To Device": connection.to.component, "To Connector": connection.to.connector, "To Pin": connection.to.pin, "To Signal": target.name, "To Type": target.type})
    return rows
