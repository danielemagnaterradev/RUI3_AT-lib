import rui3pylib

iface = rui3pylib.RUI3Node()

iface.set_device_eui("AC1F09FFFE285584")
iface.get_device_alias()
iface.get_device_eui()

iface.close()
