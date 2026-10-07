# imood_rtp — 接收端（B）

- Updated Time: 261008_0457

瀏覽器前端（A）和 LiveTalking（C）之間的接收端，預設 :8030。
- 對前端只提供 `POST /offer`。
- 另外有 `OPTIONS /offer`（CORS preflight）和 `GET /health`（`scripts/start.sh` 用來確認接收端已啟動）。

架構和分工見 `docs/architecture.md`，前端介面規格見前端 repo 的 `cyber_gf/docs/frontend_v2_interface.md`（本機副本：`docs/local_records/frontend_v2_interface_1003.md`，不上傳）。

## 權限規則

**可以修改：** 只有本專案資料夾。
- WSL：`/root/imood_rtp/`
- Windows：`C:\imood_project\temp_mem2\imood_rtp\`

**唯讀（可以讀、可以呼叫它們的 HTTP API，但絕不修改、不安裝套件、不重啟服務）：**
- `/root/livetalking/`
- `/root/cyber_gf/`
- `/root/imood_like_poc/`
- `/root/CosyVoice/`
- `/root/lt_weights/`
- Windows 端的前端 `cyber_gf` repo（本機的實際路徑見 `docs/local_records/local_paths.md`，不上傳）

**Python 環境：**
- 套件只裝進專案自己的 `.venv`（`uv venv --python 3.10`，跟 `.venv-lt` 一樣用 uv）。
- 絕不動 conda base、系統 Python，或其他專案的 env（`.venv-lt`、`.venv-tts-*`、`cosyvoice*`、`imood-*`）。

## 程式碼同步（以 git 為準）

- **原始碼以 git 為準。**
  - 在 Windows 修改、commit、push。
  - WSL 的 `/root/imood_rtp/` 只用 `git pull` 更新。
- 不要直接在 WSL 端改程式，否則 `git pull` 會衝突。
- **WSL 端第一次設定**（只需要做一次）：
  - 現有資料夾直接變成 git 工作目錄，不用刪檔案。
  - `.venv/`、`logs/`、`docs/local_records/` 都在 `.gitignore` 裡，git 不會動到。
  ```bash
  cd /root/imood_rtp
  bash scripts/stop.sh
  git init
  git remote add origin <repo URL>
  git fetch origin
  git checkout -f -B main origin/main
  git status                                # 應該是 clean
  bash scripts/start.sh
  ```
- **之後每次更新：** `cd /root/imood_rtp && git pull`。
  - 改到 `receiver/` 的話，再執行 `bash scripts/stop.sh && bash scripts/start.sh` 重啟接收端。

## 文件規則

**放置規則：**
- **確定版**放 `docs/`。
- **歷史紀錄**放 `docs/logs/`。
- **暫存**放 `docs/local_records/`。

```
docs/
  architecture.md       ← 確定版（上傳）：架構與分工
  test_guide.md         ← 確定版（上傳）：使用者自己操作的測試步驟
  test_status.md        ← 確定版（上傳）：各測試項目的目前狀態，每次更新直接覆蓋
  logs/                 ← 歷史紀錄（上傳）：YYMMDD_HHMM_<英文名>.md，原則上寫完不改（例外見下）
  local_records/        ← 暫存（不上傳，.gitignore）：草稿、別人給的檔案
```

- **檔名一律用英文**（例如 `architecture.md`、`test_status.md`、`test_guide.md`），內容維持中文。
- **`docs/logs/` 的例外：**原則上不改內容，只有下面三種情況可以改，改了要更新 Updated Time，檔名維持不變。
  - 修正檔案引用（例如改名後的路徑）。
  - 去除個人資訊。
  - 使用者要求的修正。
- **每份文件**的標題下一行都要有 `- Updated Time: YYMMDD_HHMM`，改內容時一起更新。
- **每次測試**都另存一份新的 log（例如 `YYMMDD_HHMM_test_item3_rerun.md`），然後覆蓋更新 `test_status.md` 的狀態、日期和 log 連結。
- **改名或搬移檔案時**，要用 grep 找出所有引用一起更新。
- **上傳的文件**不要把 `docs/local_records/` 裡的檔案當作唯一來源。
  - 前端規格請引用前端 repo 的 `cyber_gf/docs/frontend_v2_interface.md`。
- **repo 會公開**：上傳的檔案裡不要寫含使用者名稱的路徑（例如 `C:\Users\<名字>\...`）。
  - 前端 repo 的路徑用 `$CYBER_GF`／`$CYBER_GF_WSL`，或寫「前端 `cyber_gf` repo」。
  - 實際路徑記在 `docs/local_records/local_paths.md`。
  - `/root/...` 不帶個人資訊，可以照寫。
- **兩個 `logs/` 不同：**專案根目錄的 `logs/` 是接收端執行時的 log（`receiver.log`），跟 `docs/logs/` 無關。

## 常用指令（在 WSL 的 `/root/imood_rtp` 執行）

```bash
bash scripts/setup_env.sh   # 建 .venv、安裝 aiohttp（只需一次）
bash scripts/start.sh       # 背景啟動 :8030，log 寫在 logs/receiver.log
bash scripts/stop.sh
bash scripts/selftest.sh    # 自動檢查 CORS、錯誤回應，以及 LiveTalking 的 session 數
```

## 設計重點

- 目前用**做法 1：只轉發協商**。WebRTC 媒體是瀏覽器直連 LiveTalking。
- 向 LiveTalking 協商的程式集中在 `receiver/server.py` 的 `negotiate_with_livetalking()`。
  - 之後升級成做法 2（WebRTC 中繼）時，只換這個函式。`/offer` 對前端的介面不變。
- `sessionid` 一律直接用 LiveTalking 回傳的值。
