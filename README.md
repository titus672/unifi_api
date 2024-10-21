### how it works

search snipe for unifi mac, if it isn't present, create a composite device with
the exists_in_snipe to false, if the mac is present, see if the site, name or
status needs to be updated.

To create the device, need to create a device with snipe by posting to the hard-
ware endpoint

This repo also contains some WIP tools to locate devices and ssid's across
multiple controllers currently `tools.py` contains a function for printing out
each site with it's ssid's. `toolbox.py` will contain the function to search for
mac addresses

If the script is erroring out with a `ERROR matching model_id, crashing` it means
there is a model in unifi that doesn't have a snipe_model_id associated with it.
The fix is to find/create the missing model in snipe and insert the unifi name
and set `self.model_id` to the corresponding snipe_model_id in `tools.py` in the
`Unifi_Device` class definition.
