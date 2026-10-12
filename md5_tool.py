import hashlib
import os
import sys


def compute_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, "rb") as file_handle:
        while True:
            chunk = file_handle.read(1048576)
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest()


def main():
    current_dir = os.getcwd()
    self_path = os.path.abspath(sys.argv[0])
    output_name = sys.argv[1] if len(sys.argv) > 1 else "md5_list.txt"
    output_path = os.path.abspath(os.path.join(current_dir, output_name))
    entries = os.listdir(current_dir)
    results = []
    for name in entries:
        file_path = os.path.join(current_dir, name)
        if os.path.isdir(file_path):
            continue
        if os.path.abspath(file_path) == self_path:
            continue
        if os.path.abspath(file_path) == output_path:
            continue
        try:
            md5_value = compute_md5(file_path)
            results.append((name, md5_value))
        except OSError as exc:
            sys.stderr.write(f"跳过文件: {name} ({exc})\n")
    results.sort(key=lambda item: item[0].lower())
    with open(output_path, "w", encoding="utf-8") as output_file:
        for name, md5_value in results:
            output_file.write(f"{name}\t{md5_value}\n")


if __name__ == "__main__":
    main()
