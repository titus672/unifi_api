from tools import CONFIG, pprint, Unifi_Controller
import json
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
    list1 = [1,2,3,4]
    list2 = [5,6,7,8,9,10]
    for l in list1:
        for li in list2:
            list2.remove(6)
            print(li)
if __name__ == "__main__":
    test()
