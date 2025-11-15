# Why aligning the cache line can avoid the false sharing

Aligning cache lines can help avoid false sharing due to the way modern CPUs implement caching.

### What is False Sharing?

False sharing occurs when multiple threads on different processors modify variables that reside on the same cache line, leading to undesired performance degradation. Even though the threads are working on different variables, the shared cache line causes unnecessary cache coherency traffic.

### How Cache Lines Work

1. **Cache Line Size**: Cache lines are typically 64 bytes. When a single byte in this line is modified, the entire line must be reloaded in other caches.

2. **Memory Access**: If threads access different variables that fall within the same cache line, changing one variable will invalidate the cache line in other CPU caches. This leads to frequent cache misses and performance hits.

### Benefits of Aligning Cache Lines

- **Separate Cache Lines**: By aligning data structures to cache line boundaries, you ensure that each variable or frequently accessed data structure resides in its own cache line.

- **Reduced Coherence Traffic**: Since threads working on different variables will not be affecting the same cache line, it minimizes the invalidation messages sent across the memory subsystem.

- **Improved Performance**: Aligning data helps maintain cache locality, leading to more efficient memory access patterns and improved overall application performance.

### Conclusion

In summary, aligning cache lines helps prevent false sharing by ensuring that frequently accessed variables are placed in separate cache lines, reducing cache coherence traffic and improving the efficiency of multi-threaded applications.


### Summary
Cache lines typically consist of 64 bytes, If you update one byte of the cache line, the whole cache line gets
invalidated, this caused performance degradation.
By aligning the cache line boundaries, the frequently accessed variables keep it's own cahce line and won't get 
invalidated by other threads.