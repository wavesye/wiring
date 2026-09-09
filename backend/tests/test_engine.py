from pathlib import Path
from fastapi.testclient import TestClient
from app.engine import RuleEngine
from app.models import ComponentTemplate,Project,RuleConfig
from app.storage import Storage
import app.main as api

def template(id,name,pins,connector="P1",allow_multiple=False):
    return ComponentTemplate.model_validate({"id":id,"name":name,"connectors":[{"id":connector,"name":connector,"pin_count":max(p[0] for p in pins),"pins":[{"number":n,"name":kind,"type":kind,"direction":direction,"allow_multiple":allow_multiple} for n,kind,direction in pins]}]})
CAN_A=template("CAN_A","SOURCE",[(1,"CAN_H","OUT"),(2,"CAN_L","OUT"),(3,"NTC_SENSOR","OUT"),(4,"POWER_12V_OUT","OUT")])
CAN_B=template("CAN_B","TARGET",[(1,"CAN_H","IN"),(2,"CAN_L","IN"),(3,"GPIO","IN"),(4,"POWER_5V_IN","IN"),(5,"NTC_INPUT","IN")])
def project(connections,instances=None):return Project.model_validate({"id":"p1","name":"Test","instances":instances or [{"id":"SOURCE1","template_id":"CAN_A","position":{"x":0,"y":0}},{"id":"TARGET1","template_id":"CAN_B","position":{"x":100,"y":0}}],"connections":connections})
def connection(id,source_pin,target_pin,source="SOURCE1",target="TARGET1",source_connector="P1",target_connector="P1"):return {"id":id,"from":{"component":source,"connector":source_connector,"pin":source_pin},"to":{"component":target,"connector":target_connector,"pin":target_pin}}
def codes(result):return [v.rule_id for v in result.violations]
def test_valid_can_connection():assert RuleEngine(project([connection("c1",1,1)]),[CAN_A,CAN_B]).validate().valid
def test_can_h_to_can_l():assert "PIN_TYPE" in codes(RuleEngine(project([connection("c1",1,2)]),[CAN_A,CAN_B]).validate())
def test_ntc_to_gpio():assert "PIN_TYPE" in codes(RuleEngine(project([connection("c1",3,3)]),[CAN_A,CAN_B]).validate())
def test_12v_to_5v():assert "PIN_TYPE" in codes(RuleEngine(project([connection("c1",4,4)]),[CAN_A,CAN_B]).validate())
def test_missing_pin():assert "PIN_REFERENCE" in codes(RuleEngine(project([connection("c1",99,1)]),[CAN_A,CAN_B]).validate())
def test_duplicate_incoming():assert "DUPLICATE_INCOMING" in codes(RuleEngine(project([connection("c1",1,1),connection("c2",2,1)]),[CAN_A,CAN_B]).validate())
def test_allow_multiple():
    target=template("MULTI","TARGET",[(1,"CAN_H","IN")],allow_multiple=True);p=project([connection("c1",1,1),connection("c2",1,1)],[{"id":"SOURCE1","template_id":"CAN_A","position":{"x":0,"y":0}},{"id":"TARGET1","template_id":"MULTI","position":{"x":1,"y":1}}]);assert "DUPLICATE_INCOMING" not in codes(RuleEngine(p,[CAN_A,target]).validate())
def bic_project(edges):
    bic=ComponentTemplate.model_validate({"id":"BIC_A","name":"BIC","connectors":[{"id":"P1","name":"in","pin_count":1,"pins":[{"number":1,"name":"IN","type":"DAISY_IN","direction":"IN"}]},{"id":"P2","name":"out","pin_count":1,"pins":[{"number":1,"name":"OUT","type":"DAISY_OUT","direction":"OUT"}]}]});instances=[{"id":f"BIC{i}","template_id":"BIC_A","position":{"x":i*100,"y":0}} for i in range(1,4)];links=[connection(f"c{i}",1,1,s,t,"P2","P1") for i,(s,t) in enumerate(edges)];return project(links,instances),bic
def test_cycle_detection():p,b=bic_project([("BIC1","BIC2"),("BIC2","BIC3"),("BIC3","BIC1")]);assert "CYCLE" in codes(RuleEngine(p,[b]).validate())
def test_sequential_chain_correct():p,b=bic_project([("BIC1","BIC2"),("BIC2","BIC3")]);assert "bic_daisy_chain" not in codes(RuleEngine(p,[b]).validate())
def test_sequential_chain_skip():p,b=bic_project([("BIC1","BIC3")]);assert "bic_daisy_chain" in codes(RuleEngine(p,[b]).validate())
def test_sequential_chain_cycle():p,b=bic_project([("BIC1","BIC2"),("BIC2","BIC3"),("BIC3","BIC1")]);result=RuleEngine(p,[b]).validate();assert "CYCLE" in codes(result) and "bic_daisy_chain" in codes(result)
def test_path_validation():
    rules=RuleConfig.model_validate({"pin_types":{"CAN_H":["CAN_H"]},"paths":[{"id":"source_target_path","from_component_type":"SOURCE","to_component_type":"TARGET"}]});assert "source_target_path" in codes(RuleEngine(project([]),[CAN_A,CAN_B],rules).validate())
def test_persistence_and_csv_export(tmp_path:Path):
    api.storage=Storage(tmp_path/"test.db");client=TestClient(api.app)
    for value in [CAN_A,CAN_B]:assert client.post("/api/component-templates",json=value.model_dump(mode="json",exclude={"created_at","updated_at"})).status_code==201
    created=client.post("/api/projects",json={"name":"Persisted","instances":[{"id":"SOURCE1","template_id":"CAN_A","position":{"x":10,"y":20}},{"id":"TARGET1","template_id":"CAN_B","position":{"x":30,"y":40}}],"connections":[connection("c1",1,1)]});assert created.status_code==201
    project_id=created.json()["id"];reopened=client.get(f"/api/projects/{project_id}").json();assert reopened["instances"][0]["position"]=={"x":10.0,"y":20.0}
    invalid={"name":"Persisted","instances":reopened["instances"],"connections":[connection("c_bad",1,2)]};assert client.put(f"/api/projects/{project_id}",json=invalid).status_code==200;assert client.post(f"/api/projects/{project_id}/validate").json()["valid"] is False
    valid={**invalid,"connections":[connection("c1",1,1)]};assert client.put(f"/api/projects/{project_id}",json=valid).status_code==200;assert client.post(f"/api/projects/{project_id}/validate").json()["valid"] is True
    exported=client.get(f"/api/projects/{project_id}/export/csv");assert exported.status_code==200 and "From Signal" in exported.text and "CAN_H" in exported.text
    excel=client.get(f"/api/projects/{project_id}/export/excel");assert excel.status_code==200 and excel.content[:2]==b"PK"
