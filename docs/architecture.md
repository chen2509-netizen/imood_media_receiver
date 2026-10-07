# 現有架構與分工

- Updated Time: 261008_0446

> 依 2026-10-08 實際讀取程式碼與執行中服務整理（唯讀調查，未修改任何既有檔案）。
> RTP 方案已放棄：上游 LiveTalking 只輸出 WebRTC，接收端照它的方式接 WebRTC。
> 標「待確認」的地方是推測，請找對應同事確認。

---

## 1. 分工

| 代號 | 負責 | 內容 | 位置 |
|---|---|---|---|
| **A** | 前端同事 | 網頁前端。瀏覽器是**最終的 WebRTC 接收方**（收影像＋聲音、顯示、算 debug 統計） | 前端 `cyber_gf` repo 的 `web/imood_ai.html`，由 :8010 提供 `/imood/imood_ai.html` |
| **B** | 我們 | **中間接收端（WebRTC）** :8030：接瀏覽器的 `/offer`，向 LiveTalking 取得影像＋聲音和 sessionid，再送給瀏覽器 | `/root/imood_rtp/`（Windows 端副本：`C:\imood_project\temp_mem2\imood_rtp\`） |
| **C** | 模型同事 | **LiveTalking + Wav2Lip** :8010：取代 JoyGen，產生數字人說話影像＋聲音，輸出 WebRTC | `/root/livetalking/LiveTalking`（`.venv-lt`），角色在 `data/avatars/wav2lip256_avatar2_*`、`avatar3_*` |
| **A** | 前端同事 | 語音服務 :8020（ASR → LLM → TTS → 把聲音推給 LiveTalking） | `cyber_gf/scripts/wsl/voice_service.py`（`/root/cyber_gf/.venv-tts-fast`） |
| **A** | 前端同事 | LLM：llama-server :8090（Qwen3-14B） | Windows 端 |

技術補充（對分工表的修正）：
- C 的 :8010 不是直接跑 LiveTalking 的 `app.py`，而是用 `cyber_gf/scripts/wsl/livetalking_cyber_gf.py` 啟動。
  它在**未修改的** LiveTalking 外面加了幾個路由：`/cyber_gf/audio_stream`、`/cyber_gf/stats`，以及靜態頁 `/imood/`、`/cyber_gf/web/`。
  這支啟動程式放在前端 repo 裡。
- A 的「WebRTC 接收」指的是瀏覽器本身。B 對 A 來說是 WebRTC **送出方**，對 C 來說是 WebRTC **接收方**。

---

## 2. 架構圖

### 加入 B 之後（目標）

```
┌──────────── A：瀏覽器 imood_ai.html（從 :8010/imood/ 開啟）────────────┐
│ <video>/<audio> 播放；⚡診斷用 pc.getStats() 自己算 fps/掉幀/jitter      │
└──┬───────────────────────┬──────────────────────────┬──────────────────┘
   │① POST {media}/offer    │② POST {voice}/api/ask    │③ GET /sse, POST /record
   │  ◄══ WebRTC 影像+聲音   │   ?sessionid=…           │   ?sessionid=…
   ▼                        ▼                          │
┌───────────────┐    ┌──────────────────┐            │
│ B：接收端 :8030│    │ 語音服務 :8020    │            │
│ (WebRTC 中繼)  │    │ ASR→LLM(:8090)→TTS│            │
└──────┬────────┘    └────────┬─────────┘            │
       │ POST /offer           │ POST /cyber_gf/audio_stream?sessionid=…
       │ ◄══ WebRTC 影像+聲音    │ （TTS 聲音，16 kHz）     │
       ▼                       ▼                         ▼
┌──────────────────────── C：LiveTalking + Wav2Lip :8010 ────────────────────────┐
│ session_manager：每個 sessionid 一個數字人 session（聲音 → 嘴型 → 影像＋聲音） │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 現在（沒有 B，`media` 留空）

①直接打 :8010 的 `/offer`，瀏覽器跟 LiveTalking 直接建 WebRTC。②③不變。
B 加入後**只換掉①**，②③完全不動。

---

## 3. 一次對話的流程（sessionid 怎麼串起來）

1. A 按「開始視訊」，送出 `POST {media}/offer`，內容是 `{sdp, type, avatar}`。
2. C 的 `session_manager.create_session(params)` 建立 session，用 `avatar` 選角色，產生 uuid 當 `sessionid`。
   C 回傳 `{sdp, type:"answer", sessionid}`，並開始送 WebRTC：閒置時是 idle 畫面，說話時是對嘴畫面。
3. A 錄音或上傳 WAV，送出 `POST :8020/api/ask?sessionid=…`。
   語音服務做 ASR → LLM → TTS，把聲音串流到 `:8010/cyber_gf/audio_stream?sessionid=…`。
   C 用這段聲音驅動**同一個 session** 的嘴型，所以 WebRTC 那條畫面就開始說話。
4. A 用 `/sse?sessionid=` 收播放事件，`/record` 錄影。
5. A 按「結束視訊」，只做 `pc.close()`。
   C 在自己那條 peer connection 變成 `closed` 或 `failed` 時，呼叫 `remove_session(sessionid)`
   （見 `server/rtc_manager.py` 的 `on_connectionstatechange`）。

**結論：** sessionid 由 C 產生，而且綁定「C 送出的那一條 WebRTC」。
B 必須把 C 回傳的 sessionid 原封不動交給 A，而且送給 A 的影像必須來自同一條連線。

---

## 4. B（接收端）要做的事

前端規格見前端 repo 的 `cyber_gf/docs/frontend_v2_interface.md`（本機副本：`docs/local_records/frontend_v2_interface_1003.md`，不上傳）。

| 項目 | 內容 |
|---|---|
| 介面 | 只有 `POST /offer`（另有 `OPTIONS /offer` 給 CORS），預設 :8030 |
| 輸入 | `{sdp, type:"offer", avatar?}`。瀏覽器是 recvonly，先 video 後 audio |
| 輸出 | 成功回 `{sdp, type:"answer", sessionid}`；失敗回 `{code:-1, msg}`，不帶 `sdp` |
| sessionid | 直接用 C 回傳的值 |
| 影像＋聲音 | 從 C 收到的 video、audio 兩條 track 轉送給 A，不另外重新對時 |
| CORS | `OPTIONS` 回 204，`POST` 回應帶 `Access-Control-Allow-Origin: *` |
| ICE | non-trickle，answer 裡直接帶 candidate（aiortc 預設就是這樣） |
| 斷線 | 做法 1：WebRTC 是 A 直連 C，A 一關閉連線，C 就會自己刪 session，B 不用處理。做法 2：A 那條連線變 `closed`/`failed` 時，B 關掉 B→C 那條，C 就會自己刪 session |
| debug | 不需要提供。A 用 getStats 自己算 |

### 實作做法（261008 決定：先用做法 1）

「向 LiveTalking 協商」寫成獨立函式，`/offer` 對前端的介面固定不變。
之後如果需要浮水印、錄影，或雲端網路要求影像必須經過 B，再升級成做法 2，前端不用改。

| 做法 | 說明 | 優缺點 |
|---|---|---|
| 1. 只轉發協商 | B 把 offer 原樣轉給 C，再把 answer 傳回 A。影像直接從 C 送到 A，不經過 B | 最簡單、零延遲；但 B 碰不到影像，只是 CORS proxy |
| 2. WebRTC 中繼 | B 用 aiortc 當 C 的客戶端，收到 track 後再送給 A | 影像確實經過 B，之後可以加功能；但 aiortc 會解碼再重新編碼，延遲增加約 20–60 ms，並多佔 CPU |

---

## 5. 備註：之後上雲端 A100

目前不實作。上雲端時要注意：
- **UDP、STUN、TURN：** 做法 1 是瀏覽器直接連 LiveTalking 的隨機 UDP port。
  - 預計走「防火牆開放 UDP」或 localhost 這種最少阻礙的方式。
  - 如果平台只開放 TCP，需要 TURN，或升級成做法 2。
- **HTTPS：** 不是 localhost 的話，瀏覽器麥克風需要 HTTPS。

## 6. 環境事實（261008 查證）

| 項目 | 內容 |
|---|---|
| 執行中 | :8010（pid 107124，`livetalking_cyber_gf.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar3_WA3`）、:8020。:8030 尚未佔用 |
| LiveTalking | commit `b3e7490`，`max_session` = 5，Python 3.10.21，aiortc 1.15.0，aiohttp 3.14.3，av 17.1.0 |
| 其他端點 | C 另有 `/whep`（WHEP 協定）和 `/cyber_gf/stats`（列出存活的 sessions，自我測試第 4 項會用到） |
| 角色清單 | `cyber_gf/web/avatars.json`：WA3（預設）、BA3、WA2、BA2、mA1、mB2 |
| 工具 | 24.04 的 `uv` 0.12.19 是獨立安裝在 `/root/.local/bin`，不在 conda base；既有 venv 全是用 uv 建的（`.venv-lt` 用 uv 管理的 CPython 3.10.21） |
| 不相關 | `/root/imood_like_poc`（9/23 的安裝腳本，模型和素材資料夾是空的）；22.04 的 JoyGen RTP 工作（已被 LiveTalking 取代） |

---

## 7. 相關文件

| 文件 | 內容 |
|---|---|
| [test_guide.md](test_guide.md) | 使用者自己操作的測試步驟：啟動順序、瀏覽器操作、預期結果、log 位置 |
| [test_status.md](test_status.md) | 各測試項目的目前狀態、最後測試日期，以及對應的 log |
| [logs/](logs/) | 歷史紀錄（`YYMMDD_HHMM_*.md`），例如開發總結、每次的測試紀錄 |
