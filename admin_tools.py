#!/usr/bin/env python3

#this program was authored by Titus Friesen (titusfreezn@gmail.com) on 10-24-24
#to remove a user from all sites. This was created because a bug in the Unifi
#controller software gave a user permision to all sites.
#Credit for reverse engineering the Unifi API goes to Art-of-Wifi (https://github.com/Art-of-Wifi)

from tools import Unifi_Controller, Unifi_Site, CONFIG, pprint
import argparse

class Admin_Manager:
    def __init__(self, controller: Unifi_Controller):
        self.controller = controller
        self.controller.get_all_sites()

    #takes a site_id string. This can be obtained by navigating to the site in
    # a browesr (unifi.com:8443/manage/default/dashboard). In the previous
    # example, "default" is the site id, other site ids are a more random hash
    def list_site_admins(self, site_id:str):
        admins = self.controller.post(f"{site_id}/cmd/sitemgr", {"cmd": "get-admins"})["data"]
        pprint(admins)

    # takes a user_id string and revokes admin privilege for that user across
    # all the sites on the given controller if the site_id field is not populated
    def delete_site_admin(self, user_id: str, site_id=None):
        self.controller.get_all_sites()
        if site_id:
            print(site_id)
            admins = self.controller.post(f"{site_id}/cmd/sitemgr", {"cmd": "get-admins"})["data"]
            for admin in admins:
                if admin["_id"] == user_id:
                    pprint(self.controller.post(f"{site_id}/cmd/sitemgr", {"cmd": "revoke-admin", "admin": user_id}))
                else:
                    print("skipped admin ", admin["email"])

        else:
            self.controller.get_all_sites()
            for site in self.controller.sites:
                print(site.site_name)
                admins = self.controller.post(f"{site.site_id}/cmd/sitemgr", {"cmd": "get-admins"})["data"]
                for admin in admins:
                    if admin["_id"] == user_id:
                        pprint(self.controller.post(f"{site.site_id}/cmd/sitemgr", {"cmd": "revoke-admin", "admin": user_id}))
                    else:
                        print("skipped admin ", admin["email"])
    
 
def main():
    c = CONFIG()
    
    parser = argparse.ArgumentParser(description="Manage admins on a Unifi Controller")
    exclusive_group = parser.add_mutually_exclusive_group()
    exclusive_group.add_argument("-l", "--list-admins", action="store_true", help="get admins from a given site")
    exclusive_group.add_argument("-D", "--delete-admin", action="store_true", help="delete a given admin from a given site(I don't think it works if they are a superadmin)")
    parser.add_argument("-s", "--site", required=True, help="site id parameter")
    parser.add_argument("-u", "--user", help="admin _id parameter")
    args = parser.parse_args()

    controller = Unifi_Controller(c.UNIFI_URLS[1], c.UNIFI_USERNAME, c.UNIFI_PASSWORD)
    manager = Admin_Manager(controller)

    if args.list_admins:
        manager.list_site_admins(args.site)
    elif args.delete_admin:
        if args.site:
            manager.delete_site_admin(args.user, args.site)
        else:
            manager.delete_site_admin(args.user)



if __name__ == "__main__":
    main()
