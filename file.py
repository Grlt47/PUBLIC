import socket
import sys
import time
import random
from datetime import datetime
import threading
from queue import Queue

port_queue = Queue()
open_ports = []
lock = threading.Lock()

COMMON_PORTS = [
    20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995,
    3306, 3389, 8080, 8443, 5900, 1433, 6379, 9200, 5432, 1521,
    139, 445, 135, 389, 636, 88, 161, 162
]

def scan_port(target_ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)        
        
        result = sock.connect_ex((target_ip, port))
        sock.close()
        
        if result == 0:
            with lock:
                open_ports.append((target_ip, port))
                print(f"[+] {target_ip:<15} : {port:<5} OPEN")
                
    except:
        pass

    time.sleep(random.uniform(1.2, 2.2))


def worker():
    while True:
        target_ip, port = port_queue.get()
        scan_port(target_ip, port)
        port_queue.task_done()


def load_targets(file_path):
    targets = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    targets.append(line)
        return targets
    except FileNotFoundError:
        print(f"[-] File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Error reading file: {e}")
        sys.exit(1)


def main():
    target_file = sys.argv[1]
    targets = load_targets(target_file)
    print(f"Loaded {len(targets)} list from {target_file}")
    
    print(f"Using {len(COMMON_PORTS)} common ")
    print("work started at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    start_time = time.time()
    num_threads = 20
    
    for _ in range(num_threads):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
    for target in targets:
        try:
            target_ip = socket.gethostbyname(target)
            print(f"Queuing → {target} ({target_ip})")
            
            for port in COMMON_PORTS:
                port_queue.put((target_ip, port))
                
        except socket.gaierror:
            print(f"[-] Could not resolve: {target}")
            continue
    port_queue.join()
    print("\n" + "=" * 70)
    print("Work Completed!")
    print(f"Duration: {time.time() - start_time:.2f} seconds")
    print(f"Total work items found: {len(open_ports)}")
    
    if open_ports:
        print("\nwork items Summary:")
        open_ports.sort()
        for ip, port in open_ports:
            print(f"    {ip:<15} : {port}")
    else:
        print("No work items found.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] work stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")