#!/usr/bin/env python3
from tools import update_local_cache, find_mac, find_ssid
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
    parser.add_argument(
        "-u", "--update", help="update local cache", action="store_true")
    args = parser.parse_args()

    sites: list = update_local_cache(args.update)

    if args.find_mac:
        find_mac(args.find_mac, sites)
    elif args.find_ssid:
        find_ssid(args.find_ssid, sites)


if __name__ == "__main__":
    main()
