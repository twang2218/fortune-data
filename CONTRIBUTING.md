# 🌟 Contributing to Fortune Data Collection Project

> Welcome to our project! Every contribution helps build this unique multilingual collection of wisdom and knowledge.

## 🎯 How You Can Help

We're excited to have you here! There are many ways you can contribute to make this project even better:

- 🔍 Adding new data sources
- 🛠️ Improving existing crawlers
- ✨ Enhancing data processing
- 📝 Improving documentation
- 🐛 Fixing bugs

## 🚀 Getting Started

### Setting Up Your Environment

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh
```


## 💡 Adding New Data Sources

The heart of our project lies in its diverse data sources. Here's how you can add a new one!

### ✨ Creating Your Crawler

Take inspiration from our existing crawlers (`wikiquote.py`, `gushiwen.py`). Here's a template to get you started:

```python
from typing import List
from common import Cookie, CookieJar
from loguru import logger
from pydantic import Field
from .crawler import Crawler

class YourAmazingCrawler(Crawler):
    """Your crawler for collecting wonderful quotes!"""
    
    base_url: str = Field(
        default="https://your-source.com/api",
        description="The base URL for your source"
    )
    
    def crawl(self, jar: CookieJar) -> List[Cookie]:
        """Main crawling logic - where the magic happens!"""
        logger.info(f"Starting collection: {jar.name}")
        cookies = []
        
        # Your brilliant implementation here
        jar.link = self.format_url(jar)
        soup = self.get_page(jar.link)
        
        for item in self.parse_list(soup):
            cookie = self.parse_item(item)
            if cookie.content:
                cookies.append(cookie)
                
        logger.info(f"Collection complete! Found {len(cookies)} entries")
        return cookies
```

### 🧪 Testing Your Crawler

Create a test file in `scripts/extract/test/` to ensure your crawler works perfectly:

```python
def test_your_amazing_crawler():
    """Verify your crawler works as expected"""
    jar = CookieJar(
        name="your_source",
        extractor="crawler.your_source.lang",
        lang="lang_code"
    )
    cookies = YourAmazingCrawler.extract(jar)
    
    # Make sure we got some good stuff!
    assert len(cookies) > 0
    for cookie in cookies:
        assert cookie.content.strip()
        assert cookie.source.strip()
```

## 🎨 Code Style

We use `ruff` to keep our code beautiful:

```bash
make format
```

## 📖 Project Structure

```
scripts/
├── extract/          # 🕷️ Crawlers live here
│   ├── wikiquote.py  # Wikipedia quotes crawler
│   ├── gushiwen.py   # Classical literature crawler
│   └── your_file.py  # Your amazing crawler goes here!
├── transform/        # ✨ Data processing magic
└── load/            # 💾 Data storage

cookies/             # 📚 Generated content (hands off!)
├── tier1/           # ⭐ Premium content
├── tier2/           # 📚 Complete collection
└── raw/             # 🌱 Raw data
```

## ❤️ Best Practices

1. **Crawler Design**
   - Focus on one source at a time
   - Handle errors gracefully
   - Log meaningful messages
   - Follow existing patterns

2. **Testing**
   - Write tests for your crawler
   - Test both success and error cases
   - Use meaningful test data

3. **Documentation**
   - Comment your code
   - Update source attribution
   - Share insights about your source

## 🤝 Need Help?

- 💭 Have questions? Open an issue!
- 💡 Got ideas? We'd love to hear them!
- 🤔 Not sure about something? Just ask!

## 📜 License

- 💻 Code: MIT License
- 📚 Data: CC BY-SA 3.0

---

<p align="center">
<i>Thank you for considering contributing to our project! Together, we can build something amazing! ✨</i>
</p>
