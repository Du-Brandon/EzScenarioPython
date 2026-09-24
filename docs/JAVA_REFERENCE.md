# Java ezSpec 參考分析與 Python 需求對照

日期：2026-09-23。
參考來源：相鄰目錄 `../ezspec-java-reference`，HEAD 為 `061eadc8dd47510bf12d62dd87d3fdaa0a37b20d`。
閱讀範圍包括 core／report 的 README、ScenarioOutline、RuntimeScenario、JUnit annotations、相關測試、TXT／JSON 報告實作、範例與動態測試樹截圖。
本次僅閱讀與整理文件，沒有修改 Java 或 Python 執行器，也沒有執行 Java 測試。

## 已確認需求

| 主題 | 使用者確認的方向 |
| --- | --- |
| 產品目標 | 像 ezSpec 一樣方便閱讀測試內容與結果 |
| Outline 執行單位 | 每列資料是獨立 pytest 測試，可各自顯示、篩選、重跑 |
| 缺少測試資料 | 依最新更正按照 Java：未提供 Examples 時不執行、不報錯；明確傳入空 Examples 集合仍保留原有參數檢查 |
| Pending | 尚未確認如何對應 pytest 狀態；與缺資料分開處理 |

以下把 Java 現況、Python 現況和推導出的設計建議分開記錄。
後續具體方案見 [Outline 逐列測試設計](PYTEST_OUTLINE_DESIGN.md)，其中 decorator 宣告 Examples 的 API 方向已獲使用者接受。

## Java 如何讓使用者看懂測試

### 1. 可讀的名稱與規格文字

`@EzFeature` 使用 `DisplayNameGenerator.ReplaceUnderscores`，讓方法名稱中的底線顯示為空白。
Feature／Rule／Scenario／Steps 本身保留文字描述，使用者不需要從 callback 的程式碼還原測試意圖。

來源：`ezspec-core/src/main/java/tw/teddysoft/ezspec/EzFeature.java:12`。

### 2. IDE 中的逐步測試樹

一般 `@EzScenarioOutline` 是 JUnit `@Test`；`@EzDynamicScenarioOutline` 則是 `@TestFactory`。
因此 Java 也區分「一個方法完成所有資料列」與「回傳動態測試樹」兩種入口。

`RuntimeScenario.DynamicExecute()` 建立 Scenario container；`dynamicExecuteImpl()` 為每個 Step 建立 DynamicTest。
名稱包含狀態、關鍵字和描述，例如 `[Success] Given a successful given`。

`ScenarioOutline.DynamicExecute()` 再為每一列建立 container，名稱包含一開始為 1 的列序號和該列輸入表格；每列之下接各步驟節點。
這提供「情境 → 資料列 → 步驟／結果」的閱讀層次。

來源：

- `ezspec-core/src/main/java/tw/teddysoft/ezspec/keyword/RuntimeScenario.java:191, 200`
- `ezspec-core/src/main/java/tw/teddysoft/ezspec/keyword/ScenarioOutline.java:194`
- `ezspec-core/src/main/java/tw/teddysoft/ezspec/extension/junit5/EzDynamicScenarioOutline.java`
- `ezspec-core/img/dynamicScenarioReportExample.png`（已檢視）

截圖中的 Pending／Skipped 名稱前仍可見綠色勾號。
由 `Scenario.dynamicExecuteStep()` 可確認：Pending 與 Skipped 直接 return，只有 Failure 重新拋出原始例外。
因此文字狀態與 JUnit 的成功／失敗指示並不完全相同。

來源：`ezspec-core/src/main/java/tw/teddysoft/ezspec/keyword/Scenario.java:468`。

### 3. 執行後的 living documentation

`PlainTextReport` 依序輸出 Outline 模板、原始 Examples、每列替換後的步驟及狀態。
逐列標題使用列序號，以及資料中可選的 `example_code`；錯誤訊息接在失敗步驟後面。
語系機制可將關鍵字顯示為「功能／背景／場景／假如／當／那麼」等文字。

JSON 的 `ScenarioOutlineDto` 同時保留 `rawStepDtos`、`allExampleDtos` 和 `runtimeScenarioDtos`，可支援模板與執行結果的不同檢視。
報告 extension 在 JUnit `afterAll` 階段讀取 class 的 `feature` 欄位並輸出檔案。

來源：

- `ezspec-report/src/main/java/tw/teddysoft/ezspec/visitor/PlainTextReport.java:57, 82, 92`
- `ezspec-report/src/main/java/tw/teddysoft/ezspec/report/ScenarioOutlineDto.java:8`
- `ezspec-report/src/main/java/tw/teddysoft/ezspec/extension/junit5/EzSpecReportExtension.java:73`
- `ezspec-report/src/test/resources/ezSpec-report/tw.teddysoft.ezspec.LanguageTwReportSpec.txt`

## 缺少資料：依最新更正按照 Java

Java 的 `WithExamples(List)` 會拒絕空集合，錯誤為 `require at least an example`。
但如果完全沒呼叫 WithExamples，`runtimeScenarios` 為空，Execute 的迴圈不會執行，最後也不會拋出錯誤。
Java 測試 `scenario_outline_without_examples_should_not_execute` 明確斷言 callback 執行次數為 0。

來源：

- `ezspec-core/src/main/java/tw/teddysoft/ezspec/keyword/ScenarioOutline.java:135, 457`
- `ezspec-core/src/test/java/tw/teddysoft/ezspec/ScenarioOutlineSpec.java:57`

目前 Python 的 no-op 與 Java 原有行為一致。使用者最新更正為「按照 Java」，取代先前要求一律對缺資料報錯的決定。

後續維護應保留以下差別：

- 完全沒呼叫 WithExamples：沒有 runtime scenarios，不執行 callback，也不額外報錯。
- 明確呼叫 WithExamples 並傳入空集合：保留 `require at least an example` 的參數檢查錯誤。
- 可解析但只有表頭、沒有資料列的表格：不新增「至少一列」的檢查，依 Java 的零次執行語意處理。
- Execute、DynamicExecute、ExecuteConcurrently 與未來的 pytest 整合不得擅自新增缺資料失敗規則。

每列資料可獨立顯示、篩選、重跑的需求仍然有效。零資料列如何呈現在 pytest 中，需在整合時處理，不能因此重新引入已撤回的缺資料報錯規則。

## 逐列 pytest 測試的架構重點

Python 現況：Outline 的 WithExamples 寫在測試方法內，而 `Execute()` 在該方法執行時才跑完所有列。
`DynamicExecute()` 目前只是呼叫 Execute 並回傳物件，沒有建立逐列 pytest items。

Java 的實作有一點需要特別注意：`dynamicExecuteImpl()` 先呼叫 `preExecuteScenario()` 執行 callbacks，再建立帶結果文字的 DynamicTest。
後面的 DynamicTest 只檢查保存的 Result，並不重新執行 callbacks。

這是 Java 的實作方式。若要讓 Python 每列都能真正獨立選取和重跑，不能在 pytest 收集階段就執行全部列，再事後顯示結果。

建議的分工：

1. **規格與資料宣告**：先取得 Outline 模板及 Examples，不執行 Given／When／Then callbacks。
2. **pytest 收集**：每列建立穩定、唯一的 item／node id，讓篩選在執行前生效；未提供 Examples 時保留 Java 不執行、不報錯的語意。
3. **逐列執行**：只有被選取的列執行 callbacks，各列具有清楚的 environment 生命週期，並保留 fixture 的正確使用時機。
4. **結果呈現**：顯示 Outline 名稱、列識別、實際參數與步驟結果；報告從同一份結果模型產生。

範例顯示方向：

```text
計算含稅金額 [TC01, price=100, rate=0.05]
  [Success] Given 未稅金額為 100
  [Success] When 稅率為 0.05
  [Success] Then 含稅金額為 105
```

建議優先沿用可讀的 `example_code` 作為列標籤，沒有時以列序號與精簡參數辨識；重複代碼仍需確保 node id 唯一。
這是呈現設計建議，尚未決定或實作 API。
目前保留「每列一個可重跑單位」，步驟細節作為該列的執行資訊；不把共用 scenario 狀態的每個步驟直接當成可任意獨立執行的測試。

後續測試應驗證：collect-only 不執行 callbacks；選取一列只執行該列；一列失敗不妨礙其他被選取列；fixture／parametrize 能正確使用；報告能區分實際執行與未選取資料。

## 版本記錄

Python README 使用「ezSpec 2.0.4」字樣，但此參考 commit 的根目錄 `pom.xml:48` 設定 revision 為 `2.0.5`。
本次所有對照以固定 commit 的實際原始碼為依據，未把版本文字當作完整相容性證明。
