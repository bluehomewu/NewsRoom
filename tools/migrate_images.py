import os
import re
import requests
from urllib.parse import urlparse

# --- 請在這裡設定 ---

# 1. 你的文章所在的資料夾
POSTS_DIRECTORY = '../_posts'

# 2. 下載的圖片要儲存到哪個資料夾
IMAGE_DEST_DIR = os.path.join('../', 'assets', 'img', 'posts')

# 3. 在 Markdown 檔案中，替換後的圖片路徑前綴
#    (前面的 '/' 非常重要，代表網站根目錄)
NEW_IMAGE_PATH_PREFIX = '/assets/img/posts/'

# ---------------------


def find_hackmd_urls(directory):
    """
    掃描指定目錄下的所有 .md 檔案，找出所有 HackMD 圖片連結。
    """
    hackmd_urls = set()
    file_list = []
    
    # 正規表示式，用來匹配 HackMD 的上傳連結
    # 它會捕捉到完整的 URL，無論是在 () 還是 "" 中
    url_pattern = re.compile(r"https://hackmd\.io/_uploads/[^)\s\"\']+")

    print(f"[*] Scanning files in '{directory}'...")
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            file_list.append(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    found_urls = url_pattern.findall(content)
                    for url in found_urls:
                        hackmd_urls.add(url)
            except Exception as e:
                print(f"[!] Error reading {file_path}: {e}")
                
    print(f"[+] Found {len(hackmd_urls)} unique HackMD image URLs across {len(file_list)} files.")
    return list(hackmd_urls), file_list


def download_images(urls, dest_dir):
    """
    下載所有圖片到指定的本地資料夾。
    返回一個 {原始URL: 新相對路徑} 的對應字典。
    """
    os.makedirs(dest_dir, exist_ok=True)
    url_map = {}
    
    print("\n[*] Starting image download process...")
    for i, url in enumerate(urls):
        # 從 URL 中提取檔名 (例如 'HJ0pJjLige.png')
        # 移除可能存在的 HackMD 尺寸參數 (例如 '=500x')
        filename = os.path.basename(urlparse(url).path)
        local_path = os.path.join(dest_dir, filename)
        new_relative_path = os.path.join(NEW_IMAGE_PATH_PREFIX, filename).replace('\\', '/')

        url_map[url] = new_relative_path

        if os.path.exists(local_path):
            print(f"  ({i+1}/{len(urls)}) SKIPPED: '{filename}' already exists.")
            continue

        try:
            print(f"  ({i+1}/{len(urls)}) Downloading '{filename}'...")
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
            else:
                print(f"  [!] FAILED: Could not download {url} (Status: {response.status_code})")
        except Exception as e:
            print(f"  [!] FAILED: Error downloading {url}: {e}")
            
    return url_map


def replace_urls_in_files(files, url_map):
    """
    遍歷所有檔案，將舊的 URL 替換成新的本地路徑。
    """
    print("\n[*] Starting URL replacement process...")
    total_files_modified = 0
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            for old_url, new_path in url_map.items():
                content = content.replace(old_url, new_path)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  UPDATED: {file_path}")
                total_files_modified += 1

        except Exception as e:
            print(f"[!] Error processing {file_path}: {e}")
    
    print(f"[+] Modified {total_files_modified} files.")


if __name__ == "__main__":
    if not os.path.isdir(POSTS_DIRECTORY):
        print(f"[!] Error: Directory '{POSTS_DIRECTORY}' not found.")
        print("    Please run this script from your Jekyll project's root directory.")
    else:
        # 步驟 1: 找出所有連結和檔案
        hackmd_urls, files_to_process = find_hackmd_urls(POSTS_DIRECTORY)
        
        if not hackmd_urls:
            print("\n[*] No HackMD URLs found. Nothing to do.")
        else:
            # 步驟 2: 下載所有圖片
            url_to_new_path_map = download_images(hackmd_urls, IMAGE_DEST_DIR)
            
            # 步驟 3: 在檔案中替換連結
            replace_urls_in_files(files_to_process, url_to_new_path_map)
            
            print("\n[✔] Migration process finished!")
            print("    Please check the changes and commit the new image files and updated posts to Git.")
