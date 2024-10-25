#!/usr/bin/env python
import requests,json, html, os, time
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def pprint(j):
    print(json.dumps(j, indent=4))

class Debug:
    def __init__(self):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", help="print debug messages", action="store_true")
        parser.add_argument("--create_new_assets", help="create new assets in snipe if needed", action="store_true")
        parser.add_argument("--report", help="report devices not in unifi", action="store_true")
        self.args = parser.parse_args()
    def debug(self, *message):
        if self.args.debug:
            print(str(message))
    def report(self, snipes):
        if self.args.report:
            print("""........Report.......
                  the following devices were not found in the configured unifi
                  controllers. Consider deleting or archiving these devices""")
            for snipe in snipes:
                print(snipe.id, snipe.mac_address, snipe.site, snipe.name)

class CONFIG:
    def __init__(self):
        with open("config.json", "r") as config:
            self.config = json.load(config)
        self.UNIFI_USERNAME = self.config["UNIFI_USERNAME"]
        self.UNIFI_PASSWORD = self.config["UNIFI_PASSWORD"]
        self.UNIFI_URLS = self.config["UNIFI_URLS"]
        self.SNIPE_KEY = self.config["SNIPE_CON_KEY"]
        self.SNIPE_URL = self.config["SNIPE_CON_URL"]

    def __str__(self):
        return (f"{self.UNIFI_USERNAME}\n{self.UNIFI_PASSWORD}\n{self.UNIFI_URLS}")

class Snipe_Connection:
    def __init__(self, key: str, url: str):
        self.KEY = key
        self.URL = f"https://{url}/api/v1/"

    def get(self, endpoint, querystring=""):

        url = self.URL + endpoint

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.KEY
        }
        request = requests.get(url, headers=headers, params=querystring)
        request_data = json.loads(request.text)
        return request_data

    def put(self, endpoint, payload={}):

        url = self.URL + endpoint

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.KEY
        }

        ### This needs to be redone to match the post method, returning a wrapped object
        response = requests.request("PUT", url, json=payload, headers=headers)
        return {"response": response, "data": json.loads(response.text)}

    def post(self, endpoint, payload={}):

        url = self.URL + endpoint

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.KEY
        }

        response = requests.request("POST", url, json=payload, headers=headers)
        return {"response": response, "data": json.loads(response.text)}

    def patch(self, endpoint, payload={}):
        url = self.URL + endpoint
        
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.KEY
        }
        response = requests.request("PATCH", url, json=payload, headers=headers)
        return {"response": response, "data": json.loads(response.text)}

class Composite_Device:
    def __init__(self, data):
        ###
        # Data structure...
        # {
        #     "status": "Stock",
        #     "snipe_id": "1234",
        #     "name": "test_device",
        #     "model": "unifi_model"
        # }
        self.needs_update = False
        self.mac = data.get("mac", None)
        self.snipe_id = data.get("snipe_id", None)
        self.name = data["name"]
        ###
        # match for status label
        # 3 = Archived
        # 4 = Shipping
        # 5 = Stock
        # 6 = Deployed
        # sets the appropriate self.status_id based on the site
        ###
        self.site = data.get("site", None)
        match data.get("site", None):
            case None:
                # no site, must still be shipping
                self.status_id = 4
            case "1a-Default":
                # exception for default site, if here, it must be stock
                self.status_id = 5
            case _:
                # if it's at any other site, it's deployed
                self.status_id = 6

        self.model_id = data["model_id"]

class Snipe_Asset:
    def __init__(self, data):
        
        # Does this asset need to be updated in Snipe? default to false and
        # update the value later
        self.used = False

        self.id = data["id"]
        self.name = html.unescape(data["name"])
        self.model = data["model"]["id"]
        # 3 : archived
        # 6 : deployed
        # 4 : shipping
        # 5 : stock

        self.status_label = data["status_label"]["id"]
        
        self.mac_address = data.get("custom_fields", {}).get("MAC Address", {}).get("value", None)

        self.site = (data.get("custom_fields", {}).get("Site", {}).get("value", None))

class Unifi_Controller:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.full_url = f"https://{url}:8443/api/"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        data = {"username": username, "password": password}
        self.session = requests.Session()
        self.session.post(self.full_url + "login", headers=headers, json=data, verify=False)
        self.sites = []

    def __del__(self):
        self.session.post(self.full_url + "logout")
        print("logged out session " + self.url)

    def get(self, endpoint):
        data = self.session.get(self.full_url + endpoint)
        return data.json()

    def post(self, endpoint: str, payload: dict):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        return self.session.post(self.full_url + "s/" + endpoint, headers=headers,json=payload, verify=False ).json()
        
    
    def get_all_sites(self):
        self.sites: list[Unifi_Site] = []
        data = self.get("self/sites")
        for site in data["data"]:
            self.sites.append(Unifi_Site({
                                          "site_id": site["name"], 
                                          "site_name": site["desc"], 
                                          "controller": self.url
                                          }))

    def get_devices_from_site(self, site):
        # make sure devices haven't been retrieved already
        if site.devices == []:
            data = self.get(f"s/{site.site_id}/stat/device")["data"]
            for device in data:
                # some devices don't have names, this just replaces the name
                # with the model if it's empty
                if "name" in  device:
                    site.devices.append(Unifi_Device({
                                                      "name": device["name"],
                                                      "mac": device["mac"], 
                                                      "model": device["model"],
                                                      "site_name": site.site_name, 
                                                      "controller": self.url
                                                      }))
                elif "name" not in device:
                    site.devices.append(Unifi_Device({
                                                      "name": device["model"], 
                                                      "mac": device["mac"], 
                                                      "model": device["model"],
                                                      "site_name": site.site_name, 
                                                      "controller": self.url
                                                      }))
                else:
                    print("!!!ERROR processing devices in get_device_from_site")
                    exit(1)
        elif site.devices != []:
            print("!!!ERROR in get_devices_from_site: list was not empty")

    # function to get wlan from a specific site, probably prefered to use the `collect_all_wlans`
    # function to collect them all instead
    def get_wlans_from_site(self, site):
        if site.wlans == []:
            wlans = self.get(f"s/{site.site_id}/rest/wlanconf")["data"]
            for wlan in wlans:
                site.wlans.append(wlan)
        elif site.wlans != []:
            print("Skipping wlans for site {}", site.site_name)

    # function to collect all devices
    def collect_all_devices(self):
        # make sure the self.sites variable is populated
        if self.sites == []:
            self.get_all_sites()
            print("collecting sites for devices")

        for site in self.sites:
            self.get_devices_from_site(site) 
        
    def collect_all_wlans(self):
        # collect all wlans from all sites
        #check for self.sites and populate if empty
        if self.sites == []:
            self.get_all_sites()
            print("collecting sites for wlan")

        for site in self.sites:
            self.get_wlans_from_site(site)

class Unifi_Site:
    def __init__(self, data):
        self.controller = data["controller"]
        self.site_id = data["site_id"]
        self.site_name = data["site_name"]
        self.devices = []
        self.wlans = []
    
    def __str__(self):
        return f"site_id = {self.site_id}\nsite_name = {self.site_name}\ncontroller={self.controller}\n"

class Unifi_Device:
    def __init__(self, data):
        self.name = data["name"]
        self.mac = data["mac"].upper()
        self.site_name = data["site_name"]
        self.controller = data["controller"]
        self.model = data["model"]
        match self.model:
            case "U7MSH":
                self.model_id = 93
            case "U2O":
                self.model_id = 105
            case "U7LT":
                self.model_id = 75
            case "U2HSR":
                self.model_id = 106
            case "BZ2":
                self.model_id = 107
            case "BZ2LR":
                self.model_id = 108
            case "U7P":
                self.model_id = 109
            case "UDMB":
                self.model_id = 92
            case "US16P150":
                self.model_id = 110
            case "U7LR":
                self.model_id = 111
            case "USF5P":
                self.model_id = 99
            case "U7PG2":
                self.model_id = 113
            case "US8P150":
                self.model_id = 114
            case "US8P60":
                self.model_id = 115
            case "U7NHD":
                self.model_id =  95
            case "U7IW":
                self.model_id = 116
            case "UAPL6":
                self.model_id = 96
            case "U6M":
                self.model_id = 78
            case "USMINI":
                self.model_id = 117
            case "UALR6v2":
                self.model_id = 98
            case "UAP6MP":
                self.model_id = 97
            case "UAL6":
                self.model_id = 79
            case "USL24":
                self.model_id = 118
            case "U6EXT":
                self.model_id = 94
            case "USAGGPRO":
                self.model_id = 119
            case "USL8LP":
                self.model_id = 120
            case "U6IW":
                self.model_id = 101
            case _:
                print("ERROR matching model_id, crashing")
                pprint(data)
                #import pdb
                #pdb.set_trace()
                exit(1)
    def __str__(self):
        return f"name={self.name}\nmac={self.mac}\nsite_name={self.site_name}\ncontroller={self.controller}\nmodel={self.model}\n"

# get all unifi devices from both controllers
def get_unifi_unifi():
    config = CONFIG()
    controllers = []
    for url in config.UNIFI_URLS:
        controllers.append(Unifi_Controller(url, config.UNIFI_USERNAME, config.UNIFI_PASSWORD))

    unifi_unifis: list[Unifi_Device] = []
    for controller in controllers:
        controller.collect_all_devices()
        for site in controller.sites:
            for device in site.devices:
                unifi_unifis.append(device)
    return unifi_unifis

# get all unifi assets from snipe, returns a list of [Snipe_Asset]
def get_unifi_snipe():
    config = CONFIG()
    snipe = Snipe_Connection(config.SNIPE_KEY, config.SNIPE_URL)
    offset = 0
    hardware = snipe.get("hardware", f"category_id=3&limit=1&offset={offset}")
    total: int = hardware["total"]
    count = 0
    assets: list[Snipe_Asset] = []
    while offset <= total:
        data = snipe.get("hardware", f"category_id=3&limit=100&offset={offset}")
        offset += 100
        for d in data["rows"]:
            assets.append(Snipe_Asset(d))
            count += 1
    return assets

# this function creates a local cache of sites, their devices and wlans.
# It also checks to make sure the cache isn't too far out of date, currently
# that's set at 30min.
def update_local_cache():
    c = CONFIG()
    controllers: list[Unifi_Controller] = []
    for url in c.UNIFI_URLS:
        controllers.append(Unifi_Controller(url, c.UNIFI_USERNAME, c.UNIFI_PASSWORD))

    # try updating cache if the file already exists
    if os.path.exists("unifi_cache.json"):
        try:
            with open("unifi_cache.json", 'r+') as cache_handle:
                #{
                #    "time": unix_time when written,
                #    "sites": [{
                #       "controller": controller,
                #       "site_name": site_name,
                #       "devices": [{
                #            "device_name": device_name,
                #            "mac": mac,
                #            "model": model
                #           }],
                #       "wlans": [{
                #           "name": wlan_name,
                #           "x_passphrase": wifi_password, 
                #                   }]
                #}]
                #}
                now = time.time()
                cache = json.load(cache_handle)
                # update cache if it's over 5m old
                if (now - cache["time_written"]) < 1800:
                    print("time is less than 1800")
                    return cache["sites"]
                elif (now - cache["time_written"]) >= 1800:
                    print("time is greater than 1800, updating cache")
                    sites = []
                    sites_json = []
                    for controller in controllers:
                        controller.get_all_sites()
                        controller.collect_all_devices()
                        controller.collect_all_wlans()
                        #sites.extend(controller.sites)
                        for site in controller.sites:
                            devices = []
                            for device in site.devices:
                                devices.append({
                                    "device_name": device.name,
                                    "mac": device.mac,
                                    "model": device.model
                                })
                            sites_json.append({
                                "controller": site.controller,
                                "site_name": site.site_name,
                                "devices": devices,
                                "wlans": site.wlans
                            })

                    new_cache = {
                        "time_written": now,
                        "sites": sites_json,
                    }
                    cache_handle.seek(0)
                    json.dump(new_cache, cache_handle, indent=2)
                    cache_handle.truncate()
                    return sites
                    
        except Exception as e:
            print("exception in update_local_cache")
            print(e)
            exit(1)

    # create and populate the cache
    elif not os.path.exists("unifi_cache.json"):
        try:
            with open("unifi_cache.json", 'w') as cache_handle:
                now = time.time()
                sites = []
                sites_json = []
                for controller in controllers:
                    controller.get_all_sites()
                    controller.collect_all_devices()
                    controller.collect_all_wlans()
                    for site in controller.sites:
                        devices = []
                        for device in site.devices:
                            devices.append({
                                "device_name": device.name,
                                "mac": device.mac,
                                "model": device.model
                            })
                        sites_json.append({
                            "controller": site.controller,
                            "site_name": site.site_name,
                            "devices": devices,
                            "wlans": site.wlans
                        })

                new_cache = {
                    "time_written": now,
                    "sites": sites_json,
                }
                json.dump(new_cache, cache_handle, indent=2)
                return sites
                
        except Exception as e:
            print("Error while creating 'unifi_cache.json'")
            print(e)
            exit(1)
    else:
        print("unknown error occured in update_local_cache,\n couldn't find or create cache file")
        exit(1)

def test():
    sites = update_local_cache()
    wlans = []
#    for site in sites:
#        pprint(site)
#    for wlan in wlans:
#        #pprint(wlan)
#        print(wlan)

if __name__ == "__main__":
    test()
