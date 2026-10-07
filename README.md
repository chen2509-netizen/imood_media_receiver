# imood_media_receiver

- Updated Time: 261008_0540

imood 數位人 demo 的影像接收端。

前端 `imood_ai.html` 把影像來源指向這個服務後，就能透過它和 LiveTalking 建立 WebRTC 連線，取得數位人的影像和聲音。

## Requirements

- Linux 或 WSL2，Python 3.10，[uv](https://docs.astral.sh/uv/)
- LiveTalking 已經在執行（預設 `http://127.0.0.1:8010`）

## Quick Start

```bash
git clone https://github.com/chen2509-netizen/imood_media_receiver.git
cd imood_media_receiver
bash scripts/setup_env.sh   # 只需一次：建立 .venv、安裝套件
bash scripts/start.sh       # 啟動，預設 :8030
bash scripts/selftest.sh    # 檢查，最後一行應該是 "== 6 passed, 0 failed"
```

用瀏覽器開啟：

```
http://localhost:8010/imood/imood_ai.html?media=http://localhost:8030
```

然後按「開始視訊」。停止服務：`bash scripts/stop.sh`。

## Configuration

| 環境變數 | 預設值 | 說明 |
|---|---|---|
| `RECEIVER_PORT` | `8030` | 接收端的 port |
| `LT_URL` | `http://127.0.0.1:8010` | LiveTalking 的位址 |

例如：`RECEIVER_PORT=8031 bash scripts/start.sh`

## Documentation

- [docs/architecture.md](docs/architecture.md)：架構、分工、設計決策
- [docs/test_guide.md](docs/test_guide.md)：完整的啟動與測試步驟
- [docs/test_status.md](docs/test_status.md)：目前的測試狀態
