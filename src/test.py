import rui3pylib

iface = rui3pylib.RUI3node()

iface.attention()
iface.getSerialNumber()
iface.getDeviceAlias()
iface.getFirmVersion()
iface.getAPIVersion()

iface.tryClose()
