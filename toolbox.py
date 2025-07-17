#!/usr/bin/env python3
from tools import update_local_cache, find_mac, find_ssid, find_duplicates, test, list_asset_models, get_sso_devices
import argparse

# this file is intended to be a general purpose CLI tool to search unifi
# controllers for device macs or ssid's


def main():
    parser = argparse.ArgumentParser(
        description="Search unifi controllers for a device/site based on mac address or SSID")
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument(
        "-fm", "--find-mac", help="find device by MAC Address")
    exclusive_group.add_argument(
        "-fs", "--find-ssid", help="find site by SSID")
    exclusive_group.add_argument(
        "-fd", "--find-duplicates", help="find duplicates", action="store_true"
    )
    exclusive_group.add_argument("-t", "--test", help="run test function", action="store_true")
    exclusive_group.add_argument("-la", "--list-asset-models", help="run test function", action="store_true")
    exclusive_group.add_argument("-gs", "--get-sso-devices", help="run test function", action="store_true")
    parser.add_argument(
        "-u", "--update", help="update local cache", action="store_true")
    args = parser.parse_args()

    sites: list = update_local_cache(args.update)

    if args.find_mac:
        find_mac(args.find_mac, sites)
    elif args.find_ssid:
        find_ssid(args.find_ssid, sites)
    elif args.find_duplicates:
        find_duplicates(sites)
    elif args.test:
        test()
    elif args.list_asset_models:
        list_asset_models()
    elif args.get_sso_devices:
        devices = get_sso_devices()
        for device in devices:
            print(device)


if __name__ == "__main__":
    main()
