# 並行步驟的資料範圍

2026-09-24 修正 `ExecuteConcurrently()` 中，目前參數與匿名表格會被同群其他步驟覆寫的問題。適用於 RuntimeScenario，以及既有 ScenarioOutline 的並行執行入口；逐列 pytest Outline 仍採循序執行。

## callback 看到的資料

| 資料 | 行為 |
| --- | --- |
| `getArgs()`／`getArg()`／數字轉換方法 | 目前步驟自己的參數 |
| `table()`／`row()`／`lastRow()` | 自己明確指定的匿名表格；未指定時，繼承群組開始前的表格 |
| `get("$ARGUMENTS")`／`get("$ANONYMOUS_TABLE")` | 與專用 accessor 相同的步驟局部值 |
| `setArguments()`／`setAnonymousTable()`／對上述 reserved key 的 `put()` | 只更新目前步驟，群組完成後才合併 |
| `scenario.activeTable()`／`lookup_table`／`lookupTable` | 情境在目前步驟的 active table；由含表格的步驟描述設定 |
| 其他 `put()`／`get()` 值、Examples input、execution count | 保留原有情境共用行為 |
| `getHistoricalArgs()` | 完整歷史的讀取快照，同一並行群組內的順序不保證 |

callback 收到的 environment 與 `scenario.getEnvironment()` 仍為同一物件。框架透過 ContextVar 區分目前步驟，沒有為整個 callback 加鎖，因此同群步驟仍可真正並行。歷史引數的追加與快照讀取使用短暫鎖定。

## 群組結束與後續步驟

每個群組先取得相同的既有資料，再開始執行。群組中沒有表格的步驟，不會讀到其他同群步驟剛設定的表格。

所有 callback 完成後，局部修改依步驟宣告順序合併；最後明確設定的表格留給下一群組。沒有提供新表格的步驟不會把其他步驟的表格覆蓋回舊值。參數則沿用每次步驟開始時重新設定的規則；歷史不會在合併時重複追加。

無論 callback 成功、失敗或 Pending，都會在離開時清除執行緒的局部範圍。失敗策略仍在所有同群 callback 完成後判斷，必要時跳過後續群組。

## 仍由使用者管理的共享資料

一般 `env.put("key", value)` 依舊用來跨步驟交換資料；這不保證「先讀再加一再寫回」等複合操作具有原子性。需要時請自行使用 Lock、Event 或其他同步方式。

Background、使用者物件與繼承的表格仍採原有淺複製／參照語意，不會偷偷 deepcopy。隔離表格指派不代表直接修改同一個繼承 Table 的內容也受到隔離。框架建立的並行 worker 會套用步驟範圍；callback 自行建立的執行緒不會自動繼承該範圍。

`setAnonymousTable()` 管理 environment 的匿名表格；直接呼叫它不會額外改變 Scenario 的 active table，與既有循序 API 相同。由步驟描述建立的表格會同時設定兩者。

## 驗證

`tests/test_concurrent_environment.py` 使用 Barrier／Event 強制多個 callback 交錯，不依賴 sleep 或隨機排程碰到錯誤。測試涵蓋參數、表格、無表格步驟、Background、共用使用者值、setter、失敗處理與歷史引數。

本檔相關回歸共 10 項；完整測試套件在 Windows／Python 3.11.2、pytest 8.3.3 與 9.1.1 各通過 199 項，並將 RuntimeWarning 視為錯誤。
