import subprocess

host = "192.168.139.30"
port = "5000"

cmd = f"(sleep 1; echo 'show interfaces status'; sleep 2) | telnet {host} {port} 2>/dev/null"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)

print("=== RAW OUTPUT ===")
print(repr(result.stdout))
print("=== END ===")