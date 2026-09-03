// g++ parse_log.cpp -o parse_log && ./parse_log

#include <filesystem>
#include <iostream>
#include <fstream>
#include <vector>
#include <string_view>
#include <string.h>
#include <algorithm>

using namespace std;

const string filename = "./demo.log";
const string delimiters = "=,";

const vector<double> percentile_list = {0.25, 0.5, 0.9, 0.95};

void split_strpbrk(string const &s, char const *delims, vector<string_view> &ret)
{
    vector<string_view> output;
    char const *p = s.c_str();
    char const *q = strpbrk(p + 1, delims);
    for (; q != NULL; q = strpbrk(p, delims))
    {
        output.push_back(string_view(p, q - p));
        p = q + 1;
    }
    if (*p)
    {
        output.push_back(string_view(p));
    }
    output.swap(ret);
}

void parseLine(const string &line, vector<double> &numbers)
{
    vector<string_view> tokens;
    split_strpbrk(line, delimiters.c_str(), tokens);
    numbers.push_back(stod(string(tokens[3])));
}

void showPercentiles(vector<double> &numbers)
{
    cout << "original value: ";
    for (auto v : numbers)
    {
        cout << v << " ";
    };
    cout << endl;
    // Percentile = (Number of Values Below “x” / Total Number of Values) × 100.
    sort(numbers.begin(), numbers.end());
    auto count = (int)numbers.size();
    for (auto p : percentile_list)
    {
        auto idx = int(p * count);
        idx = min(idx, count);
        cout << numbers[idx] << " ";
    }
    cout << endl;
}

long getDefaultCppStdVersion()
{
#ifdef __cplusplus
    return __cplusplus;
#endif
    return 0L;
}

int main()
{
    std::cout << "getDefaultCppStdVersion = " << getDefaultCppStdVersion() << std::endl;

    try
    {
        if (!filesystem::exists(filename))
        {
            cout << "File not exists: " << filename << endl;
            return -1;
        }

        std::ifstream infile(filename);
        std::string line;
        vector<double> numbers;
        numbers.reserve(1000);
        while (std::getline(infile, line))
        {
            // cout << line << endl;
            parseLine(line, numbers);
        }
        showPercentiles(numbers);
    }
    catch (std::exception &e)
    {
        cout << "exception: " << e.what() << endl;
    }

    return 0;
}