#!/usr/bin/env python

from tools import Snipe_Connection, pprint, get_unifi_snipe, get_unifi_unifi, Snipe_Asset, Unifi_Device, Composite_Device, CONFIG, Debug

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
debug = Debug()
def search_snipes_for_mac():
    unifis = get_unifi_unifi()
    snipes = get_unifi_snipe()
    comps: list[Composite_Device] = []
    remove_snipes = set()
    remove_unifis = set()
    empty_snipes: set[Snipe_Asset] = set()
    unassigned_unifs: set[Unifi_Device] = set()
    debug.debug("unifis:", len(unifis))
    debug.debug("snipes:", len(snipes))
    match1 = 0
    match2 = 0
    match3 = 0
    match4 = 0
    match5 = 0
    for unifi_index, unifi in enumerate(unifis):
        for snipe_index, snipe in enumerate(snipes):
            if snipe.used == False:
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
                                "mac": unifi.mac,
                            })
                            match1 += 1
                            comp.needs_update = True
                            snipe.used = True
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
                                "mac": unifi.mac,
                            })
                            match2 += 1
                            comp.needs_update = False
                            snipe.used = True
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
                    #    debug.debug("Err stopping")
                    #    exit(1)
                elif snipe.mac_address is None and snipe.model == unifi.model_id:
                    # logic to use empty_assets
                    comp = Composite_Device({
                        "name": unifi.name,
                        "snipe_id": snipe.id,
                        "model_id": unifi.model_id,
                        "site": unifi.site_name,
                        "mac": unifi.mac,
                    })
                    match3 += 1
                    comp.needs_update = True
                    snipe.used = True
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
                    debug.debug("ERR parsing snipes, Crashing")
                    debug.debug(f"{snipe.id} {unifi.model}")
                    exit(1)
            # the unifi doesn't have a snipe asset, need to create it
            #for snipe in snipes:
            #    debug.debug(snipe.name, snipe.id, snipe.model)
    debug.debug("remove_snipes", len(remove_snipes))
    debug.debug("remove_unifis", len(remove_unifis))

    remove_snipes = sorted(remove_snipes, reverse=True)
    remove_unifis = sorted(remove_unifis, reverse=True)
    for snipe in remove_snipes:
        del snipes[snipe]
    for unifi in remove_unifis:
        del unifis[unifi]

    if debug.args.create_new_assets:
        debug.debug(f"Creating {len(unifis)} assets")
        for unifi in unifis:
            snipe = create_asset(unifi.model_id)
            debug.debug("created asset", snipe.id)
            comp = Composite_Device({
                "name": unifi.name,
                "snipe_id": snipe.id,
                "model_id": unifi.model_id,
                "site": unifi.site_name,
                "mac": unifi.mac
            })
            comp.needs_update = True
            comps.append(comp)
    else:
        debug.debug(f"create_new_assets flag not set, skipping creation for {len(unifis)} devices")
    debug.report(snipes)

    debug.debug("site != site", match1)
    debug.debug("site = site", match2)
    debug.debug("no mac, model = model", match3)
    debug.debug("no mac, model != model", match4)
    debug.debug("snipe.mac != unifi.mac", match5)
    debug.debug("snipes",len(snipes))
    debug.debug("unifis", len(unifis))
    debug.debug("unassigned_unifs", len(unassigned_unifs))
    debug.debug("empty_snipes", len(empty_snipes))
    debug.debug("comps", len(comps))
    return comps

# creates an asset(snipe) with the appropriate model and status
def create_asset(model_id: int = 107, status_id: int = 4):
    debug.debug("creating new asset")
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
        debug.debug("crashing in 'create_asset'")
        debug.debug(p)
        exit(1)

def main():
    c = CONFIG()
    snipe_conn = Snipe_Connection(c.SNIPE_KEY, c.SNIPE_URL)
    comps = search_snipes_for_mac()
    update = 0
    for comp in comps:
        if comp.needs_update:
            update += 1
            data = {
                "name": comp.name,
                "status_id": comp.status_id,
                "_snipeit_mac_address_1": comp.mac,
                "_snipeit_site_2": comp.site,
            }
            debug.debug(comp.name, comp.mac, comp.site)
            if comp.mac is None:
                exit(1)
            snipe_conn.patch(f"hardware/{comp.snipe_id}", data)
    debug.debug(f"updated {update} devices")

if __name__ == "__main__": 
    main()
