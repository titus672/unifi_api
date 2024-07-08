#!/usr/bin/env python
from tools import CONFIG, Snipe_Connection, pprint, Unifi_Controller, get_unifi_snipe
import json
from copy import deepcopy
def main():
    c = CONFIG()
    conn = Unifi_Controller("unifi.streamitnet.com", c.UNIFI_USERNAME, c.UNIFI_PASSWORD)
    device = conn.get(f"s/ga5eo1zo/stat/device")
    data = []
    #pprint(device["data"])
    for d in device["data"]:
        ...
        #print(d["model"])
    with open("test_device.json", "r") as f:
        data = json.load(f)
        for d in data:
            if d["model"] == "U20":
                print("Found d.model without strpp")
            elif d["model"].strip() == "U20":
                print("Found d.model with strpp")
            else:
                print("couldn't find model")

def test():
    c = CONFIG()
    conn = Snipe_Connection(c.SNIPE_KEY, c.SNIPE_URL)
    assets = get_unifi_snipe()
    assets2 = deepcopy(assets)
    dups = set()
    for asset in assets:
        for asset2 in assets2:
            if asset2.mac_address == asset.mac_address and asset2.id != asset.id:
                dups.add(asset)
    for dup in dups:
        print(dup.site, dup.name, dup.mac_address)
    print(len(dups), "dups")
if __name__ == "__main__":
    test()
