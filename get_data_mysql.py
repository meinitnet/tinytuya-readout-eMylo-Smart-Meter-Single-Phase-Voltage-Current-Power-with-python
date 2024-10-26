import tinytuya
import time
import base64
import mysql.connector
from mysql.connector import Error

# Device setup
DEVICE_ID = "your_device_id"      # Replace with your device ID
DEVICE_IP = "your_device_ip"      # Replace with your device IP
LOCAL_KEY = "your_local_key"      # Replace with your local key
DEVICE_VERSION = "3.3"            # or "3.1" based on your device version

device = tinytuya.Device(DEVICE_ID, DEVICE_IP, LOCAL_KEY)
device.set_version(DEVICE_VERSION)
device.set_socketPersistent(True)
device.set_socketTimeout(15)

# Database connection function
def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="USER",
            password="PASSWORD",
            database="sensor_data"
        )
        if db.is_connected():
            print("Connected to database.")
            return db, db.cursor()
    except Error as e:
        print(f"Database connection error: {e}")
    return None, None

# Initial database connection
db, cursor = connect_db()
if db is None or cursor is None:
    print("Initial database connection failed. Retrying in the loop...")

# Initialize previous values for DPS
prev_dp1, prev_dp6, prev_dp15 = None, None, None

# Request all DPS
print(" > Send Request for All DPS Status < ")
payload = device.generate_payload(tinytuya.DP_QUERY)
device.send(payload)

print(" > Begin Monitor Loop <")
while True:
    try:
        # Timestamp for current loop iteration
        epoch_timestamp = int(time.time())

        # Reconnect to DB if connection is lost
        if not db or not db.is_connected():
            print("Reconnecting to the database...")
            db, cursor = connect_db()
            if not db or not cursor:
                print("Reconnection failed; retrying after delay.")
                time.sleep(5)
                continue

        # Receive data from the device
        data = device.receive()
        if data:
            # Extract DPS data
            dps_data = data.get("dps", {})
            dp1 = dps_data.get("1", prev_dp1)  # Use previous value if None
            dp6 = dps_data.get("6", prev_dp6)  # Use previous value if None
            dp15 = dps_data.get("15", prev_dp15)  # Use previous value if None

            # Update previous values for future use
            prev_dp1, prev_dp6, prev_dp15 = dp1, dp6, dp15

            # Decode dp6 if it exists
            if dp6 is not None:
                try:
                    field = dp6.encode('ascii')
                    z = base64.b64decode(field)
                    zbin = "".join(["{:08b}".format(x) for x in z])
                    a, b, c = zbin[:16], zbin[16:40], zbin[48:64]
                    voltage = int(a, 2) / 10.0
                    current = int(b, 2)
                    power = int(c, 2)

                    # Print decoded values
                    print("Epoch Timestamp:", epoch_timestamp)
                    print("V = %0.1f V" % voltage)
                    print("I = %d mA" % current)
                    print("P = %d W" % power)

                    # Insert data into the database
                    insert_query = """
                    INSERT INTO measurements (timestamp, voltage, current, power, dp1, dp15)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (epoch_timestamp, voltage, current, power, dp1, dp15))
                    db.commit()

                except Exception as decode_exception:
                    print(f"Error during decoding: {decode_exception}")

        else:
            print("No data received - using previous values")
            print("Previous DPS 1:", prev_dp1)
            print("Previous DPS 6:", prev_dp6)
            print("Previous DPS 15:", prev_dp15)

        # Optional: Sleep to avoid spamming the device
        time.sleep(5)

        # Send a periodic heartbeat to keep the connection alive
        heartbeat_payload = device.generate_payload(tinytuya.HEART_BEAT)
        device.send(heartbeat_payload)

    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
        break
    except Error as db_error:
        print(f"Database error: {db_error}")
        if db:
            db.close()
        db, cursor = None, None
        time.sleep(5)  # Wait before retrying
    except Exception as e:
        print(f"Unexpected error: {e}")
        time.sleep(5)

# Close resources on exit
if cursor:
    cursor.close()
if db:
    db.close()
