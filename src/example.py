import pandas as pd
import rui3pylib # type: ignore
import serial
import sys
import yaml
from time import sleep


def main():
    node_number = 2
    print("Insert device...")
    try:
        config = yaml.safe_load(open("lorawan.yaml"))
        if config is not None:
            app_config = config["app-config"]
            device_config = config["device-config"]
        else:
            print("Error opening lorawan.yaml file")
        node_list = pd.read_excel("config.xlsx")  # type: ignore
        if node_list["deveui"][node_number] is None:
            raise KeyError

    except KeyboardInterrupt:
        print("\nExiting...")
        sleep(1)
        sys.exit()
    except KeyError:
        print(f"node n.{node_number + 1} not found")
        print("\nExiting...")
        sleep(1)
        sys.exit()

    while True:
        try:
            sleep(5)
            node = rui3pylib.RUI3Node()  # type: ignore

            if node.ping() is not None:  # pyright: ignore[reportUnknownMemberType]
                rui3pylib.check_success(node, f"AT+PORT={device_config['port']}")  # type: ignore
                rui3pylib.check_success(node, f"AT+SENDINT={device_config['sendint']}")  # type: ignore
                node.set_device_eui(node_list["deveui"][node_number])  # type: ignore
                node.set_app_eui(app_config["app-eui"])  # type: ignore
                node.set_app_key(app_config["app-key"])  # type: ignore
                node.set_network_join_mode(device_config["join-mode"])  # type: ignore
                node.set_adaptive_rate(device_config["adr-enabled"])  # type: ignore
                node.set_transmit_power(device_config["transmit-power"])  # type: ignore
                node.set_data_rate(device_config["data-rate"])  # type: ignore
                node.set_lorawan_class(device_config["lora-class"])  # type: ignore
                node.set_confirm_mode(device_config["confirm-mode"])  # type: ignore
                node.set_freq_band(device_config["lora-region-band"])  # type: ignore

                while True:
                    print("Please disconnect your device before continuing")
                    prompt = input("Do you want to continue? (Y/N)")
                    match prompt.upper():
                        case "Y":
                            node_number += 1
                            print("Insert device...")
                            break
                        case "N":
                            print("Exiting...")
                            sleep(1)
                            sys.exit()
                        case _:
                            print("Invalid input")
                            continue
                    break

        except KeyboardInterrupt:
            print("\nExiting...")
            sleep(1)
            sys.exit()
        except serial.serialutil.PortNotOpenError:  # type: ignore
            print("Device not found")
            continue
        except KeyError:
            print(f"node n.{node_number + 1} not found")
            print("\nExiting...")
            sleep(1)
            sys.exit()


if __name__ == "__main__":
    main()
