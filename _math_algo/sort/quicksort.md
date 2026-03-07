# Show in-place quicksort

Sure! Let’s look at an **in-place Quicksort** in Go (but the concept works in any language). “In-place” means we **don’t use extra arrays**; we just swap elements within the original array.

---

```go
package main

import "fmt"

// In-place quicksort
func quicksort(arr []int, low, high int) {
	if low < high {
		// Partition the array and get pivot index
		pivotIndex := partition(arr, low, high)
		
		// Recursively sort left and right subarrays
		quicksort(arr, low, pivotIndex-1)
		quicksort(arr, pivotIndex+1, high)
	}
}

// Partition function
func partition(arr []int, low, high int) int {
	pivot := arr[high] // choose last element as pivot
	i := low - 1       // index of smaller element

	for j := low; j < high; j++ {
		if arr[j] <= pivot {
			i++
			arr[i], arr[j] = arr[j], arr[i] // swap
		}
	}

	// Place pivot in correct position
	arr[i+1], arr[high] = arr[high], arr[i+1]
	return i + 1
}

func main() {
	arr := []int{8, 3, 1, 7, 0, 10, 2}
	quicksort(arr, 0, len(arr)-1)
	fmt.Println(arr) // Output: [0 1 2 3 7 8 10]
}
```

---

### How it works (step by step)

1. Pick the **pivot** (last element in this version).
2. Maintain an index `i` for **elements smaller than the pivot**Perfect! Let’s visualize **in-place Quicksort** with a diagram so you can “see” the swaps happening. I’ll walk step by step using the array we used before:

```
[8, 3, 1, 7, 0, 10, 2]
```

---

### Step 1: Pick Pivot

We choose the **last element as pivot** → `2`.

```
Array: [8, 3, 1, 7, 0, 10, 2]
Pivot = 2
i = -1
```

---

### Step 2: Partitioning (loop through low→high-1)

**j=0**: 8 > 2 → no swap → i stays -1
**j=1**: 3 > 2 → no swap → i stays -1
**j=2**: 1 ≤ 2 → swap arr[i+1] & arr[j] → swap arr[0] & arr[2]

```
Swap 8 and 1:
[1, 3, 8, 7, 0, 10, 2]
i = 0
```

**j=3**: 7 > 2 → no swap → i = 0
**j=4**: 0 ≤ 2 → swap arr[i+1] & arr[j] → swap arr[1] & arr[4]

```
Swap 3 and 0:
[1, 0, 8, 7, 3, 10, 2]
i = 1
```

**j=5**: 10 > 2 → no swap → i = 1

---

### Step 3: Place pivot in correct position

Swap arr[i+1] & arr[high] → swap arr[2] & arr[6]

```
Swap 8 and 2:
[1, 0, 2, 7, 3, 10, 8]
Pivot 2 is now at index 2
```

---

### Step 4: Recur on subarrays

* Left: `[1, 0]` → pivot = 0 → swaps → `[0,1]`
* Right: `[7,3,10,8]` → pivot = 8 → swaps → `[3,7,8,10]`

---

### ✅ Final Sorted Array

```
[0, 1, 2, 3, 7, 8, 10]
```

---

### Visual Swap Diagram (ASCII style)

```
Initial:  8  3  1  7  0 10  2  (pivot=2)
Step1:    1  3  8  7  0 10  2  (swap 8 & 1)
Step2:    1  0  8  7  3 10  2  (swap 3 & 0)
Step3:    1  0  2  7  3 10  8  (swap pivot 2 & 8)
```

Then recurse left `[1,0]` and right `[7,3,10,8]`.

---

If you want, I can make a **colorful, step-by-step visual diagram** like boxes and arrows showing `i`, `j`, and pivot moving—almost like an animation in one picture—which is extremely clear for students.

Do you want me to make that graphical version?
.
3. Loop through the array:

   * If element ≤ pivot → swap it with `arr[i+1]` and increment `i`.
4. Finally, swap the pivot into its correct spot (`i+1`).
5. Recur on the **left** and **right** subarrays.
6. Done! No extra array is needed.

---

💡 **Key point:** In-place quicksort is memory-efficient because it only uses **stack space** for recursion, not extra arrays.

If you like, I can also make a **diagram showing the in-place swaps visually**, which really helps students understand.

Do you want me to make that diagram?


# go full code


```go

package qsort

import (
	"fmt"
	"log"
	"testing"
)

func QSort(items []int, low, high int) {
	fmt.Println("======")
	fmt.Printf("QSort: %+v \n", items[low:high+1])
	if high > low {
		pivotIdx := partition(items, low, high)

		QSort(items, 0, pivotIdx-1)
		QSort(items, pivotIdx+1, high)
	}
}

func partition(items []int, low, high int) int {
	pivot := items[high]
	i := low - 1

	for j := low; j < high; j++ {
		if items[j] < pivot {
			i++
			log.Println("partition: pivot ", pivot, " swap ", items[i], " and ", items[j])
			items[i], items[j] = items[j], items[i]
		}
	}

	log.Println("partition_end: swap pivot: ", items[i+1], items[high])
	items[i+1], items[high] = items[high], items[i+1]
	return i + 1
}

func TestSort(t *testing.T) {
	arr := []int{8, 3, 1, 7, 0, 3, 10, 2}
	QSort(arr, 0, len(arr)-1)
	t.Logf("after sorted 1: %+v", arr)

}

```