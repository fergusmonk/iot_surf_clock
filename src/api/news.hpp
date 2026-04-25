#pragma once
#include <string>
#include <vector>

struct NewsItem {
    std::string headline;
    std::string source;
};

class NewsClient {
public:
    virtual std::vector<NewsItem> fetchHeadlines(int count = 5) = 0;
    virtual ~NewsClient() = default;
};
