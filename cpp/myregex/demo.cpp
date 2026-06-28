// ============================================================================
// demo.cpp — command-line driver for myregex
// ----------------------------------------------------------------------------
//   make demo                       # runs a built-in showcase
//   bin/demo '<pattern>' <text>...  # test one pattern against one or more strings
//
// Examples:
//   bin/demo 'colou?r' color colour colouur
//   bin/demo '(cat|dog)s?' cat cats dog dogs fish
//   bin/demo 'a.*z' az abcz abc
// ============================================================================
#include "myregex.hpp"

#include <iostream>
#include <string_view>

namespace {

void show(std::string_view pattern, std::string_view text) {
    try {
        const bool ok = myregex::Regex(pattern).matches(text);
        std::cout << "  /" << pattern << "/  vs  \"" << text << "\"  =>  "
                  << (ok ? "MATCH" : "no match") << "\n";
    } catch (const myregex::ParseError& e) {
        std::cout << "  /" << pattern << "/  =>  " << e.what() << "\n";
    }
}

void showcase() {
    std::cout << "myregex showcase (full-match semantics)\n"
                 "supported: literal text   .   *   ?   {n}   |   (grouping)   \\escape\n\n";

    struct Case {
        const char* pattern;
        const char* text;
    };
    const Case cases[] = {
        {"abc", "abc"},          {"abc", "abcd"},
        {"a.c", "axc"},          {"a.c", "ac"},
        {"ab*c", "abbbbc"},      {"ab*c", "ac"},
        {"colou?r", "color"},    {"colou?r", "colour"},
        {"a{3}", "aaa"},         {"a{3}", "aa"},
        {"cat|dog", "dog"},      {"cat|dog", "cow"},
        {"(a|b)*", "abba"},      {"(ab){2}", "abab"},
        {"a\\.b", "a.b"},        {"a\\.b", "axb"},
        {"a.*z", "a-middle-z"},  {"a.*z", "abc"},
    };
    for (const Case& c : cases) {
        show(c.pattern, c.text);
    }

    std::cout << "\nmalformed patterns are reported, not crashed on:\n";
    for (const char* bad : {"a{", "*x", "(abc"}) {
        show(bad, "");
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        showcase();
        std::cout << "\ntip: bin/demo '<pattern>' <text>...  to test your own.\n";
        return 0;
    }
    const std::string_view pattern = argv[1];
    if (argc == 2) {
        // Just validate / report the pattern.
        try {
            myregex::Regex r(pattern);
            std::cout << "/" << pattern << "/ compiled OK. Pass strings to test it.\n";
        } catch (const myregex::ParseError& e) {
            std::cout << e.what() << "\n";
            return 1;
        }
        return 0;
    }
    for (int i = 2; i < argc; ++i) {
        show(pattern, argv[i]);
    }
    return 0;
}
