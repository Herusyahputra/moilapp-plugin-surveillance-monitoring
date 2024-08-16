import requests, tarfile, sys, time

def download_file(url, file_path, dest_dir, retries=3):
    for _ in range(retries):
        try:
            response = requests.get(url, stream=True)
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            block_size = 1024  # 1 Kibibyte
            downloaded_size = 0

            with open(file_path, 'wb') as file:
                for data in response.iter_content(block_size):
                    file.write(data)
                    downloaded_size += len(data)
                    print(f"\rDownloaded {downloaded_size} of {total_size_in_bytes} bytes", end='')

            if total_size_in_bytes != 0 and downloaded_size < total_size_in_bytes:
                print("\nDownload incomplete. Retrying...")
                time.sleep(3)
                continue
            else:
                print("\nDownload successful.")
                with tarfile.open(file_path, 'r:xz') as tar:
                    tar.extractall(dest_dir)
                return True

        except Exception as e:
            print(f"\nDownload failed: {e}")
            time.sleep(3)
            continue

    print(f"\nFailed to download {url} after {retries} retries.")
    return False

if sys.platform.startswith('linux'):
    url_ffmpeg = "https://github.com/mhafiz03/mhafiz03.github.io/raw/ffmpeg/ffmpeg-linux-x264.tar.xz"
    ffmpeg_file_path = "ffmpeg-linux.tar.xz"
elif sys.platform == 'win32' or sys.platform == 'cygwin':
    url_ffmpeg = "https://github.com/mhafiz03/mhafiz03.github.io/raw/ffmpeg/ffmpeg-windows-av1.tar.xz"
    ffmpeg_file_path = "ffmpeg-windows.tar.xz"
else:
    print("Unsupported OS.")
    sys.exit(1)

# download_file(url, file_path)
