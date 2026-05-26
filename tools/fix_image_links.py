import os
import re

# --- 設定 ---
POSTS_DIRECTORY = '../_posts'
# --- 設定結束 ---

def fix_links_in_file(file_path):
    """
    在一個文件中尋找並修復帶有尺寸參數的錯誤 Markdown 連結。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
        return False

    original_content = content
    
    # 正則表達式，匹配整個錯誤的 Markdown 圖片語法，並擷取:
    # 1. alt text (非貪婪)
    # 2. 正確的圖片路徑 (以 .png, .jpg, .jpeg, .gif 結尾)
    # 3. 尺寸值 (例如 500 或 50%)
    pattern = re.compile(
        r"!\[(.*?)\]\((/assets/img/posts/.*?\.(?:png|jpg|jpeg|gif))\s*=\s*(\d+%?)x?\)"
    )
    
    matches = pattern.findall(content)
    
    if not matches:
        return False # 文件中沒有需要修復的連結

    print(f"\n[*] Fixing links in: {os.path.basename(file_path)}")
    
    for alt_text, image_path, size_value in matches:
        
        # --- 1. 找到原始的、錯誤的 Markdown 字串 ---
        # 注意: 我們需要手動重建它，因為正則表達式擷取的是部分內容
        # 這裡我們假設了尺寸參數的格式，這對於 re.sub 來說更安全
        # (我們將使用 re.sub 來進行更可靠的替換)
        
        # --- 2. 生成新的 HTML <img> 標籤 ---
        width_style = f"width: {size_value};" if '%' in size_value else f"width: {size_value}px;"
        safe_alt = alt_text.replace('"', '&quot;')
        new_html_tag = f'<img src="{image_path}" alt="{safe_alt}" style="{width_style}">'
        
        print(f"  -> Converting '{os.path.basename(image_path)}' with style '{width_style}'")

        # --- 3. 定義一個替換函數給 re.sub 使用 ---
        # 這比簡單的 content.replace() 更安全，因為它只替換完全匹配的模式
        def create_replacer(replacement_html):
            # 使用閉包來擷取 replacement_html
            def replacer(match):
                # match.group(0) 是整個匹配到的字串, e.g., ![...](...=500x)
                # 我們把它替換成新生成的 HTML
                return replacement_html
            return replacer
        
        # 使用 re.sub 進行替換
        # 為了簡單起見，我們每次只處理一個匹配類型，儘管效率稍低，但更可靠
        # 我們需要重建一個臨時的 pattern 來確保只替換當前循環的這一項
        
        # 簡化版：直接用字串替換 (對於不重疊的情況是安全的)
        original_markdown = f"![{alt_text}]({image_path} ={size_value}x)"
        # 考慮到空格和%號等變化，我們還是用 re.sub 最好
        
    # 一次性替換所有找到的匹配項
    def replacer_func(match):
        alt, path, size = match.groups()
        w_style = f"width: {size};" if '%' in size else f"width: {size}px;"
        s_alt = alt.replace('"', '&quot;')
        return f'<img src="{path}" alt="{s_alt}" style="{w_style}">'

    content = pattern.sub(replacer_func, content)

    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [*] SUCCESS: Updated {file_path}")
            return True
        except Exception as e:
            print(f"  [!] ERROR: Failed to write changes to {file_path}: {e}")
    
    return False


if __name__ == "__main__":
    if not os.path.isdir(POSTS_DIRECTORY):
        print(f"[!] Error: Directory '{POSTS_DIRECTORY}' not found.")
        print("    Please run this script from your Jekyll project's root directory.")
    else:
        print("Starting to fix broken image links with size parameters...")
        total_files_modified = 0
        
        all_files = [os.path.join(POSTS_DIRECTORY, f) for f in os.listdir(POSTS_DIRECTORY) if f.endswith(".md")]

        for file_path in all_files:
            if fix_links_in_file(file_path):
                total_files_modified += 1
        
        print(f"\n[✔] Fixing process finished! Total files modified: {total_files_modified}")
        print("    Please review and commit the changes.")
