# **I need the map with fast iteration, slow writes are ok.**

If **fast iteration** is the priority and **slow writes** are acceptable, the best approach is:

### **✅ 1. Copy-on-Write with Atomic Pointer (Best for Read-Heavy Workloads)**

- Writes update a new map and atomically swap the pointer.

- Reads and iterations are lock-free.

#### **Implementation**

package main

import (

"fmt"

"sync/atomic"

"unsafe"

)

type ConcurrentMap struct {

ptr unsafe.Pointer // Stores \*map\[string\]string atomically

}

func NewConcurrentMap() \*ConcurrentMap {

m := make(map\[string\]string)

return &ConcurrentMap{ptr: unsafe.Pointer(&m)}

}

func (c \*ConcurrentMap) Load() \*map\[string\]string {

return (\*map\[string\]string)(atomic.LoadPointer(&c.ptr))

}

func (c \*ConcurrentMap) Set(key, value string) {

// Create a new copy and update the pointer

oldMap := c.Load()

newMap := make(map\[string\]string, len(\*oldMap)+1)

for k, v := range \*oldMap {

newMap\[k\] = v

}

newMap\[key\] = value

atomic.StorePointer(&c.ptr, unsafe.Pointer(&newMap))

}

func (c \*ConcurrentMap) Get(key string) (string, bool) {

m := c.Load()

val, ok := (\*m)\[key\]

return val, ok

}

func (c \*ConcurrentMap) Iterate(fn func(string, string)) {

m := c.Load()

for k, v := range \*m {

fn(k, v)

}

}

func main() {

cm := NewConcurrentMap()

cm.Set("a", "1")

cm.Set("b", "2")

cm.Iterate(func(k, v string) {

fmt.Println(k, v)

})

}

### **✅ 2. RWMutex with Snapshot Copy (Slower Write, Fast Read & Iterate)**

If atomic swaps aren’t necessary, an RWMutex with a snapshot provides a simpler alternative.

type ConcurrentMap struct {

sync.RWMutex

data map\[string\]string

}

func NewConcurrentMap() \*ConcurrentMap {

return &ConcurrentMap{data: make(map\[string\]string)}

}

func (m \*ConcurrentMap) Set(key, value string) {

m.Lock()

defer m.Unlock()

m.data\[key\] = value

}

func (m \*ConcurrentMap) Get(key string) (string, bool) {

m.RLock()

defer m.RUnlock()

val, ok := m.data\[key\]

return val, ok

}

func (m \*ConcurrentMap) Iterate(fn func(string, string)) {

m.RLock()

snapshot := make(map\[string\]string, len(m.data))

for k, v := range m.data {

snapshot\[k\] = v

}

m.RUnlock()

for k, v := range snapshot {

fn(k, v)

}

}

- **Pros:** Fast iteration using a read snapshot

- **Cons:** More memory usage, slower writes due to copying

### **📌 Best Choice?**

||
||
||
||

**🔹 Pick Copy-on-Write (atomic pointer) if iteration needs to be the fastest.  **
**🔹 Pick RWMutex + Snapshot if you want simpler code with fewer unsafe operations.** 🚀
