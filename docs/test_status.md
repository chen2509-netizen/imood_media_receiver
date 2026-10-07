# 測試現況

- Updated Time: 261008_0417

> **這份每次更新都直接覆蓋**，只放各項目的「目前」狀態。
> 每次測試的完整經過另外存在 `docs/logs/YYMMDD_HHMM_*.md`，下表的「log」欄連到最近一次的紀錄。
> 測試步驟見 [test_guide.md](test_guide.md)。

| 項目 | 狀態 | 最後測試 | 測試方式 | log | 備註 |
|---|---|---|---|---|---|
| 自動檢查（`scripts/selftest.sh`，6 項） | ✅ 通過 | 2026-10-08 | 腳本 | [261008_0331_test_record](logs/261008_0331_test_record.md) | CORS preflight、POST 帶 CORS header、錯誤回 `{code:-1, msg}` |
| 1. 連線、出畫面 | ✅ 通過 | 2026-10-08 | 無頭（aiortc） | [261008_0331_test_record](logs/261008_0331_test_record.md) | offer 約 5.3 s |
| 2. fps ≈ 25 | ✅ 通過 | 2026-10-08 | 無頭（aiortc） | [261008_0331_test_record](logs/261008_0331_test_record.md) | 平均 24.4 fps |
| 3. 對嘴（sessionid 正確） | ❌ 未完成 | 2026-10-08 | 無頭（aiortc） | [261008_0331_test_record](logs/261008_0331_test_record.md) | llama-server :8090 沒有啟動，卡在 LLM。聲音、音畫同步、嘴型都還沒驗證 |
| 4. 斷線清理 | ✅ 通過 | 2026-10-08 | 無頭（aiortc） | [261008_0331_test_record](logs/261008_0331_test_record.md) | 關閉後 3 秒內 session 已刪除 |
| 真實瀏覽器（1–4 項） | ⏳ 未測 | — | 使用者操作 | — | 照 [test_guide.md](test_guide.md) 第 5 節 |
| 換角色重連 | ⏳ 未測 | — | — | — | test_guide 第 5 節選做項目 |

## 下一步

1. 確認 VRAM：:8000、:8001 的服務要先停掉，怎麼停請問 A。然後啟動 llama-server :8090。
2. 重跑第 3 項，結果另存為 `docs/logs/YYMMDD_HHMM_test_item3_rerun.md`，再更新本表。
   - 要回報三件事：有沒有收到聲音、音畫是否同步、嘴型有沒有動。
3. 使用者用真的瀏覽器跑一輪，結果同樣另存 log，再更新本表。
