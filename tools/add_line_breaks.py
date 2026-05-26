import os
import re

# --- 設定 ---

# 腳本會自動將根目錄設定為此檔案的上一層目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 你想要處理的資料夾 (相對於專案根目錄)
POSTS_DIRECTORY = os.path.join(PROJECT_ROOT, '_posts')

# 2. 是否為「試運行」模式？
#    強烈建議保持 True 進行第一次執行，檢查變更是否符合預期。
#    確認無誤後，再改為 False 來實際修改檔案。
DRY_RUN = False

# --- 腳本主體 ---

def is_prose_line(line):
    """
    判斷某一行是否為需要處理的「純文字」行。
    這是一個更嚴格的版本，排除了更多非段落內容。
    """
    stripped_line = line.strip()
    
    # 排除所有非純文字的情況
    if (not stripped_line or  # 空白行
        stripped_line.endswith('  ') or
        stripped_line.startswith(('#', '>', '---', '***', '```')) or
        re.match(r'^\s*[-*+]\s', stripped_line) or  # 無序列表
        re.match(r'^\s*\d+\.\s', stripped_line) or  # 有序列表
        re.match(r'^[a-zA-Z0-9_]+:\s*.*', stripped_line) or # 排除 'Key: Value' 格式 (例如 Ref1:, 主機板：)
        stripped_line.startswith('|') or  # 表格
        stripped_line.startswith('{:') or  # Kramdown 屬性
        stripped_line.startswith('<') or  # HTML 標籤
        re.fullmatch(r'!\[.*?\]\(.*?\)', stripped_line) or # 整行都是圖片
        re.fullmatch(r'\[.*?\]\(.*?\)', stripped_line) # 整行都是連結
    ):
        return False
        
    return True

def process_markdown_file(file_path, dry_run=True):
    """
    處理單一 Markdown 檔案，為多行文字段落加上行尾空格。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"[!] 讀取檔案 {file_path} 時發生錯誤: {e}")
        return False

    new_lines = []
    in_code_block = False
    modified = False
    
    # 將檔案內容分割為 Front Matter 和主要內容
    content_str = "".join(lines)
    parts = content_str.split('---', 2)
    
    if len(parts) < 3 or not parts[0].strip() == "":
        # 沒有有效的 Front Matter，將整個檔案視為內容
        main_content_lines = lines
        new_lines = [] # 重置
    else:
        # 有 Front Matter，將其保留不動
        front_matter = f"---\n{parts[1]}---\n"
        main_content_lines = parts[2].splitlines(True)
        new_lines.extend(front_matter.splitlines(True))

    for i, line in enumerate(main_content_lines):
        stripped_line = line.strip()

        if stripped_line.startswith('```'):
            in_code_block = not in_code_block
        
        if in_code_block:
            new_lines.append(line)
            continue

        if is_prose_line(line):
            is_multiline_paragraph = False
            if i + 1 < len(main_content_lines):
                next_line = main_content_lines[i + 1]
                if is_prose_line(next_line):
                    is_multiline_paragraph = True
            
            if is_multiline_paragraph:
                modified_line = line.rstrip('\n') + "  \n"
                new_lines.append(modified_line)
                if line != modified_line:
                    modified = True
                    if dry_run:
                        print(f"--- 在檔案: {os.path.basename(file_path)} ---")
                        print(f"- 舊: {line.rstrip()}")
                        print(f"+ 新: {modified_line.rstrip()}")
                        print("-" * 10)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if modified and not dry_run:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"[成功] 已修改: {file_path}")
        except Exception as e:
            print(f"[!] 寫入檔案 {file_path} 時發生錯誤: {e}")
    
    return modified

if __name__ == "__main__":
    if not os.path.isdir(POSTS_DIRECTORY):
        print(f"[!] 錯誤: 找不到資料夾 '{POSTS_DIRECTORY}'。")
        print("    請確認此腳本位於專案根目錄下的 'tools' 資料夾內。")
    else:
        print("開始修正 Markdown 換行...")
        if DRY_RUN:
            print("[提示] 目前為「試運行」模式，不會實際修改任何檔案。")
            print("       請檢視以下預計的變更。")
        else:
            print("[警告] 「試運行」模式已關閉，檔案將會被直接修改。")

        total_modified_files = 0
        for filename in os.listdir(POSTS_DIRECTORY):
            if filename.endswith(".md"):
                file_path = os.path.join(POSTS_DIRECTORY, filename)
                if process_markdown_file(file_path, dry_run=DRY_RUN):
                    total_modified_files += 1
        
        print(f"\n[✔] 處理完畢。預計/實際 修改的檔案總數: {total_modified_files}")
