## READ THIS
# RPI UART
#    https://www.abelectronics.co.uk/kb/article/1035/raspberry-pi-3--4-and-zero-w-serial-port-usage
# loc = /dev/ttyS0
# baud = 2000000

import serial
import time
import platform

# Frequency, in hertz
xfreq = 1
yfreq = 60
sf = 20e3
byts = (1/xfreq) * sf

# Calculate resulting image resolution
ypoints = (1/(yfreq*2)) / (1/sf)
xpoints = byts / ypoints

bytes_to_read = 100

print(f"Resolution: {xpoints} x {ypoints}")
s_com = serial.Serial('/dev/ttyACM0', 115200)

if "arm" in platform.uname().machine:
    # For raspberry pi
    s_dat = serial.Serial('/dev/ttyS0', 2e6, timeout=1.0)
else:
    s_dat = serial.Serial('/dev/ttyUSB0', 2e6, timeout=1.0)

print("Expecting %f Bytes" % byts)
st = 's %f, %f, 10, 20' % (xfreq, yfreq)

s_com.write(str.encode(st))   # Set freq of dacs
time.sleep(1)

while True:
    print(f"Starting scan. Reading {bytes_to_read} bytes at a time...")
    s_com.write(b'r')             # Do a scan

    total_bytes_read = 0
    start_time = time.time()

    # Incrementally ingest the incoming data stream (ie. row by row instead of all at once)
    while True:
        k = s_dat.read(bytes_to_read)

        total_bytes_read += len(k)

        # Break if no more data is received
        if len(k) == 0:
            print(f"Bytes received: {total_bytes_read}")
            break

    elapsed_time = time.time() - start_time
    print(f"Elapsed time: {elapsed_time:.2f} sec")

    if total_bytes_read == 0:
        print("No bytes received. Is the device connected?")
        break
