#!/usr/bin/env python3
import os
import sys
import time
from pathlib import Path

try:
    from PIL import Image
    from pyzbar.pyzbar import decode
except ImportError:
    print("Install: pip install pillow pyzbar")
    sys.exit(1)

# Auto-detect storage locations
ROOTS = [
    Path("/storage/emulated/0"),
    Path("/sdcard"),
    Path.home(),
    Path.cwd(),
]

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SKIP_DIRS = {
    "android", "cache", ".cache", "thumbnails",
    ".thumbnails", "__pycache__", "node_modules", ".git"
}

MAX_SIZE = (1600, 1600)

C = "\033[96m"
G = "\033[92m"
Y = "\033[93m"
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"


def banner():
    os.system("clear")
    print(f"""{C}{B}
╭────────────────────────────────────────╮
│            WiFi QR SCANNER             │
│               AUTO SCAN                │
╰────────────────────────────────────────╯{R}
{D}Automatic image detection | WiFi QR only{R}
""")


def parse_wifi(data):
    if not data.startswith("WIFI:"):
        return None

    fields = {}

    for part in data[5:].split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            fields[key] = value

    return {
        "ssid": fields.get("S", "Unknown"),
        "password": fields.get("P", ""),
        "security": fields.get("T", "Unknown"),
    }


def get_roots():
    roots = []
    seen = set()

    for root in ROOTS:
        try:
            root = root.resolve()
            if root.exists() and root.is_dir():
                if str(root) not in seen:
                    roots.append(root)
                    seen.add(str(root))
        except Exception:
            pass

    return roots


def scan():
    stack = get_roots()
    visited = set()
    total = 0
    hits = []
    start = time.time()

    while stack:
        folder = stack.pop()

        try:
            folder_id = str(folder.resolve())
            if folder_id in visited:
                continue
            visited.add(folder_id)

            with os.scandir(folder) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name.lower() not in SKIP_DIRS:
                                stack.append(Path(entry.path))

                        elif entry.is_file(follow_symlinks=False):
                            if Path(entry.name).suffix.lower() in EXTENSIONS:
                                total += 1

                                try:
                                    with Image.open(entry.path) as image:
                                        image = image.convert("RGB")
                                        image.thumbnail(MAX_SIZE)
                                        decoded = decode(image)

                                    for qr in decoded:
                                        raw = qr.data.decode(
                                            "utf-8", errors="ignore"
                                        )
                                        result = parse_wifi(raw)

                                        if result:
                                            hits.append(
                                                (entry.path, result)
                                            )

                                    print(
                                        f"\r{C}[*] Images scanned: "
                                        f"{total}{R}",
                                        end="", flush=True
                                    )

                                except Exception:
                                    pass

                    except (PermissionError, OSError):
                        pass

        except (PermissionError, OSError):
            pass

    elapsed = time.time() - start
    return total, hits, elapsed


def display_result(index, path, data):
    print(f"\n{G}{B}")
    print("╭──────────────────────────────────────╮")
    print(f"│          WIFI QR FOUND #{index:<14}│")
    print("├──────────────────────────────────────┤")
    print(f"{R}{G}│{R} SSID     : {data['ssid']}")
    print(f"{G}│{R} Password : {data['password'] or '(empty)'}")
    print(f"{G}│{R} Security : {data['security']}")
    print(f"{G}│{R}{D} File     : {path}{R}")
    print(f"{G}╰──────────────────────────────────────╯{R}")


def main():
    banner()

    print(f"{C}[*] Starting automatic scan...{R}")
    print(f"{D}[*] No path input required.{R}\n")

    total, hits, elapsed = scan()

    print("\n")

    if hits:
        for i, (path, data) in enumerate(hits, 1):
            display_result(i, path, data)

        print(f"\n{G}[+] {len(hits)} WiFi QR found.{R}")

    else:
        print(f"{Y}[!] No WiFi QR found.{R}")

    print(f"\n{C}[*] Images processed : {total}{R}")
    print(f"{C}[*] Scan time       : {elapsed:.2f}s{R}")
    print(f"{G}[+] Scan completed.{R}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}[!] Scan stopped.{R}")
