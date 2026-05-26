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
        fwd_body = body[split_index:]
        lines = fwd_body.split('\n')
        clean_lines = []
        in_header = True
        header_fields = ['from:', 'to:', 'subject:', 'date:', 'sent:', 'cc:', '寄件者:', '收件者:', '日期:', '主旨:', '副本:']
        for line in lines:
            stripped = line.strip()
            if in_header:
                # 遇到空行代表轉寄郵件標頭結束，開始進入原始內文
                if not stripped:
                    in_header = False
                    continue
                # 跳過包含郵件標頭欄位的行
                if any(stripped.lower().startswith(field) for field in header_fields):
                    continue
                # 跳過冒號前置與常見標頭相符的行
                if ':' in stripped and any(stripped.split(':', 1)[0].strip().lower() == f.replace(':', '') for f in header_fields):
                    continue
                # 其他轉寄標頭細節（如過長收件者換行），繼續跳過
                continue
            else:
                clean_lines.append(line)
        return '\n'.join(clean_lines).strip()
    return body.strip()

def main():
    if len(sys.argv) < 3:
        print("Usage: python clean_email.py <filename> <base64_content>")
        sys.exit(1)
        
    raw_filename = sys.argv[1]
    b64_content = sys.argv[2]
    
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
