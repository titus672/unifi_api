#!/usr/bin/env python
import json
from tools import pprint, CONFIG, Unifi_Controller

def main():
    ...

def sort_via_set(data):
    ... 
def sort_files():
    with open("unifi-1.json", "r") as f:
        unifi_1_data = json.loads(f.read())

    with open("unifi-2.json", "r") as f:
        unifi_2_data = json.loads(f.read())
    
    import sys
    search_str = sys.argv[1]
    for unifi in unifi_1_data:
        if search_str in unifi["mac"].upper():
            print(unifi)
    for unifi in unifi_2_data:
        if search_str in unifi["mac"].upper():
            print(unifi)
    #same = []
    #print(type(unifi_1_data))
    #for device2 in unifi_2_data:
    #    for device1 in unifi_1_data:
    #        if device1["mac"] == device2["mac"]:
    #            same.append({"device1": device1, "device2": device2})

    #pprint(same)

if __name__ == "__main__":
    sort_files()
