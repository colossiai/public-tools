# Techniques in C++ HFT system for high-speed order execution - checklist

## HPC

| Technique | Desc | Status | Performance Gain |  |
|---|---|---|---|---|
| CRTP |  | tested | CRTP result: 100000000, CRTP time: 140 ns<br>Virtual result: 100000000, Virtual time: 141,107,839 ns  (等于141ms, 1007913倍) 简单函数 |  |
| tcmalloc/Arena |  | tested | Benchmarking new(): 0.00345892 seconds<br>Benchmarking tcmalloc: 0.00039765 seconds<br>Benchmarking folly::SysArena(default chunk): 0.000051s<br>Benchmarking folly::SysArena(32k): 0.000038s<br>Benchmarking folly::benchmark_folly_thread_cached_arena: 0.000144s<br> |  |
| Arena+Placement New |  | tested | Regular new/delete: 140 ms<br>Arena + placement new: 6 ms |  |
| False Sharing | Cacne line alignment | tested | constexpr int NUM_ITERATIONS = 10'000'000;<br>False Sharing Time: 488.698 ms<br>Cache-Line Aligned Time: 96.6623 ms (19% of original time) |  |
| lockfree/MPMC Queue | Multi producer multi consumer | tested | with -O3<br>std::queue + mutex:Throughput: 7.03046e+06 msg/sec<br>Folly::MPMCQueue: Throughput: 8.21611e+06 msg/sec<br>MoodyCamel::ConcurrentQueue: Throughput: 8.84891e+06 msg/sec | https://github.com/cameron314/concurrentqueue |
| SIMD |  | tested | Traditional Addition Time: 7.3e-05 ms<br>SIMD Addition Time: 4.4e-05 ms (50% consumed time of original) |  |
| SBE |  | tested | ------------------------------------------------------------------------------<br>benchmark_serialize.cpp     relative  time/iter   iters/s<br>------------------------------------------------------------------------------<br>SBE_Encode_Decode                                           0.00fs  Infinity<br>Json_Encode_Decode                                          3.19us   313.61K |  |
| CPU Affinity | only on linux | tested | Time elapsed, unbind:1.5479, binding:1.5286, binding-pct:98.75 (bind/unbound) |  |
| String_View  |  | tested | ----------------------------------------------------------<br>Benchmark                Time             CPU   Iterations<br>----------------------------------------------------------<br>BM_ManualSplit         496 ns          495 ns      1290275<br>BM_AbseilSplit       0.755 ns        0.754 ns    758791137<br>BM_GetlineSplit        847 ns          846 ns       810326 |  |
| AbseilFlatMap |  | tested | --------------------------------------------------------------------------<br>Benchmark                                Time             CPU   Iterations<br>--------------------------------------------------------------------------<br>BM_AbseilFlatMapInsert/100000         5.67 ns         5.65 ns    123823675<br>BM_StdUnorderedMapInsert/100000       6.33 ns         6.26 ns    123626859<br>BM_StdMapInsert/100000                1.79 ns         1.78 ns    379966020<br>BM_AbseilFlatMapLookup/100000         9.12 ns         9.08 ns     75082322<br>BM_StdUnorderedMapLookup/100000       6.62 ns         6.58 ns     93764651<br>BM_StdMapLookup/100000                11.9 ns         11.8 ns     44080049 |  |
| Tcpdump |  | tested | N/A |  |
| Concept |  | tested | N/A, only compile time comparison to SFINAE |  |
| Core Dump(Linux) |  | tested | ulimit -c unlimited<br>set core dump pattern |  |
| rdstc() | vs std::chrono::high_resolution_clock | tested | std::chrono: 170105 ns<br>rdtsc cycles: 409918 cycles<br>rdtsc time:   157661 ns (using TSC frequency: 2600000000 Hz) |  |
| DPDK/f-stack(Linux) |  | test dpdk-testpmd (dummy) | DPDK does not require NUMA support, but it benefits significantly from it<br>We need DPDK compatible NIC or Virtual NIC<br>Acer linux WIFI driver r8188eu is not supported |  |
| NUMA(Linux) |  | know-how(require linux) | Acer linux lscpu Socket(s) = 1不支持 |  |
| ClickHouse |  | sql compatible |  |  |
| UDP Multicast | iperf3 -s -B 239.255.0.1 -4 | know-what |  |  |
| HugeTLB page(Linux) | Translation Lookaside Buffer | tested | $ ./hugetlb_bench <br>Buffer size: 512 MB<br>Regular Pages access time: 0.279466 seconds<br>HugePages access time: 0.0913678 seconds (3x faster) |  |
| Time sync(linuxptp) |  | Not working with USB wifi |  |  |
| Basic lock | std::mutex |  | std::mutex mtx;<br>void calc_safe(const std::string& msg) {<br>    std::lock_guard<std::mutex> lock(mtx);  // Automatically locks and unlocks<br>} |  |
| Read/Write lock | std::share_mutex |  | std::shared_mutex rw_mutex;<br>std::shared_lock read_lock(rw_mutex);  // shared (read) access<br>std::unique_lock write_lock(rw_mutex);  // exclusive (write) access |  |
