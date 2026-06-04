import rui3pylib

iface = rui3pylib.RUI3Node()
try:

    iface.set_device_eui("AC1F09FFFE285584")
    iface.get_device_alias()
    iface.get_device_eui()

    iface.close()

except rui3pylib.serial.serialutil.PortNotOpenError as e:
    print(f"SerialException on {iface.port}: {e}")
    if iface.is_open:
        iface.close()
