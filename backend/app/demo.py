from .models import ComponentTemplateInput

def pins(count:int,overrides:dict[int,tuple[str,str,str]]):
    return [{"number":n,"name":overrides.get(n,(f"RESERVED_{n}","GPIO","BIDIRECTIONAL"))[0],"type":overrides.get(n,("","GPIO","BIDIRECTIONAL"))[1],"direction":overrides.get(n,("","GPIO","BIDIRECTIONAL"))[2],"allow_multiple":False} for n in range(1,count+1)]

DEMO_TEMPLATES=[
 ComponentTemplateInput.model_validate({"id":"PACK_CONN","name":"PACK","description":"Demo 33-pin pack connector","connectors":[{"id":"J1","name":"PACK J1","pin_count":33,"pins":pins(33,{1:("CAN_H","CAN_H","BIDIRECTIONAL"),2:("CAN_L","CAN_L","BIDIRECTIONAL"),3:("KL30_12V","POWER_12V_OUT","OUT"),4:("PACK_NTC","NTC_SENSOR","OUT")})}]}),
 ComponentTemplateInput.model_validate({"id":"BASU_A","name":"BASU","description":"Demo 32-pin battery safety unit","connectors":[{"id":"P1","name":"BASU P1","pin_count":32,"pins":pins(32,{1:("CAN_H","CAN_H","BIDIRECTIONAL"),2:("CAN_L","CAN_L","BIDIRECTIONAL"),3:("NTC_1","NTC_INPUT","IN"),4:("VBAT_12V","POWER_12V_IN","IN"),5:("VBAT_5V","POWER_5V_IN","IN")})}]}),
 ComponentTemplateInput.model_validate({"id":"BIC_A","name":"BIC","description":"Demo daisy-chain controller","connectors":[{"id":"P1","name":"Chain input","pin_count":2,"pins":[{"number":1,"name":"ISO_IN+","type":"DAISY_IN","direction":"IN"},{"number":2,"name":"ISO_IN-","type":"DAISY_IN","direction":"IN"}]},{"id":"P2","name":"Chain output","pin_count":2,"pins":[{"number":1,"name":"ISO_OUT+","type":"DAISY_OUT","direction":"OUT"},{"number":2,"name":"ISO_OUT-","type":"DAISY_OUT","direction":"OUT"}]}]}),
 ComponentTemplateInput.model_validate({"id":"NTC_10K","name":"NTC","description":"Demo temperature sensor","connectors":[{"id":"S1","name":"Sensor","pin_count":2,"pins":[{"number":1,"name":"NTC_OUT","type":"NTC_SENSOR","direction":"OUT"},{"number":2,"name":"GND","type":"GND","direction":"OUT","allow_multiple":True}]}]}),
 ComponentTemplateInput.model_validate({"id":"MCU_A","name":"MCU","description":"Demo controller","connectors":[{"id":"J1","name":"MCU IO","pin_count":4,"pins":[{"number":1,"name":"ADC_NTC","type":"ADC_NTC","direction":"IN"},{"number":2,"name":"GPIO_1","type":"GPIO","direction":"BIDIRECTIONAL"},{"number":3,"name":"CAN_H","type":"CAN_H","direction":"BIDIRECTIONAL"},{"number":4,"name":"CAN_L","type":"CAN_L","direction":"BIDIRECTIONAL"}]}]})
]
