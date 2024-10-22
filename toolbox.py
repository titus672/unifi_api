#!/usr/bin/env python3
from tools import update_local_cache, pprint
import argparse
# this file is intended to be a general purpose CLI tool to search unifi controllers
# for device macs or ssid's

def main():
    parser = argparse.ArgumentParser(description="Search unifi controllers for a device/site based on mac address or SSID")
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument("-fm", "--find-mac", help="find device by MAC Address")
    exclusive_group.add_argument("-fs", "--find-ssid", help="find site by SSID")
    args = parser.parse_args()
    
    sites: list = update_local_cache()

    if args.find_mac:
        print(f"Searching unifi devices for {args.find_mac}\n")
        for site in sites:
            for device in site["devices"]:
                if args.find_mac.upper() in device["mac"]:
                    print(device["mac"], "at", site["site_name"])
    elif args.find_ssid:
        print(f"searching unifi sites for {args.find_ssid}\n")
        for site in sites:
            for wlan in site["wlans"]:
                if args.find_ssid.upper() in wlan["name"].upper():
                    print(f"found SSID '{args.find_ssid}' at {site['site_name']} on {site['controller']}")


    


if __name__ == "__main__":
    main()
