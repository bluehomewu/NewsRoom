import base64
import os
import re
import sys

def clean_text_prefix(text):
    # 移除常見轉寄前綴（不分大小寫），支援 fwd:, fwd_, 轉寄:, 轉寄_ 等
    pattern = r'^(fwd\s*[:_]\s*|轉寄\s*[:_]\s*)+(.+)$'
    match = re.match(pattern, text, re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return text.strip()

def is_header_field(line):
    stripped = line.strip()
    if not stripped:
        return False
    
    # 標準化冒號，將全形冒號替換為半形冒號以利處理
    normalized = stripped.replace('：', ':')
    
    header_fields = ['from:', 'to:', 'subject:', 'date:', 'sent:', 'cc:', '寄件者:', '收件者:', '日期:', '主旨:', '副本:']
    
    # 檢查是否以任何 header_fields 開頭
    if any(normalized.lower().startswith(field) for field in header_fields):
        return True
        
    # 檢查是否包含冒號，且冒號前面的單字屬於 header_fields
    if ':' in normalized:
        prefix = normalized.split(':', 1)[0].strip().lower()
        if any(prefix == f.replace(':', '') for f in header_fields):
            return True
            
    return False

def merge_paragraph_lines(paragraph_text):
    # 合併普通段落內部的硬換行
    lines = paragraph_text.split('\n')
    if len(lines) <= 1:
        return paragraph_text
        
    result = lines[0].strip()
    for line in lines[1:]:
        next_line = line.strip()
        if not next_line:
            continue
            
        # 檢查 result 的最後一個字元與 next_line 的第一個字元
        last_char = result[-1] if result else ''
        first_char = next_line[0] if next_line else ''
        
        # 判定是否為英數字或常見英文符號
        is_last_eng = last_char.isalnum() or last_char in "-_°®™©$#+/"
        is_first_eng = first_char.isalnum() or first_char in "-_°®™©$#+/"
        
        if is_last_eng and is_first_eng:
            result += " " + next_line
        else:
            result += next_line
            
    return result

def clean_links_only(text):
    # 將商品名 [URL] 格式的超連結轉為 [商品名](URL)
    # 限制商品名稱僅為英數字、空格、連接號等，排除中文字以防連帶匹配 "與" 等連接詞
    link_pattern = r'([A-Za-z0-9\s\-\_°®™©\.\+]+?)\n*\s*\[(https?://[A-Za-z0-9\.\/\-\_\?\&\=\%\#\:\+]+)\]'
    
    def repl(match):
        name = match.group(1).strip()
        url = match.group(2).strip()
        clean_name = merge_paragraph_lines(name)
        return f"[{clean_name}]({url})"
        
    return re.sub(link_pattern, repl, text)

def clean_body(body):
    # 定位常見轉寄分界線
    fwd_patterns = [
        r'-+\s*Forwarded\s*message\s*-+',
        r'-+\s*轉寄的郵件\s*-+',
        r'-+\s*Original\s*Message\s*-+'
    ]
    
    split_index = -1
    for pattern in fwd_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            split_index = match.end()
            break
            
    if split_index != -1:
        # 有分界線，從分界線之後開始清除標頭
        fwd_body = body[split_index:]
        lines = fwd_body.split('\n')
        has_header = True
    else:
        # 沒有分界線，檢查開頭幾行（跳過前置空行）是否含有標頭欄位
        lines = body.split('\n')
        has_header = False
        non_empty_count = 0
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            non_empty_count += 1
            if is_header_field(line):
                has_header = True
                break
            if non_empty_count >= 5: # 只檢查前 5 個非空行
                break

    if has_header:
        clean_lines = []
        in_header = True
        header_started = False
        for line in lines:
            stripped = line.strip()
            if in_header:
                if not stripped:
                    if header_started:
                        # 已經讀過標頭，遇到空行代表標頭結束
                        in_header = False
                    continue
                
                if is_header_field(line):
                    header_started = True
                    continue
                
                # 如果已經開始標頭，但此行不是標頭欄位（可能是折行或標頭內其他資訊），繼續跳過
                if header_started:
                    continue
                
                # 如果還沒開始標頭，就遇到了非空行，代表這不是標頭區塊
                in_header = False
                clean_lines.append(line)
            else:
                clean_lines.append(line)
        result_body = '\n'.join(clean_lines).strip()
    else:
        result_body = body.strip()
        
    # 段落重新拼裝與超連結格式化
    # 將內文以空行拆分成多個段落
    paragraphs = re.split(r'(\n\s*\n+)', result_body)
    cleaned_paragraphs = []
    
    for part in paragraphs:
        if not part.strip():
            cleaned_paragraphs.append(part)
            continue
            
        # 檢查該段落是否為 Markdown 特殊格式（列表、標題、表格等）或 PR 聯繫人
        lines = part.split('\n')
        is_markdown_special = False
        
        for line in lines:
            stripped_line = line.strip()
            # 偵測 Markdown 清單、標題、表格、引用等，以及有序清單
            if stripped_line.startswith(('#', '-', '*', '+', '>', '|')) or re.match(r'^\d+\.(?!\d)', stripped_line):
                is_markdown_special = True
                break
                
        if "ASUS PR Contacts" in part or "媒體公關" in part or "技術公關" in part:
            is_markdown_special = True
            
        if any(re.match(r'^[\-\=\_]{10,}$', line.strip()) for line in lines):
            is_markdown_special = True
            
        if is_markdown_special:
            # 特殊段落不合併硬換行，只優化可能存在的超連結
            cleaned_part = clean_links_only(part)
            cleaned_paragraphs.append(cleaned_part)
        else:
            # 普通內文段落，合併硬換行並優化超連結
            merged_text = merge_paragraph_lines(part)
            cleaned_part = clean_links_only(merged_text)
            cleaned_paragraphs.append(cleaned_part)
            
    result_body = "".join(cleaned_paragraphs).strip()
        
    # 移除華碩免責聲明
    asus_disclaimer_pattern = r'={10,}\s*This email and any attachments to it contain confidential information[\s\S]*?={10,}'
    result_body = re.sub(asus_disclaimer_pattern, '', result_body)
    
    return result_body.strip()

def main():
    if len(sys.argv) < 3:
        print("Usage: python clean_email.py <filename> <base64_content>")
        sys.exit(1)
        
    raw_filename = sys.argv[1].strip()
    b64_content = sys.argv[2].strip()
    
    # 支援手動觸發 (workflow_dispatch) 時提供預設測試參數，防範 IsADirectoryError 空檔名錯誤
    if not raw_filename:
        import datetime
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        raw_filename = f"{today}-manual-trigger-test.md"
        
    if not b64_content:
        default_post = """---
layout: post
title: "手動測試：自動發佈工作流驗證"
date: 2026-05-26 12:00:00 +0800
categories: test
---

這是一篇透過 GitHub Actions 網頁端手動觸發（workflow_dispatch）產生的測試文章。

如果您能在新聞首頁看到此文章，代表郵件發文與網站部署工作流皆正常運行！
"""
        b64_content = base64.b64encode(default_post.encode('utf-8')).decode('utf-8')

    
    # 1. 清洗檔名
    # 檔名格式通常為 YYYY-MM-DD-filename.md
    filename_match = re.match(r'^(\d{4}-\d{2}-\d{2}-)(.+)$', raw_filename)
    if filename_match:
        date_prefix = filename_match.group(1)
        rest_name = filename_match.group(2)
        clean_rest = clean_text_prefix(rest_name)
        clean_filename = f"{date_prefix}{clean_rest}"
    else:
        clean_filename = clean_text_prefix(raw_filename)
        
    # 將空白與冒號替換為安全字元，以免造成路徑問題
    clean_filename = clean_filename.replace(':', '_').replace(' ', '_')
    
    # 2. 解碼 Base64 內文
    try:
        decoded_bytes = base64.b64decode(b64_content)
        raw_content = decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"Error decoding base64 content: {e}")
        sys.exit(1)
        
    # 3. 解析 Jekyll Front Matter 與內文
    parts = raw_content.split('---\n', 2)
    if len(parts) >= 3:
        front_matter = parts[1]
        body = parts[2]
        
        # 清洗 Front Matter 中的 title
        fm_lines = front_matter.split('\n')
        clean_fm_lines = []
        for line in fm_lines:
            if line.strip().startswith('title:'):
                title_match = re.match(r'^(title:\s*)(["\']?)(.+?)(["\']?)$', line)
                if title_match:
                    prefix = title_match.group(1)
                    quote_start = title_match.group(2)
                    title_text = title_match.group(3)
                    quote_end = title_match.group(4)
                    clean_title = clean_text_prefix(title_text)
                    clean_fm_lines.append(f"{prefix}{quote_start}{clean_title}{quote_end}")
                else:
                    clean_fm_lines.append(line)
            else:
                clean_fm_lines.append(line)
                
        clean_front_matter = '\n'.join(clean_fm_lines)
        clean_body_text = clean_body(body)
        
        final_content = f"---\n{clean_front_matter}---\n\n{clean_body_text}"
    else:
        final_content = raw_content
        
    # 4. 寫入檔案
    os.makedirs('_posts', exist_ok=True)
    dest_path = os.path.join('_posts', clean_filename)
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"Successfully processed and saved to: {dest_path}")
    
    # 5. 將新檔名寫入 GitHub Actions 輸出
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as go:
            go.write(f"clean_filename={clean_filename}\n")
            
if __name__ == '__main__':
    main()
