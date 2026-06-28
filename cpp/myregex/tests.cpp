// ============================================================================
// tests.cpp — test suite for myregex (no external framework)
// Build & run:  make test     (or: clang++ -std=c++20 tests.cpp -o bin/tests && bin/tests)
// Exits non-zero if any check fails.
// ============================================================================
#include "myregex.hpp"

#include <iostream>
#include <string>
#include <string_view>

namespace {

int g_failures = 0;
int g_checks = 0;

// Assert that pattern/text matching yields `expected`.
void check_match(std::string_view pattern, std::string_view text, bool expected) {
    ++g_checks;
    bool got = false;
    try {
        got = myregex::Regex(pattern).matches(text);
    } catch (const std::exception& e) {
        ++g_failures;
        std::cout << "FAIL  /" << pattern << "/ vs \"" << text << "\": threw \"" << e.what() << "\"\n";
        return;
    }
    if (got != expected) {
        ++g_failures;
        std::cout << "FAIL  /" << pattern << "/ vs \"" << text << "\": expected "
                  << (expected ? "match" : "no-match") << ", got " << (got ? "match" : "no-match") << "\n";
    }
}

// Assert that compiling `pattern` raises a ParseError.
void check_parse_error(std::string_view pattern) {
    ++g_checks;
    try {
        myregex::Regex r(pattern);
        (void)r;
    } catch (const myregex::ParseError&) {
        return;  // expected
    } catch (const std::exception& e) {
        ++g_failures;
        std::cout << "FAIL  /" << pattern << "/: expected ParseError, got other exception \"" << e.what() << "\"\n";
        return;
    }
    ++g_failures;
    std::cout << "FAIL  /" << pattern << "/: expected ParseError, but it compiled\n";
}

void test_literals() {
    check_match("", "", true);
    check_match("", "a", false);
    check_match("abc", "abc", true);
    check_match("abc", "abcd", false);  // full match: no trailing junk
    check_match("abc", "ab", false);
    check_match("abc", "xbc", false);
    check_match("a", "a", true);
    check_match("hello world", "hello world", true);
}

void test_dot() {
    check_match(".", "a", true);
    check_match(".", "Z", true);
    check_match(".", "", false);   // must consume exactly one char
    check_match(".", "ab", false);
    check_match("a.c", "abc", true);
    check_match("a.c", "axc", true);
    check_match("a.c", "ac", false);
    check_match("...", "xyz", true);
    check_match("...", "xy", false);
}

void test_star() {
    check_match("a*", "", true);
    check_match("a*", "a", true);
    check_match("a*", "aaaa", true);
    check_match("a*", "aaab", false);
    check_match("ab*c", "ac", true);
    check_match("ab*c", "abc", true);
    check_match("ab*c", "abbbbc", true);
    check_match("ab*c", "abxc", false);
    check_match(".*", "", true);
    check_match(".*", "anything at all 123", true);
    check_match("a.*z", "az", true);
    check_match("a.*z", "a-middle-z", true);
    check_match("a.*z", "abc", false);
}

void test_optional() {
    check_match("colou?r", "color", true);
    check_match("colou?r", "colour", true);
    check_match("colou?r", "colouur", false);
    check_match("a?", "", true);
    check_match("a?", "a", true);
    check_match("a?", "aa", false);
    check_match("ab?c?d", "abcd", true);
    check_match("ab?c?d", "ad", true);
    check_match("ab?c?d", "abd", true);
    check_match("ab?c?d", "acd", true);
}

void test_repeat_count() {
    check_match("a{3}", "aaa", true);
    check_match("a{3}", "aa", false);
    check_match("a{3}", "aaaa", false);
    check_match("a{1}", "a", true);
    check_match("a{0}", "", true);    // zero copies => empty
    check_match("a{0}", "a", false);
    check_match("ab{2}c", "abbc", true);
    check_match("ab{2}c", "abc", false);
    check_match(".{4}", "wxyz", true);
    check_match(".{4}", "wxy", false);
    check_match("a{2}b{2}", "aabb", true);
}

void test_alternation() {
    check_match("a|b", "a", true);
    check_match("a|b", "b", true);
    check_match("a|b", "c", false);
    check_match("a|b", "ab", false);  // full match
    check_match("cat|dog", "cat", true);
    check_match("cat|dog", "dog", true);
    check_match("cat|dog", "cot", false);
    check_match("abc|def|ghi", "def", true);
    check_match("abc|def|ghi", "ghi", true);
    check_match("abc|def|ghi", "xyz", false);
    check_match("a|", "a", true);   // empty alternative
    check_match("a|", "", true);
}

void test_grouping_extension() {
    check_match("(ab){2}", "abab", true);
    check_match("(ab){2}", "abababab", false);
    check_match("(a|b)c", "ac", true);
    check_match("(a|b)c", "bc", true);
    check_match("(a|b)c", "cc", false);
    check_match("(a|b)*", "", true);
    check_match("(a|b)*", "abba", true);
    check_match("(a|b)*", "abbac", false);
    check_match("(cat|dog)s?", "cats", true);
    check_match("(cat|dog)s?", "dog", true);
    check_match("gr(a|e)y", "gray", true);
    check_match("gr(a|e)y", "grey", true);
    check_match("gr(a|e)y", "groy", false);
}

void test_escaping_extension() {
    check_match("a\\.b", "a.b", true);
    check_match("a\\.b", "axb", false);
    check_match("\\*", "*", true);
    check_match("\\*", "x", false);
    check_match("a\\*b", "a*b", true);
    check_match("1\\|2", "1|2", true);
    check_match("\\(\\)", "()", true);
    check_match("\\\\", "\\", true);  // escaped backslash matches one backslash
}

void test_combinations() {
    // A simple "identifier-ish" pattern and an IPv4-octet-ish shape.
    check_match("a.*z|hello", "hello", true);
    check_match("a.*z|hello", "abcz", true);
    check_match("a.*z|hello", "world", false);
    check_match("(ab|cd)*", "abcdab", true);
    check_match("(ab|cd)*", "abc", false);
    check_match("x{2}(y|z)?", "xx", true);
    check_match("x{2}(y|z)?", "xxy", true);
    check_match("x{2}(y|z)?", "xxz", true);
    check_match("x{2}(y|z)?", "xxyz", false);
    // No catastrophic backtracking: this is linear-time in the NFA simulation.
    check_match("(a*)*b", std::string(50, 'a'), false);
    check_match("(a*)*b", std::string(50, 'a') + "b", true);
}

void test_parse_errors() {
    check_parse_error("*abc");     // nothing to repeat
    check_parse_error("a**");      // nothing to repeat (second '*')
    check_parse_error("?x");       // nothing to repeat
    check_parse_error("a{");       // unterminated {n}
    check_parse_error("a{}");      // missing number
    check_parse_error("a{2");      // missing }
    check_parse_error("a{x}");     // non-numeric
    check_parse_error("(abc");     // missing )
    check_parse_error("abc)");     // stray )
    check_parse_error("a\\");      // trailing backslash
    check_parse_error("{3}");      // nothing to repeat
}

}  // namespace

int main() {
    test_literals();
    test_dot();
    test_star();
    test_optional();
    test_repeat_count();
    test_alternation();
    test_grouping_extension();
    test_escaping_extension();
    test_combinations();
    test_parse_errors();

    std::cout << "\n" << (g_checks - g_failures) << "/" << g_checks << " checks passed.\n";
    if (g_failures != 0) {
        std::cout << g_failures << " FAILED\n";
        return 1;
    }
    std::cout << "All tests passed.\n";
    return 0;
}
