# 均線掃描器（MA30 / 45 / 60）

在 iPhone 上左右滑動，一檔一檔看 K 線和均線。加密貨幣和台股分開兩頁，上方可以篩選：多頭排列、剛突破MA30、站上MA30、空頭排列。

- 加密貨幣：Binance 成交額前 60 名的 USDT 交易對（日 K）。打開某一檔時，會再向 Binance 抓一次最新 K 線，有抓到的話會顯示「即時」。
- 台股：上市股票當日成交值前 100 名（日 K，資料來源 Yahoo Finance）。
- 資料由 GitHub Actions 每 4 小時更新一次，全部免費。

## 部署步驟（第一次大約 10 分鐘，用電腦做比較方便）

1. 註冊或登入 GitHub，新增一個 **Public** repository，例如取名 `ma-scanner`。
2. 在 repo 頁面點 **Add file → Upload files**，把這個資料夾裡的所有檔案拖進去（包含 `.github` 資料夾），然後 Commit。
   - 如果 `.github` 資料夾沒有上傳成功：改用 **Add file → Create new file**，檔名輸入 `.github/workflows/update-data.yml`，再把檔案內容貼上。
3. 到 **Settings → Actions → General**，最下方的 Workflow permissions 選 **Read and write permissions** 並儲存。
4. 到 **Actions** 分頁，點左邊的 `update-data`，再點 **Run workflow**，等 2～3 分鐘跑完（會產生 `data/` 資料夾）。
5. 到 **Settings → Pages**，Source 選 **Deploy from a branch**，Branch 選 `main`、資料夾選 `/ (root)`，然後儲存。
6. 大約 1 分鐘後，網址會是 `https://你的帳號.github.io/ma-scanner/`。

## 加到 iPhone 主畫面

用 Safari 打開上面的網址，點 **分享 → 加入主畫面**，之後就能像 App 一樣全螢幕使用。

## 自訂

修改 `config.json`：

| 欄位 | 說明 |
|---|---|
| `crypto_top_n` | 依成交額取前幾名幣種 |
| `crypto_extra` | 一定要掃的幣種，例如 `["PEPEUSDT"]` |
| `tw_top_n` | 依成交值取前幾名上市股 |
| `tw_extra` | 一定要掃的股票，上市寫 `"2330"`，上櫃要加 `.TWO`，例如 `"6488.TWO"` |
| `tw_names` | 補中文名稱（上櫃股用得到），例如 `{"6488": "環球晶"}` |

均線週期在 `index.html` 最上面的 `MA_LEN = [30, 45, 60]`。

## 備註

- GitHub 的排程可能會延遲幾分鐘到十幾分鐘，這是正常現象。
- repo 如果連續 60 天沒有活動，GitHub 可能會自動暫停排程，到 Actions 頁面重新啟用就可以。
- 只供參考，不構成投資建議。
