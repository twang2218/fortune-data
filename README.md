# 🎲 Fortune Data Collection Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/yourusername/fortune-data/graphs/commit-activity)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/yourusername/fortune-data/issues)

> A comprehensive multilingual fortune cookie data collection and curation system

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Project Structure](#-project-structure)
- [Statistics](#-statistics)
- [Data Sources](#-data-sources)
- [Development](#-development)
- [Contributing](#-contributing)

---

## 🌟 Overview

The Fortune Data Collection Project is a sophisticated data pipeline for gathering, processing, and curating multilingual quotes and sayings. It implements a two-tier system that balances quality with quantity, ensuring both exceptional quality for critical use cases and extensive content coverage for general usage.

---

## 🎯 Key Features

### Two-Tier Data Structure

#### ✨ Tier 1
- Top 500 highest-quality entries per language
- Carefully selected through rigorous quality control
- Ideal for space-constrained environments
- Perfect for scenarios requiring the absolute best content

#### 📚 Tier 2
- Comprehensive collection of high-quality content
- Organized by language and theme
- Suitable for full data distribution
- Maintains broader coverage while ensuring quality standards

### 🔄 Processing Pipeline

Our sophisticated processing pipeline:
- Collects data from multiple authoritative sources
- Applies quality control and filtering
- Organizes content by language and theme
- Ensures consistent formatting and structure

---

## 📂 Project Structure

```
.
├── cookies/
│   ├── tier1/          # Highest quality content (500 per language)
│   ├── tier2/          # Complete quality-filtered collection
│   └── raw/            # Source data
│       ├── crawled/    # Data directly from sources
│       └── processed/  # Data after quality filtering
├── scripts/            # Processing pipeline code
└── docs/              # Documentation
```

---

## 📊 Statistics

### Detailed Metrics

<table>
  <tr>
    <th align="left">Language</th>
    <th align="center">Sources</th>
    <th align="center">Raw Data</th>
    <th align="center">Tier 2</th>
    <th align="center">Tier 1</th>
  </tr>
  <tr>
    <td>🇺🇸 English</td>
    <td align="center">20</td>
    <td align="center">7,601</td>
    <td align="center">6,140 (80.8%)</td>
    <td align="center">500 (8.1%)</td>
  </tr>
  <tr>
    <td>🇪🇸 Spanish</td>
    <td align="center">17</td>
    <td align="center">3,781</td>
    <td align="center">3,433 (90.8%)</td>
    <td align="center">500 (14.6%)</td>
  </tr>
  <tr>
    <td>🇩🇪 German</td>
    <td align="center">13</td>
    <td align="center">2,829</td>
    <td align="center">2,147 (75.9%)</td>
    <td align="center">500 (23.3%)</td>
  </tr>
  <tr>
    <td>🇫🇷 French</td>
    <td align="center">30</td>
    <td align="center">4,120</td>
    <td align="center">2,860 (69.4%)</td>
    <td align="center">500 (17.5%)</td>
  </tr>
  <tr>
    <td>🇯🇵 Japanese</td>
    <td align="center">84</td>
    <td align="center">2,063</td>
    <td align="center">1,744 (84.5%)</td>
    <td align="center">500 (28.7%)</td>
  </tr>
  <tr>
    <td>🇷🇺 Russian</td>
    <td align="center">34</td>
    <td align="center">6,220</td>
    <td align="center">4,822 (77.5%)</td>
    <td align="center">500 (10.4%)</td>
  </tr>
  <tr>
    <td>🇨🇳 Chinese</td>
    <td align="center">67</td>
    <td align="center">10,912</td>
    <td align="center">8,746 (80.2%)</td>
    <td align="center">500 (5.7%)</td>
  </tr>
</table>

> **Tier 2 percentages** show how much raw data met quality standards - higher is better, indicating better source quality.  
> **Tier 1 percentages** show selection ratio from Tier 2 - lower is better, indicating more selective curation.

### Summary Statistics

<table>
  <tr>
    <th align="left">Metric</th>
    <th align="center">Count</th>
    <th align="left">Notes</th>
  </tr>
  <tr>
    <td>Languages</td>
    <td align="center">7</td>
    <td>🇺🇸 🇪🇸 🇩🇪 🇫🇷 🇯🇵 🇷🇺 🇨🇳</td>
  </tr>
  <tr>
    <td>Data Sources</td>
    <td align="center">265</td>
    <td>Various platforms and websites</td>
  </tr>
  <tr>
    <td>Raw Entries</td>
    <td align="center">37,526</td>
    <td>Total collected content</td>
  </tr>
  <tr>
    <td>Tier 2 Entries</td>
    <td align="center">29,892</td>
    <td>79.7% of raw data</td>
  </tr>
  <tr>
    <td>Tier 1 Entries</td>
    <td align="center">3,500</td>
    <td>11.7% of Tier 2</td>
  </tr>
</table>

---

## 📚 Data Sources

- [**WikiQuote**](https://www.wikiquote.org/): Multilingual quotes collection
- [**古诗文网**](https://www.gushiwen.cn/): Classical Chinese literature
- Additional curated sources per language

---

## 💻 Development

### Requirements

- Python 3.8+
- Dependencies listed in `pyproject.toml`
- Required environment variables

### Quick Start

```bash
# Process all data sources
python scripts/main.py

# Show statistics
python scripts/main.py --stats

# Process specific task file
python scripts/main.py custom_tasks.jsonl
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

- 📝 Add new data sources
- 🔧 Improve processing pipeline
- 🔍 Enhance quality control
- 🐛 Fix bugs or issues

Please check our contribution guidelines for details.

---

## 📄 License

- Source Code: [MIT License](LICENSE)
- Data Content: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- Original content follows respective source licenses

---

<p align="center">
<i>This project is actively maintained and regularly updated with new content and improvements.</i>
</p>
