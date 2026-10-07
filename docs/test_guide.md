# 操作測試步驟（由使用者本人在這台機器操作）

- Updated Time: 261008_0456

> 目的：用真的瀏覽器，透過接收端 :8030 跑完前端文件的四項自我測試。
> 依據：前端 repo 的啟動腳本（`cyber_gf/scripts/`）、`cyber_gf/README.md`，以及 261008 實測。

## 0. 先知道這些

**所有指令都在 Windows 的 PowerShell 裡下。**
- WSL 的指令一律加上 `wsl -d Ubuntu-24.04 --` 前綴，不用另外開 WSL 終端機。
- 這台的**預設 distro 是 22.04**，所以一定要寫 `-d Ubuntu-24.04`。22.04 裡沒有這些服務。
- PowerShell 5.1 的 `curl` 是 `Invoke-WebRequest` 的別名，所以下面一律寫 **`curl.exe`**。

**每開一個新的 PowerShell 視窗，先執行下面兩行。** 變數只在這個視窗裡有效。
```powershell
$CYBER_GF = "<前端 cyber_gf repo 在 Windows 的路徑>"   # 本機的實際路徑見 docs/local_records/local_paths.md（不上傳）
$CYBER_GF_WSL = wsl -d Ubuntu-24.04 -- wslpath -a ($CYBER_GF -replace '\\','/')
```
- `$CYBER_GF`：前端 repo 在 Windows 的路徑。
- `$CYBER_GF_WSL`：同一個資料夾在 WSL 裡的路徑。

下面的指令都會用到這兩個變數。

| 服務 | port | 在哪裡跑 | 負責 | 啟動方式 |
|---|---|---|---|---|
| llama-server（LLM） | 8090 | Windows | A | `cyber_gf\scripts\windows\start_llama.bat`（會開一個新視窗，不要關） |
| LiveTalking + adapter + 前端頁面 | 8010 | WSL 24.04 | C（啟動腳本是 A 的） | `cyber_gf/scripts/wsl/start_step12_v2.sh` |
| 語音服務 | 8020 | WSL 24.04 | A | 跟 LiveTalking 同一支腳本 |
| 接收端 | 8030 | WSL 24.04 | B（我們） | `/root/imood_rtp/scripts/start.sh` |

**啟動順序：** ① 檢查 VRAM → ② llama-server → ③ LiveTalking 和語音服務 → ④ 接收端 → ⑤ 瀏覽器。

---

## 1. 檢查 VRAM（PowerShell）

```powershell
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
```

- 整套大約需要 23.3 / 24 GB，其中 llama-server 約 10 GB，LiveTalking 加語音服務約 9–11 GB。
- 261008 查到的狀態：LiveTalking 和語音服務已經在跑，GPU 用了 14.6 GB。:8000 另外有一個 python 服務在跑。
  - 這時再啟動 llama-server，**很可能超過 24 GB**。
- 前端 README 說：「:8000、:8001 的舊服務要先停掉」。但我查不到 :8000 是什麼服務（pid 6108，權限不足），
  **怎麼停請問 A，我不猜。**
- **判斷：** 啟動 llama-server 之前，used 最好在 14 GB 以下，而且 :8000、:8001 已經停掉。

---

## 2. 啟動 llama-server :8090（Windows）

```powershell
& "$CYBER_GF\scripts\windows\start_llama.bat"
```

- 也可以在檔案總管直接雙擊這個 `.bat`。
- 它會占住目前的視窗，所以請另外開一個 PowerShell，或用雙擊的方式。
- 模型載入要十幾秒到一分鐘。

**確認有起來：**
```powershell
curl.exe -s http://localhost:8090/health
```
- ✅ 成功：輸出含有 `"ok"`。
- ❌ 失敗：看 llama-server 那個視窗的錯誤訊息。常見原因是 VRAM 不夠，訊息會有 out of memory。

---

## 3. LiveTalking :8010 和語音服務 :8020（WSL）

**先檢查是不是已經在跑：**
```powershell
curl.exe -s http://localhost:8010/cyber_gf/stats
curl.exe -s http://localhost:8020/api/health
```
- 第一行含 `"code": 0`，第二行含 `"ok": true`：**兩個都已經在跑，直接跳到第 4 步。**
- 有任何一個沒回應，就啟動：

```powershell
wsl -d Ubuntu-24.04 -- bash "$CYBER_GF_WSL/scripts/wsl/start_step12_v2.sh"
```
- ⚠️ 這支腳本會**先停掉**已經在跑的 LiveTalking 和語音服務，再重新啟動。
- 第一次啟動要載入所有模型，大約 20–30 秒，最多等 4 分鐘。
- ✅ 成功：最後印出 `LiveTalking+adapter: OK` 和 `voice service: OK`。
- ❌ 失敗：印出 `NOT READY`，看後面寫的 log 路徑（見第 8 節）。

> 另一個選擇：`cyber_gf\scripts\windows\start_step12_v2.bat` 會一次啟動第 2、3 步，
> 但最後會打開**舊的** debug 頁面，不是新前端。

---

## 4. 接收端 :8030（WSL）

```powershell
wsl -d Ubuntu-24.04 -- bash /root/imood_rtp/scripts/start.sh
wsl -d Ubuntu-24.04 -- bash /root/imood_rtp/scripts/selftest.sh
```
- ✅ start 成功：印出 `receiver up on :8030 (pid …)`。如果已經在跑，會印出 `already running`，這樣也算正常。
- ✅ selftest 成功：最後一行是 `== 6 passed, 0 failed`。
  - 同一段輸出的 `INFO LiveTalking live sessions: [...]` 列出目前存活的 session，**記下來**，第 4 項測試要拿來比對。
- ❌ 失敗：看 `/root/imood_rtp/logs/receiver.log`（見第 8 節）。

> 如果在 Windows 端改過接收端的程式，要先 commit、push，再在 WSL 更新並重啟：
> `wsl -d Ubuntu-24.04 -- bash -c "cd /root/imood_rtp && git pull && bash scripts/stop.sh && bash scripts/start.sh"`

---

## 5. 瀏覽器測試

用 Chrome 或 Edge 開：

**http://localhost:8010/imood/imood_ai.html?media=http://localhost:8030**

- 一定要用 `localhost`。用 IP 開的話，瀏覽器不給麥克風權限。
- 網址的 `?media=` 優先於 ⚙ 設定裡存的值。

### 測試 1：連線、出畫面

1. 畫面中間的角色按鈕選 **「白上衣 WA3（一次快眨）」**。
   - 它是清單第一個，通常已經是預設選取（黑底），也就是伺服器預設的角色。
2. 按下方綠色的 **「開始視訊」**。
3. 預期看到：
   - 右上角的狀態變成黃燈「連線中…」。
   - **大約 5 秒後**，變成綠燈「**視訊中**」，左上角出現紅色 **LIVE**，數字人畫面出現，會有閒置的眨眼動作。
   - 按鈕變成紅色的「結束視訊」。
4. **確認真的有經過接收端：** 按右上角的**波形圖示**（⚙ 左邊那個，「診斷資訊」）→「紀錄」分頁。
   - 應該有一行 `connecting via http://localhost:8030…`。
   - 還有一行 `connected, session <id>`。**記下這個 id。**
5. ❌ 失敗的情況：
   - 狀態顯示「連線失敗」：輸入框下方會顯示原因（這是接收端回傳的 `msg`），看第 8 節。
   - 一直停在「連線中…」：看 F12 → Console。

### 測試 2：fps 大約 25

1. 在「診斷資訊」裡切到「**WebRTC 接收**」分頁。
2. 預期：「影像 fps（解碼）」**大約 25**，每秒更新一次；「影像掉幀」維持在很小的數字。
3. ❌ 長時間低於 20：記下「影像凍結次數」和「jitter buffer ms」。
   - 前端 README 提到：用遠端桌面看畫面可能會卡，但錄影其實是順的。

### 測試 3：對嘴（這一項重點要回報三件事）

**做法 A：上傳檔案（結果可以重現，建議先做這個）**
1. 右側對話區左下角，按「**上傳 WAV**」。
   - 選前端 repo 裡的 `assets\test.wav`（也就是 `$CYBER_GF\assets\test.wav`）。
   - 檔案內容是一句話：「你今天過得怎麼樣？有沒有什麼有趣的事情？」
2. 按右下角的「**送出檔案**」。

**做法 B：用麥克風說話**
1. 按中間圓形的**麥克風**按鈕。第一次會跳出權限要求，選「允許」。
2. 用**中文**說一句話，例如「你今天過得怎麼樣？」。語音辨識設定的是中文（`voice.json` 的 `language: zh`）。
3. 再按一次麥克風，就會送出。錄音少於 0.5 秒會被丟掉。
4. 建議戴耳機，避免數字人的聲音又被麥克風收進去。

**預期看到：**
- 對話泡泡的狀態依序是：排隊中 → 聽寫中 → 思考中 → 準備開口 → 說話中 → 完成。
- 你的泡泡顯示辨識出的文字，對方的泡泡顯示 LLM 的回覆。回覆每次都不一樣。
- 數字人泡泡下方會出現「**x.xx 秒開口**」。參考機實測大約 3 秒。

**請回報這三件事：**

| 要回報的 | 怎麼判斷 |
|---|---|
| ① 有沒有收到聲音 | 喇叭或耳機聽得到數字人的聲音（複製的聲音）。也可以看「WebRTC 接收」分頁，「聲音補償樣本」在說話時不應該一直暴增 |
| ② 音畫是否同步 | 聲音和嘴型同時開始、同時結束，沒有明顯的先後差 |
| ③ 嘴型有沒有動 | 說話時嘴巴跟著音節開合，說完就回到閉嘴的閒置狀態 |

另外請記下：「延遲」分頁的「數字人開始說話」秒數，以及「欠載 underruns / 幀」。

**❌ 失敗時：**
- 狀態停在「思考中」或變成「錯誤」：通常是 llama-server 沒起來，回到第 2 步。
- 文字回覆出來了，但數字人沒開口：sessionid 或 LiveTalking 有問題，看 LiveTalking 的 log。
- 畫面有動但聽不到聲音：檢查瀏覽器分頁是不是被靜音，以及系統音量。

### 測試 4：斷線清理

1. 按紅色的「**結束視訊**」。狀態回到「尚未連線」。
2. 等 3 秒，在 PowerShell 執行：
   ```powershell
   curl.exe -s http://localhost:8010/cyber_gf/stats
   ```
3. ✅ 成功：輸出最前面 `"sessions": [...]` 裡**沒有**測試 1 記下的那個 id。
   - 注意：後面的 `recent_utts` 是歷史紀錄，裡面出現這個 id 是正常的，不用管。

### （選做）換角色

選另一個角色，例如「黑上衣 BA3」。視訊中切換角色會自動先斷線再重連。
預期幾秒後出現新角色，而且「紀錄」分頁的 session id 變成新的。

---

## 6. 結果回報格式（貼給我）

```
測試1 連線：OK/NG  session=<id>  連上花了約 _ 秒
測試2 fps：約 __  掉幀 __
測試3 對嘴：①聲音 有/無 ②同步 是/否（描述）③嘴型 有動/沒動   開口 _._ 秒  underruns _/_
測試4 清理：OK/NG
其他觀察：
```

---

## 7. 停止

```powershell
# 只停接收端（我們的）
wsl -d Ubuntu-24.04 -- bash /root/imood_rtp/scripts/stop.sh
```

如果要把整套都關掉（會停掉 A 的語音服務、llama-server，以及 LiveTalking）：
```powershell
& "$CYBER_GF\scripts\windows\stop_step12_v2.bat"
```

---

## 8. 失敗時看哪個 log

| 服務 | log 位置 | 怎麼看（PowerShell） |
|---|---|---|
| 接收端 :8030 | `/root/imood_rtp/logs/receiver.log` | `wsl -d Ubuntu-24.04 -- tail -n 30 /root/imood_rtp/logs/receiver.log` |
| LiveTalking :8010 | `/root/lt_logs/lt_cyber_gf.log` | `wsl -d Ubuntu-24.04 -- tail -n 50 /root/lt_logs/lt_cyber_gf.log` |
| 語音服務 :8020 | 前端 repo 的 `logs\voice_service.log` | `Get-Content "$CYBER_GF\logs\voice_service.log" -Tail 30` |
| llama-server :8090 | 沒有檔案，看它自己的視窗 | — |
| 瀏覽器 | 「診斷資訊」→「紀錄」分頁，以及 F12 → Console | — |

接收端 log 的正常樣子：
```
INFO receiver: offer avatar=wav2lip256_avatar3_WA3 -> sessionid=<id> (5.31 s)
```
- 這裡的 id 應該跟瀏覽器「紀錄」分頁顯示的一樣。
- 如果是 `WARNING ... failed: LiveTalking unreachable`，代表 :8010 沒起來。
- 如果是 `refused by LiveTalking: Maximum session limit reached`，代表 session 數到了上限（5 個）。可以關掉其他分頁，或等斷線的 session 被清掉。

---

## 9. 設定被存起來的陷阱

- 如果曾經在 ⚙ 設定裡填過「影像來源」，這個值會存在瀏覽器裡，下次開頁面還在。
- 想改回直接連 LiveTalking：把那一欄清空，再按「套用」。
- 網址上的 `?media=` 永遠優先於存起來的設定。
