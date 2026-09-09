import json,re
from collections import Counter
from pathlib import Path
import networkx as nx
from .models import Direction,Endpoint,PinDefinition,Project,RuleConfig,ValidationResult,ValidationSummary,ValidationViolation

DEFAULT_RULES=RuleConfig.model_validate_json((Path(__file__).parent/"rules.json").read_text())

class RuleEngine:
    def __init__(self,project:Project,templates,rules:RuleConfig=DEFAULT_RULES):
        self.project=project;self.rules=rules;self.templates={t.id:t for t in templates};self.instances={i.id:i for i in project.instances}
    @staticmethod
    def key(e:Endpoint):return f"{e.component}::{e.connector}::{e.pin}"
    def resolve(self,e:Endpoint)->PinDefinition|None:
        instance=self.instances.get(e.component);template=self.templates.get(instance.template_id) if instance else None
        connector=next((c for c in template.connectors if c.id==e.connector),None) if template else None
        return next((p for p in connector.pins if p.number==e.pin),None) if connector else None
    def component_type(self,instance_id):
        i=self.instances.get(instance_id);t=self.templates.get(i.template_id) if i else None;return t.name if t else None
    def violation(self,rule,message,connection=None,severity="error"):
        return ValidationViolation(rule_id=rule,severity=severity,message=message,connection_id=connection.id if connection else None,from_=connection.from_ if connection else None,to=connection.to if connection else None)
    def validate(self)->ValidationResult:
        violations=[];pin_graph=nx.DiGraph();component_graph=nx.DiGraph();component_graph.add_nodes_from(self.instances)
        for instance in self.project.instances:
            template=self.templates.get(instance.template_id)
            if not template:
                violations.append(self.violation("TEMPLATE_REFERENCE",f"Template {instance.template_id} for {instance.id} does not exist"));continue
            for connector in template.connectors:
                for pin in connector.pins:pin_graph.add_node(f"{instance.id}::{connector.id}::{pin.number}",component=instance.id,connector=connector.id,pin=pin.number)
        incoming=Counter()
        for connection in self.project.connections:
            source,target=self.resolve(connection.from_),self.resolve(connection.to)
            if not source:violations.append(self.violation("PIN_REFERENCE",f"Source {self.key(connection.from_)} does not exist",connection))
            if not target:violations.append(self.violation("PIN_REFERENCE",f"Target {self.key(connection.to)} does not exist",connection))
            if not source or not target:continue
            allowed=target.type in self.rules.pin_types.get(source.type,[]) or source.type in self.rules.pin_types.get(target.type,[])
            if not allowed:violations.append(self.violation("PIN_TYPE",f"{source.type} cannot connect to {target.type}",connection))
            pair=(source.direction,target.direction)
            direction_ok=(source.direction in (Direction.OUT,Direction.BIDIRECTIONAL) and target.direction in (Direction.IN,Direction.BIDIRECTIONAL)) or pair in self.rules.direction_exceptions
            if not direction_ok:violations.append(self.violation("DIRECTION",f"{source.direction.value} to {target.direction.value} is not allowed",connection))
            incoming[self.key(connection.to)]+=1;pin_graph.add_edge(self.key(connection.from_),self.key(connection.to),connection_id=connection.id);component_graph.add_edge(connection.from_.component,connection.to.component,connection_id=connection.id)
        for endpoint,count in incoming.items():
            target_connection=next(c for c in self.project.connections if self.key(c.to)==endpoint);pin=self.resolve(target_connection.to)
            if count>1 and pin and not pin.allow_multiple:violations.append(self.violation("DUPLICATE_INCOMING",f"{endpoint} has {count} incoming connections but allow_multiple is false",target_connection))
        component_cycles=list(nx.simple_cycles(component_graph))
        for cycle in component_cycles:violations.append(self.violation("CYCLE",f"Cycle detected: {' -> '.join(cycle+[cycle[0]])}"))
        violations.extend(self.validate_sequential(component_graph))
        violations.extend(self.validate_paths(component_graph))
        disconnected=list(nx.isolates(component_graph))
        for instance in disconnected:violations.append(self.violation("DISCONNECTED_COMPONENT",f"{instance} has no connections",severity="warning"))
        errors=sum(v.severity=="error" for v in violations);warnings=sum(v.severity=="warning" for v in violations)
        return ValidationResult(valid=errors==0,summary=ValidationSummary(errors=errors,warnings=warnings),violations=violations,graph={"pin_nodes":pin_graph.number_of_nodes(),"pin_edges":pin_graph.number_of_edges(),"cycles":component_cycles,"disconnected_components":disconnected})
    def validate_sequential(self,graph):
        violations=[]
        for rule in self.rules.sequential_chains:
            members=[i.id for i in self.project.instances if self.component_type(i.id) in (rule.component_type,) or i.template_id==rule.component_type]
            def order(value):
                match=re.search(r"(\d+)$",value);return (int(match.group(1)) if match else 10**9,value)
            members.sort(key=order);positions={value:index for index,value in enumerate(members)};matched=set()
            for connection in self.project.connections:
                if connection.from_.component not in positions or connection.to.component not in positions:continue
                if connection.from_.connector!=rule.from_connector or connection.to.connector!=rule.to_connector:continue
                expected=positions[connection.from_.component]+1;actual=positions[connection.to.component]
                if actual!=expected:violations.append(self.violation(rule.id,f"Sequential chain skips or reverses order: {connection.from_.component} -> {connection.to.component}",connection))
                else:matched.add((connection.from_.component,connection.to.component))
            for source,target in zip(members,members[1:]):
                if (source,target) not in matched:violations.append(self.violation(rule.id,f"Sequential chain link missing: {source}.{rule.from_connector} -> {target}.{rule.to_connector}"))
        return violations
    def validate_paths(self,graph):
        violations=[]
        for rule in self.rules.paths:
            sources=[i.id for i in self.project.instances if self.component_type(i.id)==rule.from_component_type];targets=[i.id for i in self.project.instances if self.component_type(i.id)==rule.to_component_type]
            if rule.required and sources and targets and not any(nx.has_path(graph,s,t) for s in sources for t in targets):violations.append(self.violation(rule.id,f"No path from {rule.from_component_type} to {rule.to_component_type}"))
        return violations

EXPORT_COLUMNS=["From Device","From Connector","From Pin","From Signal","From Type","To Device","To Connector","To Pin","To Signal","To Type"]
def export_rows(project,templates):
    engine=RuleEngine(project,templates);rows=[]
    for c in project.connections:
        a,b=engine.resolve(c.from_),engine.resolve(c.to)
        if a and b:rows.append(dict(zip(EXPORT_COLUMNS,[c.from_.component,c.from_.connector,c.from_.pin,a.name,a.type,c.to.component,c.to.connector,c.to.pin,b.name,b.type])))
    return rows
