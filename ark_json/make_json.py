import json

port=1234

# with open("/home/sentry/sandbox/ark_json/slowtest_(Version_0.0.1)_Chariot/config.json","r") as fp:
#     config=json.load(fp)
#     labels={x:{"threshhold":0.8, "color":"red" for x in config["class_str_to_int"]}
labels={'Radiation': {"threshold":0.8, "color":"red", "disabled":False}, 'person': {"threshold":1.0, "color":"blue","disabled":False}}

sensor_config={"type":"config","port":8095,"lables":labels,"camera_address_mapping":{"front":"udp://239.15.105.1:6012","back":"udp://239.15.105.1:6013"}}
with open("config.json","w") as fp:
    json.dump(sensor_config,fp,indent=3)


message_json=[{"camera":"front","time":1715877652000,"detections":[{"label":"Radiation", "confidence":0.92, "bounding_box":[0.1,0.1,0.2,0.2]},{"label":"Radiation", "confidence":0.85, "bounding_box":[0.25,0.36,0.95,0.83]},{"label":"person", "confidence":0.92, "bounding_box":[0.1,0.1,0.2,0.2]}]},{"camera":"back","time":1715877652021,"detections":[{"label":"Radiation", "confidence":0.92, "bounding_box":[0.1,0.1,0.2,0.2]},{"label":"Radiation", "confidence":0.85, "bounding_box":[0.25,0.36,0.95,0.83]},{"label":"person", "confidence":0.92, "bounding_box":[0.1,0.1,0.2,0.2]}]}]
with open("detection.json","w") as fp:
    json.dump(message_json,fp,indent=3)