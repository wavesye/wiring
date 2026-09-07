from app.engine import RuleEngine
from app.models import Project

def project(target_type="CAN_H"):
    return Project.model_validate({"templates":[{"id":"A","name":"A","connectors":[{"id":"P1","pin_count":1,"pins":[{"pin":1,"name":"CAN_H","type":"CAN_H","direction":"BIDIRECTIONAL"}]}]},{"id":"B","name":"B","connectors":[{"id":"J1","pin_count":1,"pins":[{"pin":1,"name":target_type,"type":target_type,"direction":"BIDIRECTIONAL"}]}]}],"instances":[{"id":"A1","template":"A"},{"id":"B1","template":"B"}],"connections":[{"from":{"component":"A1","connector":"P1","pin":1},"to":{"component":"B1","connector":"J1","pin":1}}]})

def test_valid_can_connection(): assert RuleEngine(project()).validate().valid
def test_type_mismatch(): assert not RuleEngine(project("CAN_L")).validate().valid
