// ============================================================================
// 08 — Static dispatch (CRTP / templates) instead of virtual on the hot path
// Compile:  clang++ -std=c++20 -O2 08_static_dispatch_crtp.cpp -o bin/08 && bin/08
// ----------------------------------------------------------------------------
// A `virtual` call costs an indirect jump through the vtable: the CPU can't
// inline it, often mispredicts the target, and loses cross-call optimization.
// On a per-tick strategy callback fired millions of times, that adds up.
//
// When the set of types is known at compile time, replace runtime polymorphism
// with COMPILE-TIME polymorphism so the callback inlines into the feed loop:
//   * CRTP (Curiously Recurring Template Pattern) — a static-dispatch base.
//   * std::variant + std::visit — closed type set, still no vtable, and you can
//     hold heterogeneous strategies in one container.
//
// We benchmark a virtual strategy vs a CRTP strategy over the same tick stream.
// ============================================================================

#include <cstdint>
#include <vector>
#include <memory>
#include <chrono>
#include <iostream>
#include <format>

struct Tick { std::int64_t price; std::uint32_t qty; };

// ---------- Runtime polymorphism (virtual): flexible but uninlinable ----------
struct IStrategy {
    virtual ~IStrategy() = default;
    virtual void on_tick(const Tick&) = 0;
    virtual std::int64_t pnl() const = 0;
};
struct MomentumVirtual final : IStrategy {
    std::int64_t acc = 0, last = 0;
    void on_tick(const Tick& t) override {
        acc += (t.price - last) * t.qty;     // trivial "signal"
        last = t.price;
    }
    std::int64_t pnl() const override { return acc; }
};

// ---------- Compile-time polymorphism (CRTP): inlines into the loop -----------
template <typename Derived>
struct StrategyBase {
    void on_tick(const Tick& t) { static_cast<Derived*>(this)->on_tick_impl(t); }
};
struct MomentumCRTP : StrategyBase<MomentumCRTP> {
    std::int64_t acc = 0, last = 0;
    void on_tick_impl(const Tick& t) {       // statically resolved => inlinable
        acc += (t.price - last) * t.qty;
        last = t.price;
    }
    std::int64_t pnl() const { return acc; }
};

int main() {
    constexpr std::size_t N = 20'000'000;
    std::vector<Tick> feed(N);
    for (std::size_t i = 0; i < N; ++i)
        feed[i] = Tick{100'0000 + static_cast<std::int64_t>(i % 100), 10};

    // Virtual dispatch through a base pointer (the realistic, pessimistic case).
    std::unique_ptr<IStrategy> vs = std::make_unique<MomentumVirtual>();
    auto t0 = std::chrono::steady_clock::now();
    for (const auto& t : feed) vs->on_tick(t);
    auto t1 = std::chrono::steady_clock::now();

    // CRTP: the call inlines, the compiler can vectorize/keep state in registers.
    MomentumCRTP cs;
    for (const auto& t : feed) cs.on_tick(t);
    auto t2 = std::chrono::steady_clock::now();

    double ns_v = std::chrono::duration<double, std::nano>(t1 - t0).count() / N;
    double ns_c = std::chrono::duration<double, std::nano>(t2 - t1).count() / N;

    std::cout << std::format("virtual on_tick : {:.3f} ns/tick  pnl={}\n", ns_v, vs->pnl());
    std::cout << std::format("CRTP    on_tick : {:.3f} ns/tick  pnl={}  (speedup {:.2f}x)\n",
                             ns_c, cs.pnl(), ns_v / ns_c);
    std::cout << "note: speedup depends on how much the body inlines; the win grows\n"
                 "      with smaller callback bodies and tighter loops.\n";
    return 0;
}
