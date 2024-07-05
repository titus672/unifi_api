#!/usr/bin/env python

from re import search
from tools import Snipe_Connection, pprint, get_unifi_snipe, get_unifi_unifi, Snipe_Asset, Unifi_Device, Composite_Device, CONFIG

###
# this fn might get moved yet, not sure, but it takes a list of Snipe Assets
# and a single Unifi_Device and looks through the snipes for the proper mac.
# if found, it creates a Composite_Device with the appropriate info and sets
# some flags in the Unifi_Device and the Composite_Device. More specificaly it
# sets the "in_snipe" flag to true for the Unifi_Device object and sets the
# "exists_in_snipe" and "needs_update" flags. I don't think I need to have the
# "exists_in_snipe" flag at all in the Composite_Device object, but I'm leaving
# it there for the moment.
###
def search_snipes_for_mac():
    unifis = get_unifi_unifi()
    snipes = get_unifi_snipe()
    comps: list[Composite_Device] = []
    remove_snipes = set()
    remove_unifis = set()
    empty_snipes: set[Snipe_Asset] = set()
    unassigned_unifs: set[Unifi_Device] = set()
    print("unifis:",len(unifis))
    print("snipes:", len(snipes))
    match1 = 0
    match2 = 0
    match3 = 0
    match4 = 0
    match5 = 0
    for unifi_index, unifi in enumerate(unifis):
        for snipe_index, snipe in enumerate(snipes):
            if snipe.mac_address is not None:
                if snipe.mac_address == unifi.mac:
                    # deal with matching macs
                    # creates a comp device with the correct
                    # metadata. It also removes the snipe and
                    # unifi objects from their respective lists
                    if snipe.site != unifi.site_name or snipe.name != unifi.name:
                        comp = Composite_Device({
                            "name": unifi.name,
                            "snipe_id": snipe.id,
                            "model_id": unifi.model_id,
                            "site": unifi.site_name,
                        })
                        match1 += 1
                        unifi.in_snipe = True
                        comp.exists_in_snipe = True
                        comp.needs_update = True
                        remove_snipes.add(snipe_index)
                        remove_unifis.add(unifi_index)
                        comps.append(comp)
                        break
                    elif snipe.site == unifi.site_name and snipe.name == unifi.name:
                        comp = Composite_Device({
                            "name": unifi.name,
                            "snipe_id": snipe.id,
                            "model_id": unifi.model_id,
                            "site": unifi.site_name,
                        })
                        match2 += 1
                        unifi.in_snipe = True
                        comp.exists_in_snipe = True
                        comp.needs_update = False
                        remove_snipes.add(snipe_index)
                        remove_unifis.add(unifi_index)
                        comps.append(comp)
                        break
                #elif snipe.mac_address != unifi.mac:
                    # I think I can remove this one if I move all the logic to
                    # this set of loops
                #    ...
                    #match5 += 1
                    #empty_snipes.add(snipe)
                    #unassigned_unifs.add(unifi)
                #else:
                #    print("Err stopping")
                #    exit(1)
            elif snipe.mac_address is None and snipe.model == unifi.model_id:
                # logic to use empty_assets
                comp = Composite_Device({
                    "name": unifi.name,
                    "snipe_id": snipe.id,
                    "model_id": unifi.model_id,
                    "site": unifi.site_name,
                })
                match3 += 1
                comp.set_mac(unifi.mac)
                unifi.in_snipe = True
                comp.needs_update = True
                remove_snipes.add(snipe_index)
                remove_unifis.add(unifi_index)
                comps.append(comp)
            elif snipe.mac_address is None and snipe.model != unifi.model_id:
                ## I think this is obsolete as well
                # move device to different list
                # this will move most of the unifis to the empty_snipes list
                match4 += 1
                empty_snipes.add(snipe)
                unassigned_unifs.add(unifi)
            else:
                print("ERR parsing snipes, Crashing")
                print(f"{snipe.id} {unifi.model}")
                exit(1)
        # the unifi doesn't have a snipe asset, need to create it
        #for snipe in snipes:
        #    print(snipe.name, snipe.id, snipe.model)
    print("remove_snipes", len(remove_snipes))
    print("remove_unifis", len(remove_unifis))

    remove_snipes = sorted(remove_snipes, reverse=True)
    remove_unifis = sorted(remove_unifis, reverse=True)
    for snipe in remove_snipes:
        del snipes[snipe]
    for unifi in remove_unifis:
        del unifis[unifi]
    print("site != site", match1)
    print("site = site", match2)
    print("no mac, model = model", match3)
    print("no mac, model != model", match4)
    print("snipe.mac != unifi.mac", match5)
    print("snipes",len(snipes))
    print("unifis", len(unifis))
    return comps

def get_empty_assets(snipes: list[Snipe_Asset]):
    emp_assets: list[Snipe_Asset] = []
    for snipe in snipes:
        if snipe.mac_address is None:
            emp_assets.append(snipe)
    return emp_assets

def create_asset(model_id: int = 107, status_id: int = 4):
    print("creating new asset")
    c = CONFIG()
    conn = Snipe_Connection(c.SNIPE_KEY, c.SNIPE_URL)
    asset = {
        "status_id": status_id,
        "model_id": model_id,
        "name": "new_device"
    }
    p = conn.post("hardware", asset)["data"]
    if p["status"] == "success":
        snipe = Snipe_Asset({
            "id": p["payload"]["id"],
            "name": p["payload"]["name"],
            "model": { "id": p["payload"]["id"] },
            "status_label": { "id": p["payload"]["status_id"] },
        })
        return snipe
    else:
        print("crashing in 'create_asset'")
        print(p)
        exit(1)
###
# takes a Unifi_Device and either finds an asset of the same model without a mac
# or makes a new one of the appropriate type
###
def create_if_empty(snipes:list[Snipe_Asset], unifi: Unifi_Device):
    empty_assets = get_empty_assets(snipes)
    print()
    comps: list[Composite_Device] = []
    while empty_assets:
        for asset in empty_assets:
            comp = Composite_Device({
                "name": unifi.name,
                "snipe_id": asset.id,
                "model": unifi.model_id,
                "site": unifi.site_name,
            })
            unifi.in_snipe = True # set in_snipe to true so we know it's been dealt with
            comp.exists_in_snipe = True # set true to indicate the asset exists
            comp.needs_update = True # the asset was empty, so it needs an update
            comp.update_mac = True
            comp.set_mac(unifi.mac)
            empty_assets.remove(asset)
    print("no more empty assets")
    print(len(empty_assets))
    print(len(comps))

def get_unique_models():
    unifis = get_unifi_unifi()
    models = []
    devices = []
    for unifi in unifis:
        if unifi.model not in models:
            models.append(unifi.model)
            devices.append(unifi)
    for d in devices:
        print(d)

def test():
    unifis = get_unifi_unifi()
    snipes = get_unifi_snipe()
    for unifi in unifis:
        create_if_empty(snipes, unifi)
        break
def testing():
    search_snipes_for_mac()

if __name__ == "__main__": 
    testing()
