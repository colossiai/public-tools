// ============================================================================
// 01 — Fixed-point prices: never represent money/prices with floating point
// Compile:  clang++ -std=c++20 -O2 01_fixed_point_price.cpp -o bin/01 && bin/01
// ----------------------------------------------------------------------------
// Why this matters in trading:
//   * `double` cannot represent 0.10 exactly -> rounding drift, failed equality,
//     and prices that don't land on the exchange tick grid.
//   * Exchanges quote prices on an integer *tick* grid (e.g. $0.01). Store the
//     price AS an integer number of ticks (or scaled integer) and all arithmetic
//     becomes exact, branch-free, and trivially comparable.
//   * Integer compares/adds are also faster and have deterministic latency.
// ============================================================================

#include <cstdint>
#include <iostream>
#include <format>
#include <compare>
#include <chrono>

// A price scaled to 4 implied decimals (1 unit = 0.0001). 123.4500 -> 1234500.
// int64 holds ~±9.2e14 at this scale = ±922,337,203,685 dollars. Plenty.
class Price {
    std::int64_t ticks_ = 0;                 // scaled integer, the single source of truth
    static constexpr std::int64_t kScale = 10'000;   // 4 decimal places

public:
    Price() = default;
    constexpr explicit Price(std::int64_t scaled) : ticks_(scaled) {}

    // Build from a human "dollars and 1/10000ths" without ever touching double.
    static constexpr Price from_decimal(std::int64_t whole, std::int64_t frac4 = 0) {
        return Price(whole * kScale + frac4);
    }

    constexpr std::int64_t raw() const { return ticks_; }

    // Exact arithmetic — these are just integer ops.
    constexpr Price operator+(Price o) const { return Price(ticks_ + o.ticks_); }
    constexpr Price operator-(Price o) const { return Price(ticks_ - o.ticks_); }

    // Spaceship => exact, total ordering for free (sorting a book, equality checks).
    constexpr auto operator<=>(const Price&) const = default;

    // Snap to a coarser tick size (e.g. round a theo price to the $0.01 grid).
    constexpr Price round_to_tick(std::int64_t tick_in_scale) const {
        // round-half-up on the integer grid, no FP.
        std::int64_t half = tick_in_scale / 2;
        std::int64_t r = ((ticks_ + (ticks_ >= 0 ? half : -half)) / tick_in_scale) * tick_in_scale;
        return Price(r);
    }

    // Only convert to text at the very edge (logging / display).
    std::string to_string() const {
        std::int64_t w = ticks_ / kScale, f = std::llabs(ticks_ % kScale);
        return std::format("{}.{:04}", w, f);
    }
};

int main() {
    // --- The classic floating-point trap --------------------------------------
    double a = 0.1, b = 0.2;
    std::cout << std::format("double 0.1 + 0.2 == 0.3 ? {}   (actual = {:.17f})\n",
                             (a + b == 0.3), a + b);

    // --- Fixed-point is exact -------------------------------------------------
    Price p1 = Price::from_decimal(0, 1000);   // 0.1000
    Price p2 = Price::from_decimal(0, 2000);   // 0.2000
    Price p3 = Price::from_decimal(0, 3000);   // 0.3000
    std::cout << std::format("fixed  0.1 + 0.2 == 0.3 ? {}   (sum = {})\n",
                             (p1 + p2) == p3, (p1 + p2).to_string());

    // --- Spread + tick rounding ----------------------------------------------
    Price bid = Price::from_decimal(123, 4500);   // 123.4500
    Price ask = Price::from_decimal(123, 4600);   // 123.4600
    Price spread = ask - bid;
    std::cout << std::format("bid={} ask={} spread={}\n",
                             bid.to_string(), ask.to_string(), spread.to_string());

    Price theo = Price::from_decimal(123, 4537);                 // 123.4537
    Price penny = theo.round_to_tick(100);                       // round to $0.01
    std::cout << std::format("theo={} rounded-to-$0.01={}\n",
                             theo.to_string(), penny.to_string());

    // --- Compile-time pricing (zero runtime cost) -----------------------------
    constexpr Price limit = Price::from_decimal(100, 0) + Price::from_decimal(0, 2500);
    static_assert(limit.raw() == 1'002'500, "computed entirely at compile time");
    std::cout << std::format("constexpr limit price = {}\n", limit.to_string());

    // --- Micro-benchmark: integer-tick vs double arithmetic -------------------
    // The headline reason for fixed-point is CORRECTNESS, not speed. But the
    // integer path is also branch-free and deterministic, so we should give up
    // nothing on throughput either. We time a tight add + compare loop both ways.
    // (At -O2 this is often a near-tie — the point is exactness comes for free.)
    constexpr std::size_t N = 100'000'000;

    Price acc_fp{0};
    const Price step_fp = Price::from_decimal(0, 1);    // +0.0001 per iter
    std::int64_t hits_fp = 0;
    auto t0 = std::chrono::steady_clock::now();
    for (std::size_t i = 0; i < N; ++i) {
        acc_fp = acc_fp + step_fp;
        if (acc_fp >= step_fp) ++hits_fp;               // exact integer compare
    }
    auto t1 = std::chrono::steady_clock::now();

    double acc_d = 0.0;
    const double step_d = 0.0001;
    std::int64_t hits_d = 0;
    for (std::size_t i = 0; i < N; ++i) {
        acc_d += step_d;
        if (acc_d >= step_d) ++hits_d;                  // FP compare (rounding!)
    }
    auto t2 = std::chrono::steady_clock::now();

    double ns_fp = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;
    double ns_d  = std::chrono::duration<double, std::nano>(t2 - t1).count() / N;
    std::cout << std::format(
        "\nbench add+compare over {} iters:\n"
        "  fixed-point : {:.3f} ns/op  (acc={}, hits={})\n"
        "  double      : {:.3f} ns/op  (acc={:.4f}, hits={})\n"
        "  ratio       : {:.2f}x (fixed-point gives exactness at ~no speed cost)\n",
        N, ns_fp, acc_fp.to_string(), hits_fp, ns_d, acc_d, hits_d, ns_d / ns_fp);

    return 0;
}
