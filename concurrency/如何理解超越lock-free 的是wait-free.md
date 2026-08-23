# 核心理解：超越 Lock-Free 的 Wait-Free

理解「超越 Lock-Free 的是 Wait-Free」，核心在於分清**系統全體有進展（System-wide Progress）**與**個體絕對不飢餓（Individual Progress）**的區別。這兩者都屬於非阻塞（Non-blocking）同步機制，但 Wait-Free 的保證遠比 Lock-Free 嚴格。

---

## 1. Lock-Free（無鎖）：保證「整體」有進展

* **定義**：從宏觀角度來看，當多個執行緒同時執行時，**總能在有限步驟內確保至少有一個執行緒成功完成操作**。
* **運作方式**：常見的實現如 CAS（Compare-and-Swap）迴圈。執行緒 A 和 B 同時修改數據，A 成功了，B 失敗。B 必須回頭重新讀取並重新嘗試。
* **痛點（飢餓問題）**：如果執行緒競爭非常激烈，某些倒楣的執行緒可能會**不斷在迴圈中失敗與重試**，導致它自己的操作遲遲無法完成（無限期延遲/飢餓）。

---

## 2. Wait-Free（無等待）：保證「每個個體」有進展

* **定義**：比 Lock-Free 更進一步。它要求**每一個執行緒**無論其他執行緒如何干擾、搶佔或延遲，都**必須在有限的步驟內完成自己的操作**。
* **運作方式**：程式碼中絕對不允許出現「無限重試直到成功」的依賴型迴圈。每一個動作的步數都有確定的上限。
* **優勢**：它消除了個別執行緒的飢餓現象，提供即時系統（Real-time systems）所需的確定性與延遲上界。

---

## 3. 核心差異比較

| 維度 | Lock-Free（無鎖） | Wait-Free（無等待） |
| :--- | :--- | :--- |
| **進展保證** | 系統整體（Global） | 單個執行緒（Per-thread） |
| **重試迴圈** | 允許（如 `while(!CAS)`） | 不允許（步驟數有硬性上限） |
| **最差情況延遲** | 可能無限大（活鎖/嚴重飢餓） | 有界、可預測 |
| **實現難度** | 高 | 極高 |

---

## 總結

* **Lock-Free**：允許「犧牲少數人成就大局」（大家一起做，總有人成）。
* **Wait-Free**：則是「人人有功練、個個能完成」。

因此，Wait-Free 在數學和執行保證上是對 Lock-Free 的高級超越。


# 解析代碼範例（例如對比 Lock-Free CAS 隊列與 Wait-Free 隊列的源碼差異）

以下為您對比 Lock-Free 與 Wait-Free 佇列（Queue）的源碼架構與核心邏輯差異。
為方便理解，代碼以 C++ 虛擬碼（Pseudo-code）風格呈現，著重展示演算法結構而非語法細節。
------------------------------
## 1. Lock-Free 佇列：基於 CAS 的無限重試
Lock-Free 最著名的實現是 Michael & Scott 佇列（Java ConcurrentLinkedQueue 的基礎） [1]。其入隊（Enqueue）的核心邏輯是：不斷嘗試 CAS，失敗就重來。

void lock_free_enqueue(Node* new_node) {
    while (true) { // 核心：無限重試迴圈
        Node* tail = this->tail.load();
        Node* next = tail->next.load();

        if (tail == this->tail.load()) { // 確保資料沒有被其他執行緒中途修改
            if (next == nullptr) {
                // 嘗試將新節點接在尾端
                if (tail->next.compare_exchange_strong(next, new_node)) {
                    // 成功接上後，嘗試更新全域的 tail 指標
                    this->tail.compare_exchange_strong(tail, new_node);
                    return; // 成功完成，退出
                }
            } else {
                // 發現 tail 已經落後了（其他執行緒接了新節點但還沒更新 tail）
                // 協助將 tail 往後推進，然後重試
                this->tail.compare_exchange_strong(tail, next);
            }
        }
    } // 如果 CAS 失敗，會在這裡無休止地迴圈，導致特定執行緒飢餓
}


* 特徵：包含 while(true) 迴圈，內部依賴 compare_exchange (CAS)。
* 缺點：高併發時，多個執行緒同時 CAS，必有輸贏。輸的執行緒會無限重試，無法保證單一執行緒的完成時間。

------------------------------
## 2. Wait-Free 佇列：基於「協助機制」的有界步驟
要做到 Wait-Free，代碼中絕對不能有依賴競爭的無限迴圈。最經典的實現是透過 協助機制（Help-mechanism） [1]：當一個執行緒發現自己被卡住時，其他執行緒在做自己的事之前，必須先幫它完成。
以下是簡化版的 Wait-Free 入隊邏輯（引入了狀態陣列與協助指引）：

// 每個執行緒都有一個固定的登記欄位（OpDesc）struct OpDesc {
    long thread_id;
    Node* node;
    bool pending; // 是否等待協助
};
void wait_free_enqueue(Node* new_node, int thread_id) {
    // Step 1: 登記自己的需求（公告天下：我要入隊了）
    state_array[thread_id].node = new_node;
    state_array[thread_id].pending = true;

    // Step 2: 掃描其他執行緒，看看有沒有人需要幫忙
    // 關鍵：這是一個有界迴圈（有限次數，等於執行緒總數 N），絕不無限重試
    for (int i = 0; i < TOTAL_THREADS; i++) {
        if (state_array[i].pending) {
            // 發現執行緒 i 正在等待，主動幫它完成入隊
            help_enqueue(i); 
        }
    }
}
// 實際執行的協助函式void help_enqueue(int target_thread_id) {
    Node* new_node = state_array[target_thread_id].node;
    
    // 這裡內部會使用有限次數的 CAS 嘗試
    // 無論成功與否，只要發現 state_array[target_thread_id].pending 變成 false
    // 就代表「我自己成功了」或者「別人幫我成功了」，函式必定結束
    if (try_cas_enqueue(new_node)) {
        state_array[target_thread_id].pending = false;
    }
}


* 特徵：迴圈次數與執行緒總數（N）綁定，步驟數有嚴格上限（通常是 O(N) 或 O(1)）。
* 機制：執行緒 A 想入隊 → 寫入登記表 → 執行緒 B 進來時，先看登記表 → B 幫 A 把節點接上 → B 再做自己的事。A 甚至可能什麼都沒做，就被 B 幫忙完成了。

------------------------------
## 3. 源碼差異總結

   1. 控制流程：Lock-Free 使用條件迴圈（直到 CAS 成功）；Wait-Free 使用計數迴圈（遍歷執行緒登記表）。
   2. 記憶體開銷：Wait-Free 需要額外的空間（如 state_array）來記錄每個執行緒的狀態，空間複雜度通常隨執行緒數量線性增長。
   3. 執行代價：
   * Lock-Free：運氣好時（無競爭）只需 1 次 CAS，速度極快；運氣差時無限重試。
      * Wait-Free：無論運氣好壞，每次都要登記、掃描、幫忙，最壞與最好情況的開銷是一樣的。
   
------------------------------
我們可以繼續深入這個話題。你想了解：

* 這種「協助機制」在實務上會帶來什麼嚴重的記憶體與效能副作用？
* 業界如何折衷處理，發展出 Amortized Wait-Free（攤銷無等待） 演算法？


