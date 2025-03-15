import sys
import struct
import datetime
import re

def extract_timestamps(wallet_path):
    timestamps = []
    
    with open(wallet_path, "rb") as f:
        data = f.read()
    
    # Поиск всех возможных временных меток (32-битные UNIX timestamps)
    for match in re.finditer(rb'\x04time.{0,10}([\x00-\xff]{4})', data):
        timestamp_bytes = match.group(1)
        timestamp = struct.unpack("<I", timestamp_bytes)[0]
        if 1231000000 < timestamp < 2000000000:  # Диапазон 2009-2033 годы
            timestamps.append(timestamp)
    
    return timestamps

def format_timestamps(timestamps):
    for ts in sorted(set(timestamps)):
        date = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"Найдено возможное время: {ts} -> {date}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python extract_time_wallet.py wallet.dat")
        sys.exit(1)
    
    wallet_path = sys.argv[1]
    timestamps = extract_timestamps(wallet_path)
    
    if timestamps:
        format_timestamps(timestamps)
    else:
        print("Временные метки не найдены.")