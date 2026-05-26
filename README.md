# NewsRoom 新聞中心

NewsRoom 是一個專為發佈合作夥伴新聞稿設計的入口網站。網站託管於 GitHub Pages，並配置自訂網域部署於 `https://edwardwu23.com/NewsRoom/`。

本專案特色在於完全**無伺服器架構 (Serverless)**，且後端整合 **Microsoft Power Automate**，實現發送電子郵件即可自動發佈新聞稿的無程式碼 (No-Code) 自動化流程。

---

## 專案架構

- **靜態網站產生器 (SSG)**：Jekyll
- **樣式設計**：客製化 CSS（位於 `assets/css/style.css`），採用現代玻璃帷幕與深色質感主題。
- **自動化發佈管道**：當新郵件寄送至 `NewsRoom@edwardwu23.com` 時，Power Automate 會自動轉換內文，並透過 GitHub REST API 寫入 `_posts/` 目錄中。

---

## 目錄結構

```text
NewsRoom/
├── _posts/                    # 由 Power Automate 自動寫入的新聞稿
├── _layouts/                  # Jekyll 網站版面配置
│   ├── default.html           # 基礎 HTML5 骨架（含導覽列、頁尾與響應式 CSS）
│   └── post.html              # 新聞稿單頁佈局
├── assets/                    # 靜態資源
│   └── css/
│       └── style.css          # 自訂現代質感 CSS 樣式表
├── _config.yml                # Jekyll 網站設定檔
├── AGENTS.md                  # 本地 AI 代理引導指南
├── README.md                  # 本說明文件
└── POWER_AUTOMATE_GUIDE.md    # Power Automate 雲端工作流設定指南
```

---

## 本地預覽與開發

若要在本地環境中啟動並預覽網站，請遵循以下步驟：

### 1. 安裝 Ruby 依賴套件

本專案使用 Bundler 管理套件依賴。請在專案根目錄下執行：

```bash
bundle install
```

### 2. 啟動 Jekyll 伺服器

執行以下指令啟動 Jekyll 本地開發伺服器：

```bash
bundle exec jekyll serve
```

伺服器啟動後，請在瀏覽器中開啟：
[http://localhost:4000/NewsRoom/](http://localhost:4000/NewsRoom/)

*(注意：由於 `_config.yml` 中設定了 `baseurl: "/NewsRoom"`，本地預覽路徑亦會包含 `/NewsRoom`字樣)*

---

## 自動化工作流設定

關於如何設定 Power Automate 串接電子郵件與 GitHub API 的詳細說明，請參閱：
[POWER_AUTOMATE_GUIDE.md](file:///home/edwardwu/workspace/NewsRoom/POWER_AUTOMATE_GUIDE.md)
