import tinytuya
import time
import base64
#tinytuya.set_debug(True)

# Device setup
DEVICE_ID = "your_device_id"      # Replace with your device ID
DEVICE_IP = "your_device_ip"      # Replace with your device IP
LOCAL_KEY = "your_local_key"      # Replace with your local key
DEVICE_VERSION = "3.3"            # or "3.1" based on your device version

device = tinytuya.Device(DEVICE_ID, DEVICE_IP, LOCAL_KEY)
device.set_version(DEVICE_VERSION)
device.set_socketPersistent(True)
device.set_socketTimeout(5)  # Set timeout for receiving data

prev_dp1 = None
prev_dp6 = None
prev_dp15 = None

epoch_timestamp = int(time.time())
print(" > Send Request for All DPS Status < ")

payload = device.generate_payload(tinytuya.DP_QUERY)
device.send(payload)

print(" > Begin Monitor Loop <")
while True:
    try:
        # Receive all DPS data
        data = device.receive()
#        print("Received Payload:", data)
        if data:
            # Extract specific DPS values
            dps_data = data.get("dps", {})
            dp1 = dps_data.get("1")    # Retrieve DPS 1
            dp6 = dps_data.get("6")    # Retrieve DPS 6
            dp15 = dps_data.get("15")  # Retrieve DPS 15
            
            if dp1 is not None:
                prev_dp1 = dp1
            if dp6 is not None:
                prev_dp6 = dp6
            if dp15 is not None:
                prev_dp15 = dp15

            print("Epoch Timestamp: %d" % epoch_timestamp)
            print("Current DPS 1:", dp1 if dp1 is not None else prev_dp1)
            print("Current DPS 6:", dp6 if dp6 is not None else prev_dp6)
            print("Current DPS 15:", dp15 if dp15 is not None else prev_dp15)

            if dp6 is None:
              dp6 = prev_dp6
            else:
              prev_dp6 = dp6  

            if dp6 is not None:
                try:
                    text = dp6  # Assuming dp6 is a Base64 encoded string
                    field = text.encode('ascii')

                    z = base64.b64decode(field)

                    zbin = "".join(["{:08b}".format(x) for x in z])
                    a = zbin[:16]
                    b = zbin[16:40]
                    c = zbin[48:64]
                    voltage = int(a, 2) / 10.0       # Voltage
                    current = int(b, 2)              # Current in mA
                    power = int(c, 2)                 # Power in W

                    print("V = %0.1f V" % voltage)  # Only display voltage
                    print("I = %d mA" % current)     # Only display current
                    print("P = %d W" % power)        # Only display power


                except Exception as decode_exception:
                    print(f"Error during decoding: {decode_exception}")
            else:
                print(" ")

        else:
            print("No data received - using previous values...")
            # Print previous values if current data is None
            print("Previous DPS 1:", prev_dp1)
            print("Previous DPS 6:", prev_dp6)
            print("Previous DPS 15:", prev_dp15)

        # Optional: Sleep to avoid spamming the device
        time.sleep(5)

        heartbeat_payload = device.generate_payload(tinytuya.HEART_BEAT)  # Correctly generate heartbeat payload
        device.send(heartbeat_payload)

    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
        break
    except Exception as e:
        print(f"Error: {e}")
        break
