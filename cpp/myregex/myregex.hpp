// ============================================================================
// myregex — a small, correct regular-expression engine (modern C++)
// ----------------------------------------------------------------------------
// Implements the subset from requirement/requirement.md:
//     literal text   .   *   ?   {n}   |
// plus two natural, necessary companions (documented as extensions):
//     ( ... )  grouping   and   \x  escaping a metacharacter
//
// Design (three clean stages, linear-time matching — no catastrophic backtracking):
//     1. Parser   — recursive descent over the pattern -> an AST.
//     2. Compiler — Thompson construction: AST -> an NFA program.
//     3. Program  — simulate the NFA over the input as a SET of active states,
//                   so an input of length n is matched in O(n * states) time.
//
// Matching semantics: `matches()` is a FULL match — the whole input must be
// consumed by the pattern (the common "does this string match this pattern?").
//
// Header-only; just `#include "myregex.hpp"`. Requires C++17 or newer.
// ============================================================================
#pragma once

#include <cctype>
#include <cstddef>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace myregex {

// Thrown for a malformed pattern (e.g. `a{`, `*ab`, unbalanced `(`).
class ParseError : public std::runtime_error {
public:
    ParseError(const std::string& msg, std::size_t pos)
        : std::runtime_error("myregex: parse error at position " + std::to_string(pos) + ": " + msg),
          position(pos) {}
    std::size_t position;
};

namespace detail {

// Guard against `{n}` blowing up memory (n copies are emitted) or overflowing int.
inline constexpr int kMaxRepeat = 100'000;

// ---------------------------------------------------------------------------
// Stage 1: the AST
// ---------------------------------------------------------------------------
struct Node {
    enum class Type {
        Empty,        // matches the empty string
        Literal,      // a single concrete character
        Any,          // '.'  — any one character
        Concat,       // children matched in sequence
        Alternation,  // '|'  — any one of the children
        Star,         // '*'  — zero or more of child[0]
        Optional,     // '?'  — zero or one of child[0]
        Repeat,       // '{n}'— exactly `count` copies of child[0]
    };
    explicit Node(Type t) : type(t) {}

    Type type;
    char literal = 0;  // Literal
    int count = 0;     // Repeat
    std::vector<std::unique_ptr<Node>> children;
};
using NodePtr = std::unique_ptr<Node>;

inline NodePtr make_node(Node::Type t) { return std::make_unique<Node>(t); }

// ---------------------------------------------------------------------------
// Stage 1: recursive-descent parser
//
// Grammar (lowest precedence first):
//     alternation := concat ('|' concat)*
//     concat      := repeat*
//     repeat      := atom ('*' | '?' | '{' number '}')?
//     atom        := '.' | '(' alternation ')' | '\' char | literal
// ---------------------------------------------------------------------------
class Parser {
public:
    explicit Parser(std::string_view pattern) : pat_(pattern) {}

    NodePtr parse() {
        NodePtr root = parse_alternation();
        if (!eof()) {
            // The only way to stop early is an unmatched ')' (or similar stray).
            throw ParseError(std::string("unexpected '") + peek() + "'", pos_);
        }
        return root;
    }

private:
    std::string_view pat_;
    std::size_t pos_ = 0;

    bool eof() const { return pos_ >= pat_.size(); }
    char peek() const { return pat_[pos_]; }

    NodePtr parse_alternation() {
        NodePtr left = parse_concat();
        if (eof() || peek() != '|') {
            return left;
        }
        NodePtr alt = make_node(Node::Type::Alternation);
        alt->children.push_back(std::move(left));
        while (!eof() && peek() == '|') {
            ++pos_;  // consume '|'
            alt->children.push_back(parse_concat());
        }
        return alt;
    }

    NodePtr parse_concat() {
        NodePtr concat = make_node(Node::Type::Concat);
        while (!eof() && peek() != '|' && peek() != ')') {
            concat->children.push_back(parse_repeat());
        }
        if (concat->children.empty()) {
            return make_node(Node::Type::Empty);  // e.g. "", "a|", "()"
        }
        if (concat->children.size() == 1) {
            return std::move(concat->children[0]);  // collapse trivial concat
        }
        return concat;
    }

    NodePtr parse_repeat() {
        NodePtr atom = parse_atom();
        if (eof()) {
            return atom;
        }
        switch (peek()) {
            case '*':
                ++pos_;
                return wrap(Node::Type::Star, std::move(atom));
            case '?':
                ++pos_;
                return wrap(Node::Type::Optional, std::move(atom));
            case '{':
                return parse_repeat_count(std::move(atom));
            default:
                return atom;
        }
    }

    NodePtr parse_repeat_count(NodePtr atom) {
        const std::size_t brace = pos_;
        ++pos_;  // consume '{'
        const std::size_t digits_begin = pos_;
        long n = 0;
        while (!eof() && std::isdigit(static_cast<unsigned char>(peek()))) {
            n = n * 10 + (peek() - '0');
            if (n > kMaxRepeat) {
                throw ParseError("repeat count in '{n}' is too large", brace);
            }
            ++pos_;
        }
        if (pos_ == digits_begin) {
            throw ParseError("expected a number inside '{n}'", brace);
        }
        if (eof() || peek() != '}') {
            throw ParseError("expected '}' to close '{n}'", brace);
        }
        ++pos_;  // consume '}'
        NodePtr rep = wrap(Node::Type::Repeat, std::move(atom));
        rep->count = static_cast<int>(n);
        return rep;
    }

    NodePtr parse_atom() {
        if (eof()) {
            throw ParseError("expected an expression but reached end of pattern", pos_);
        }
        const char c = peek();
        switch (c) {
            case '*':
            case '?':
            case '{':
                throw ParseError(std::string("nothing to repeat before '") + c + "'", pos_);
            case '|':
            case ')':
                throw ParseError(std::string("unexpected '") + c + "'", pos_);
            case '(': {
                ++pos_;  // consume '('
                NodePtr inner = parse_alternation();
                if (eof() || peek() != ')') {
                    throw ParseError("missing closing ')'", pos_);
                }
                ++pos_;  // consume ')'
                return inner;
            }
            case '.':
                ++pos_;
                return make_node(Node::Type::Any);
            case '\\': {
                ++pos_;  // consume '\'
                if (eof()) {
                    throw ParseError("trailing backslash (nothing to escape)", pos_ - 1);
                }
                return make_literal(pat_[pos_++]);
            }
            default:
                ++pos_;
                return make_literal(c);
        }
    }

    static NodePtr make_literal(char c) {
        NodePtr n = make_node(Node::Type::Literal);
        n->literal = c;
        return n;
    }
    static NodePtr wrap(Node::Type t, NodePtr child) {
        NodePtr n = make_node(t);
        n->children.push_back(std::move(child));
        return n;
    }
};

// ---------------------------------------------------------------------------
// Stage 2 & 3: the NFA program and its simulation
//
// Each state is one of:
//   Char  — consume a specific character, then go to `out`
//   Any   — consume any character, then go to `out`
//   Split — epsilon branch to both `out` and `out1` (no input consumed)
//   Match — accept
// ---------------------------------------------------------------------------
struct State {
    enum class Op { Char, Any, Split, Match };
    Op op;
    char ch = 0;   // Char
    int out = -1;  // next state (Char/Any/Split)
    int out1 = -1; // second branch (Split)
};

class Program {
public:
    std::vector<State> states;
    int start = -1;

    // Full match: the entire `text` must be consumed ending in a Match state.
    bool run(std::string_view text) const {
        std::vector<int> current;
        std::vector<int> next;
        current.reserve(states.size());
        next.reserve(states.size());
        std::vector<int> seen(states.size(), -1);  // per-step visited marker
        int gen = 0;

        ++gen;
        add_state(current, start, seen, gen);
        for (const char c : text) {
            if (current.empty()) {
                return false;  // no live states left — can't match the rest
            }
            ++gen;
            next.clear();
            for (const int s : current) {
                const State& st = states[s];
                if ((st.op == State::Op::Char && st.ch == c) || st.op == State::Op::Any) {
                    add_state(next, st.out, seen, gen);
                }
            }
            std::swap(current, next);
        }
        for (const int s : current) {
            if (states[s].op == State::Op::Match) {
                return true;
            }
        }
        return false;
    }

private:
    // Add `s` and follow epsilon (Split) edges, collecting consuming/Match states.
    // The `seen`/`gen` marker dedupes, which also makes epsilon cycles (e.g. from
    // `(a?)*`) terminate.
    void add_state(std::vector<int>& list, int s0, std::vector<int>& seen, int gen) const {
        std::vector<int> stack{s0};
        while (!stack.empty()) {
            const int s = stack.back();
            stack.pop_back();
            if (s < 0 || seen[s] == gen) {
                continue;
            }
            seen[s] = gen;
            if (states[s].op == State::Op::Split) {
                stack.push_back(states[s].out1);
                stack.push_back(states[s].out);
            } else {
                list.push_back(s);  // Char, Any, or Match
            }
        }
    }
};

// ---------------------------------------------------------------------------
// Stage 2: Thompson construction (AST -> NFA program)
//
// Each sub-expression compiles to a "fragment": a start state plus a list of
// dangling out-pointers ("holes") that the caller patches to whatever comes next.
// ---------------------------------------------------------------------------
class Compiler {
public:
    Program compile(const Node& root) {
        Frag f = emit(root);
        const int match = add(State{State::Op::Match});
        patch(f.holes, match);
        prog_.start = f.start;
        return std::move(prog_);
    }

private:
    struct Hole {
        int state;
        int slot;  // 0 -> out, 1 -> out1
    };
    struct Frag {
        int start;
        std::vector<Hole> holes;
    };

    Program prog_;

    int add(State s) {
        prog_.states.push_back(s);
        return static_cast<int>(prog_.states.size()) - 1;
    }
    void patch(const std::vector<Hole>& holes, int target) {
        for (const Hole h : holes) {
            (h.slot == 0 ? prog_.states[h.state].out : prog_.states[h.state].out1) = target;
        }
    }
    static std::vector<Hole> join(std::vector<Hole> a, const std::vector<Hole>& b) {
        a.insert(a.end(), b.begin(), b.end());
        return a;
    }

    // An epsilon pass-through: a Split whose two outs lead to the same place.
    Frag empty_frag() {
        const int s = add(State{State::Op::Split});
        return Frag{s, {{s, 0}, {s, 1}}};
    }

    Frag emit(const Node& n) {
        switch (n.type) {
            case Node::Type::Empty:
                return empty_frag();

            case Node::Type::Literal: {
                const int s = add(State{State::Op::Char});
                prog_.states[s].ch = n.literal;
                return Frag{s, {{s, 0}}};
            }
            case Node::Type::Any: {
                const int s = add(State{State::Op::Any});
                return Frag{s, {{s, 0}}};
            }
            case Node::Type::Concat: {
                if (n.children.empty()) {
                    return empty_frag();
                }
                Frag f = emit(*n.children[0]);
                for (std::size_t i = 1; i < n.children.size(); ++i) {
                    Frag g = emit(*n.children[i]);
                    patch(f.holes, g.start);
                    f.holes = std::move(g.holes);
                }
                return f;
            }
            case Node::Type::Alternation: {
                Frag f = emit(*n.children[0]);
                for (std::size_t i = 1; i < n.children.size(); ++i) {
                    Frag g = emit(*n.children[i]);
                    const int s = add(State{State::Op::Split});
                    prog_.states[s].out = f.start;
                    prog_.states[s].out1 = g.start;
                    f = Frag{s, join(std::move(f.holes), g.holes)};
                }
                return f;
            }
            case Node::Type::Star: {
                // Split: out -> body (loop), out1 -> exit. Body loops back to Split.
                const int s = add(State{State::Op::Split});
                Frag body = emit(*n.children[0]);
                prog_.states[s].out = body.start;
                patch(body.holes, s);
                return Frag{s, {{s, 1}}};
            }
            case Node::Type::Optional: {
                // Split: out -> body, out1 -> skip. Exit via body's holes OR out1.
                const int s = add(State{State::Op::Split});
                Frag body = emit(*n.children[0]);
                prog_.states[s].out = body.start;
                return Frag{s, join(std::move(body.holes), {{s, 1}})};
            }
            case Node::Type::Repeat: {
                if (n.count == 0) {
                    return empty_frag();  // `x{0}` matches the empty string
                }
                Frag f = emit(*n.children[0]);
                for (int i = 1; i < n.count; ++i) {
                    Frag g = emit(*n.children[0]);  // fresh copy of the sub-NFA
                    patch(f.holes, g.start);
                    f.holes = std::move(g.holes);
                }
                return f;
            }
        }
        throw std::logic_error("myregex: unhandled AST node");  // unreachable
    }
};

}  // namespace detail

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------
class Regex {
public:
    // Compiles `pattern`. Throws myregex::ParseError on a malformed pattern.
    explicit Regex(std::string_view pattern) : pattern_(pattern) {
        detail::Parser parser(pattern);
        detail::NodePtr ast = parser.parse();
        detail::Compiler compiler;
        program_ = compiler.compile(*ast);
    }

    // True iff `text` matches the pattern in full (the whole string is consumed).
    bool matches(std::string_view text) const { return program_.run(text); }

    const std::string& pattern() const { return pattern_; }

private:
    std::string pattern_;
    detail::Program program_;
};

// One-shot convenience: compile and match in a single call.
inline bool matches(std::string_view pattern, std::string_view text) {
    return Regex(pattern).matches(text);
}

}  // namespace myregex
