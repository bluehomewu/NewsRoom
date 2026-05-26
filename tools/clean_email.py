import base64
import json
import os
import re
import sys
from html.parser import HTMLParser

class HTMLToMarkdown(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.state_stack = []
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag in ('b', 'strong'):
            self.result.append('**')
            self.state_stack.append('bold')
        elif tag in ('i', 'em'):
            self.result.append('*')
            self.state_stack.append('italic')
        elif tag == 'a':
            href = attrs_dict.get('href', '')
            self.result.append('[')
            self.state_stack.append(('link', href))
        elif tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '圖片')
            self.result.append(f'![{alt}]({src})')
        elif tag in ('p', 'div'):
            # 確保段落開始前有至少一個空行 (兩個換行)
            if self.result:
                last_content = "".join(self.result[-2:])
                if not last_content.endswith('\n\n'):
                    if last_content.endswith('\n'):
                        self.result.append('\n')
                    else:
                        self.result.append('\n\n')
            self.state_stack.append('paragraph')
        elif tag == 'br':
            self.result.append('\n')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            level = int(tag[1])
            self.result.append('\n' + '#' * level + ' ')
            self.state_stack.append('heading')
        else:
            self.state_stack.append(tag)

    def handle_endtag(self, tag):
        if not self.state_stack:
            return
            
        state = self.state_stack.pop()
        
        if tag in ('b', 'strong'):
            self.result.append('**')
        elif tag in ('i', 'em'):
            self.result.append('*')
        elif tag == 'a':
            if isinstance(state, tuple) and state[0] == 'link':
                href = state[1]
                self.result.append(f']({href})')
            else:
                self.result.append(']')
        elif tag in ('p', 'div'):
            self.result.append('\n\n')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.result.append('\n')

    def handle_data(self, data):
        if self.state_stack and self.state_stack[-1] in ('script', 'style'):
            return
        self.result.append(data)

    def get_markdown(self):
        text = "".join(self.result)
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        return text.strip()

def html_to_markdown(html):
    # 先做一些預處理，例如移除 head, script, style 區塊以防雜訊
    html = re.sub(r'<head>[\s\S]*?</head>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    
    parser = HTMLToMarkdown()
    parser.feed(html)
    return parser.get_markdown()

def is_html(text):
    html_patterns = [
        r'<p\b', r'<div\b', r'<span\b', r'<strong\b', r'<b\b', r'<a\b', r'<img\b', r'<br\b', r'<html\b'
    ]
    return any(re.search(pat, text, re.IGNORECASE) for pat in html_patterns)

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
    # 1. 偵測並轉換 HTML
    if is_html(body):
        body = html_to_markdown(body)

    # 2. 定位常見轉寄分界線
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
        for line in lines:
            stripped = line.strip()
            if in_header:
                if not stripped:
                    # 跳過空行，但不結束標頭（因 HTML 標頭常夾雜空行）
                    continue
                if is_header_field(line):
                    # 跳過標頭欄位
                    continue
                
                # 遇到第一個既非空行也非標頭行的普通行，代表標頭區塊正式結束，開始讀取正文
                in_header = False
                clean_lines.append(line)
            else:
                clean_lines.append(line)
        result_body = '\n'.join(clean_lines).strip()
    else:
        result_body = body.strip()
        
    # 移除開頭常見的媒體朋友招呼語
    greeting_pattern = r'^\s*(親愛的|各位)?媒體朋友\s*[：，,:]?\s*\n+'
    result_body = re.sub(greeting_pattern, '', result_body, flags=re.IGNORECASE).strip()
        
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
        
    # 移除 PR Contacts 聯絡資訊、長分隔線與免責聲明等尾部雜訊
    # 1. 依長減號橫線截斷 (10個以上，容許尾端有星號等標記)
    result_body = re.split(r'\n\s*-{10,}.*', result_body)[0]
    # 2. 依長等號橫線截斷 (10個以上，容許尾端有星號等標記)
    result_body = re.split(r'\n\s*={10,}.*', result_body)[0]
    # 3. 依 PR Contacts 或 媒體/技術公關 關鍵字整行及之後截斷
    lines = result_body.split('\n')
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if "ASUS PR Contacts" in stripped or "PR Contacts" in stripped or stripped.startswith("媒體公關") or stripped.startswith("技術公關"):
            break
        clean_lines.append(line)
        
    return '\n'.join(clean_lines).strip()

def is_valid_image_data(data):
    """檢查二進位資料是否為有效的圖片格式（而非 HTML 頁面等錯誤內容）"""
    # 常見圖片格式的 magic bytes
    image_signatures = [
        b'\xff\xd8\xff',       # JPEG
        b'\x89PNG\r\n\x1a\n',  # PNG
        b'GIF87a', b'GIF89a',  # GIF
        b'RIFF',               # WebP (RIFF....WEBP)
        b'BM',                 # BMP
        b'<svg',               # SVG (XML-based)
    ]
    for sig in image_signatures:
        if data[:len(sig)] == sig:
            return True
    # WebP 進一步確認
    if data[:4] == b'RIFF' and len(data) > 11 and data[8:12] == b'WEBP':
        return True
    return False


def replace_cid_images(text, attachments, post_base_name):
    # 尋找所有 cid: 連結，格式通常是 ![alt](cid:xxx) 或 [alt](cid:xxx)
    # 我們用正則表達式找出 cid: 後面直到 ) 或 空格 的字串
    cid_pattern = r'cid:([^\)\s]+)'
    
    def repl(match):
        cid_value = match.group(1).strip()
        # 去除可能存在的角括號
        cid_value_clean = cid_value.strip('<>')
        
        # 尋找匹配的附件
        matched_attachment = None
        for att in attachments:
            # 使用 original_filename 進行名稱匹配，因為 original_filename 保留了原始郵件中的長檔名
            att_name = att.get('original_filename', '').strip()
            if not att_name:
                att_name = att.get('filename', '').strip()
                
            att_cid = att.get('contentId', '')
            if att_cid:
                att_cid = att_cid.strip('<>')
            
            # 1. 精確匹配 contentId
            if att_cid and att_cid.lower() == cid_value_clean.lower():
                matched_attachment = att
                break
                
            # 2. 附件檔名在 cid 之中 (例如 cid: image001.png@01DBC1FA)
            if att_name and att_name.lower() in cid_value_clean.lower():
                matched_attachment = att
                break
                
            # 3. cid 在附件檔名之中
            if att_name and cid_value_clean.lower() in att_name.lower():
                matched_attachment = att
                break
                
            # 4. 去除副檔名後的檔名匹配
            att_name_no_ext = os.path.splitext(att_name)[0]
            cid_value_no_ext = os.path.splitext(cid_value_clean)[0]
            if att_name_no_ext and att_name_no_ext.lower() == cid_value_no_ext.lower():
                matched_attachment = att
                break
                
        if matched_attachment:
            # 替換為重新命名後的安全檔名 filename (例如 image_1.jpg)
            safe_name = matched_attachment.get('filename')
            return f"/assets/img/posts/{post_base_name}/{safe_name}"
        else:
            print(f"Warning: Could not find matching attachment for CID: {cid_value}")
            return match.group(0) # 保持原樣
            
    return re.sub(cid_pattern, repl, text)

def main():
    raw_filename = ""
    b64_content = ""
    attachments = []
    payload = {}
    
    # 優先從環境變數 PAYLOAD_JSON 讀取
    payload_json = os.environ.get('PAYLOAD_JSON')
    if payload_json:
        try:
            payload = json.loads(payload_json)
            raw_filename = payload.get('filename', '').strip()
            b64_content = payload.get('content', '').strip()
            attachments = payload.get('attachments', [])
            print("Successfully loaded payload from PAYLOAD_JSON environment variable.")
        except Exception as e:
            print(f"Error parsing PAYLOAD_JSON: {e}")
            sys.exit(1)
            
    # 若環境變數不存在，退回使用命令列參數（以相容本地測試與手動觸發）
    if not raw_filename and not b64_content:
        if len(sys.argv) >= 3:
            raw_filename = sys.argv[1].strip()
            b64_content = sys.argv[2].strip()
            print("Loaded payload from command line arguments.")
        else:
            # 支援手動觸發 (workflow_dispatch) 時提供預設測試參數，防範 IsADirectoryError 空檔名錯誤
            import datetime
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            raw_filename = f"{today}-manual-trigger-test.md"
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
            print("Using default manual trigger test payload.")

    # 1. 清洗檔名
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
        
        # 4. 處理與儲存圖片附件
        valid_attachments = []
        post_base_name = payload.get('post_base_name', '').strip()
        if not post_base_name:
            post_base_name = os.path.splitext(clean_filename)[0]
            
        # 清洗 post_base_name：移除 Fwd 前綴（使其與 clean_filename 一致）
        pbn_match = re.match(r'^(\d{4}-\d{2}-\d{2}-)(.+)$', post_base_name)
        if pbn_match:
            pbn_rest = clean_text_prefix(pbn_match.group(2))
            post_base_name = f"{pbn_match.group(1)}{pbn_rest}"
            
        # 將 post_base_name 中的空白與冒號替換為安全字元
        post_base_name = post_base_name.replace(':', '_').replace(' ', '_')
        
        if attachments:
            img_dir = os.path.join('assets', 'img', 'posts', post_base_name)
            img_index = 1
            
            for att in attachments:
                name = att.get('filename', '').strip()
                content_bytes = att.get('contentBytes', '')
                content_type = att.get('contentType', '')
                
                if not name:
                    continue
                    
                # 判定是否為圖片
                is_image = False
                if content_type and content_type.lower().startswith('image/'):
                    is_image = True
                else:
                    _, ext = os.path.splitext(name.lower())
                    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'):
                        is_image = True
                        
                if is_image:
                    try:
                        # 儲存原始檔名用於之後的 cid 匹配
                        att['original_filename'] = name
                        
                        # 將實體圖片重新命名為安全檔名 (例如 image_1.jpg)
                        # 避免超長中文字與全形標點在 Jekyll 和 URL 解析時壞掉
                        _, ext = os.path.splitext(name.lower())
                        if not ext:
                            ext = '.jpg'
                        safe_name = f"image_{img_index}{ext}"
                        img_index += 1
                        
                        # 更新附件檔名為 safe_name
                        att['filename'] = safe_name
                        img_path = os.path.join(img_dir, safe_name)
                        
                        # 從 contentBytes (Base64) 解碼並儲存圖片
                        if content_bytes:
                            os.makedirs(img_dir, exist_ok=True)
                            img_data = base64.b64decode(content_bytes)
                            
                            # 驗證解碼後的資料確實是圖片，而非 HTML 頁面等錯誤內容
                            if not is_valid_image_data(img_data):
                                print(f"WARNING: Decoded data for {name} is NOT a valid image (possibly HTML). Skipping.")
                                print(f"  First 100 bytes: {img_data[:100]}")
                                continue
                                
                            with open(img_path, 'wb') as img_f:
                                img_f.write(img_data)
                            print(f"Successfully saved image ({len(img_data)} bytes): {img_path}")
                            valid_attachments.append(att)
                        else:
                            print(f"WARNING: No contentBytes for attachment {name}. Skipping image save.")
                            
                    except Exception as e:
                        print(f"Error processing attachment {name}: {e}")
                        
        # 5. 改寫正文中的 cid: 圖片連結，並收集未在正文中引用的圖片
        referenced_images = []
        if valid_attachments:
            clean_body_text = replace_cid_images(clean_body_text, valid_attachments, post_base_name)
            
            # 檢查哪些 valid_attachments 檔案沒有被 html 的 img 標籤引用
            # 由於在正文中被引用的圖片會被取代為包含安全名稱 (如 image_1.jpg) 的連結
            # 我們可以比對 clean_body_text 是否包含 safe_name
            for att in valid_attachments:
                safe_name = att.get('filename')
                if safe_name and safe_name not in clean_body_text:
                    referenced_images.append(att)
                    
        # 若有未被正文引用的圖片附件（例如信件直接以附件發送而 HTML 中無 img 元素），則自動追加到文章尾端
        if referenced_images:
            clean_body_text += "\n\n---\n\n### 相關圖片\n\n"
            for att in referenced_images:
                safe_name = att.get('filename')
                original_name = att.get('original_filename', '圖片')
                
                # 簡短 alt 說明 (去副檔名，並限制長度最長 30 個字)
                alt_text = os.path.splitext(original_name)[0]
                if len(alt_text) > 30:
                    alt_text = alt_text[:30] + "..."
                    
                clean_body_text += f"![{alt_text}](/assets/img/posts/{post_base_name}/{safe_name})\n\n"
            
        final_content = f"---\n{clean_front_matter}---\n\n{clean_body_text}"
    else:
        final_content = raw_content
        
    # 6. 寫入檔案
    os.makedirs('_posts', exist_ok=True)
    dest_path = os.path.join('_posts', clean_filename)
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"Successfully processed and saved to: {dest_path}")
    
    # 7. 將新檔名寫入 GitHub Actions 輸出
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a', encoding='utf-8') as go:
            go.write(f"clean_filename={clean_filename}\n")
            
if __name__ == '__main__':
    main()
