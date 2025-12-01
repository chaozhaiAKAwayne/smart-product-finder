# Smart Product Finder

An intelligent multi-agent AI system for e-commerce product search across multiple platforms (Taobao, JD, Pinduoduo), featuring precise brand/model matching, price analysis, and best deal recommendations.

## 🎯 Key Features

This project demonstrates the following core AI Agent concepts:

### ✅ 1. Multi-Agent System
- **CoordinatorAgent**: Main coordinator responsible for task distribution and result aggregation
- **Platform Agents**:
  - JDSearchAgent (JD.com search agent)
  - TaobaoSearchAgent (Taobao search agent)
  - PDDSearchAgent (Pinduoduo search agent)
- **FilterAgent**: Result filtering and analysis agent
- **Parallel Execution**: Support for concurrent multi-platform searches for improved efficiency
- **Sequential Execution**: Also supports sequential platform searches

### ✅ 2. Custom Tools
- **BrowserTool**: Browser automation tool based on Playwright
- **ProductExtractor**: LLM-powered product information extraction using Claude
- **PriceValidator**: Price validation and analysis tool

### ✅ 3. Sessions & Memory
- **SessionManager**: Session state management supporting multi-user sessions
- **SearchHistory**: Search history tracking and statistical analysis
- **Persistent Storage**: Session and history data saved to JSON files

### ✅ 4. Observability
- **Structured Logging**: Hierarchical logging (INFO/WARNING/ERROR)
- **Metrics Collection**: MetricsCollector for system performance tracking
- **Performance Tracing**: Execution time tracking for each search
- **Log Rotation**: Automatic log file size and backup management

## 🏗️ System Architecture

```
SmartProductFinder
├── CoordinatorAgent (Orchestrator)
│   ├── JDSearchAgent (JD.com)
│   ├── TaobaoSearchAgent (Taobao)
│   ├── PDDSearchAgent (Pinduoduo)
│   └── FilterAgent (Filter & Analyze)
├── Tools (Tool Layer)
│   ├── BrowserTool
│   ├── ProductExtractor
│   └── PriceValidator
└── Memory (Memory Layer)
    ├── SessionManager
    └── SearchHistory
```

## 📋 Core Functionality

1. **Exact Match Search**: Returns only products that exactly match the specified brand and model - no similar products
2. **Price Control**: Strict filtering based on maximum price limit
3. **Parallel Multi-Platform Search**: Simultaneous searches across multiple e-commerce platforms to save time
4. **Intelligent Price Analysis**:
   - Min, max, average, and median prices
   - Cross-platform price comparison
   - Best deal recommendations
5. **Duplicate Filtering**: Automatic removal of duplicate products
6. **Search History**: Records all search history with statistical analysis
7. **Session Management**: Support for multi-user, multi-session environments

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Configure API Key

Edit `config.yaml` and add your Claude API key:

```yaml
claude:
  api_key: "your-api-key-here"  # Replace with your API key
  model: "claude-sonnet-4-5-20250929"
```

### 4. Run Example

```bash
python main.py
```

## 💡 Usage Examples

### Basic Usage

```python
import asyncio
from main import SmartProductFinder

async def search_example():
    finder = SmartProductFinder()

    # Initialize components
    await finder.initialize_components()

    try:
        # Search for iPhone
        result = await finder.search(
            brand="Apple",
            model="iPhone 15 Pro",
            max_price=8999.0,
            platforms=['jd', 'taobao', 'pdd']
        )

        # Display results
        finder.display_results(result)

    finally:
        # Cleanup resources
        await finder.cleanup()

asyncio.run(search_example())
```

### Advanced Usage - Custom Sessions

```python
# Create a specific session
session_id = "user_12345"
result = await finder.search(
    brand="Xiaomi",
    model="Xiaomi 14",
    max_price=3999.0,
    session_id=session_id
)

# View session history
finder.show_history(session_id=session_id)

# Get statistics
stats = finder.search_history.get_search_statistics(session_id)
print(f"User has made {stats['total_searches']} searches")
```

### Result Structure

```python
{
    'status': 'success',
    'search_criteria': {
        'brand': 'Apple',
        'model': 'iPhone 15 Pro',
        'max_price': 8999.0
    },
    'filtered_products': [
        {
            'title': '...',
            'price': 7999.0,
            'brand': 'Apple',
            'model': 'iPhone 15 Pro',
            'platform': 'jd',
            'shop': '...',
            'url': '...'
        }
    ],
    'best_deals': [...],  # Top 5 cheapest products
    'price_analysis': {
        'count': 25,
        'min': 7999.0,
        'max': 8899.0,
        'average': 8399.0,
        'median': 8399.0,
        'by_platform': {...}
    },
    'summary': {
        'total_products_found': 30,
        'after_filtering': 25,
        'successful_platforms': ['jd', 'taobao'],
        'failed_platforms': []
    },
    'execution_time': 15.3
}
```

## 📁 Project Structure

```
smart-product-finder/
├── agents/                      # Agent modules
│   ├── base_agent.py           # Base agent class
│   ├── coordinator_agent.py    # Coordinator agent
│   ├── jd_search_agent.py      # JD search agent
│   ├── taobao_search_agent.py  # Taobao search agent
│   ├── pdd_search_agent.py     # Pinduoduo search agent
│   └── filter_agent.py         # Filter agent
├── tools/                       # Tool modules
│   ├── browser_tool.py         # Browser tool
│   ├── product_extractor.py    # Product extraction tool
│   └── price_validator.py      # Price validation tool
├── memory/                      # Memory modules
│   ├── session_manager.py      # Session manager
│   └── search_history.py       # Search history
├── logs/                        # Log directory (auto-created)
├── main.py                      # Main entry point
├── logger_config.py            # Logging configuration
├── config.yaml                 # Configuration file
├── requirements.txt            # Dependencies
├── need.txt                    # Project requirements
└── README.md                   # This file
```

## ⚙️ Configuration

### config.yaml

```yaml
# Claude API Configuration
claude:
  api_key: "your-api-key-here"
  model: "claude-sonnet-4-5-20250929"

# Browser Configuration
browser:
  headless: false    # false=show browser, true=background mode
  timeout: 30000     # Timeout in milliseconds

# Search Configuration
search:
  max_results_per_platform: 10  # Max results per platform
  platforms:
    - jd
    - taobao
    - pdd
```

## 📊 Logging and Monitoring

### Log Files

- `logs/app_YYYYMMDD.log`: All logs
- `logs/error_YYYYMMDD.log`: Error logs only
- `logs/sessions.json`: Session data
- `logs/search_history.json`: Search history

### View Metrics

```python
# Display system metrics
finder.show_metrics()
```

Sample output:
```
Metrics Summary:
================
Total Searches: 10
Successful: 9 (90.0%)
Failed: 1
Products Found: 125
Avg Search Time: 12.5s

Platform Queries:
- JD: 10
- Taobao: 8
- PDD: 7
```

## 🔧 Extension Development

### Adding New E-commerce Platforms

1. Create a new Agent class (inherit from BaseAgent):

```python
from agents.base_agent import BaseAgent

class NewPlatformAgent(BaseAgent):
    def __init__(self, browser_tool, extractor, logger=None):
        super().__init__("NewPlatform_Agent", logger)
        self.browser_tool = browser_tool
        self.extractor = extractor

    async def execute(self, task):
        # Implement search logic
        pass
```

2. Register the new agent in CoordinatorAgent
3. Update config.yaml to add the new platform

### Custom Filtering Rules

Modify the filtering logic in `agents/filter_agent.py`:

```python
def custom_filter(self, products):
    # Add custom filtering rules
    return filtered_products
```

## 🎓 Course Requirements Mapping

| Requirement | Implementation | Location |
|-------------|----------------|----------|
| Multi-agent system | ✅ Coordinator + 3 platform agents + filter agent | `agents/` |
| Parallel agents | ✅ Parallel multi-platform search | `coordinator_agent.py:76` |
| Custom tools | ✅ Browser, extractor, validator tools | `tools/` |
| Sessions & Memory | ✅ Session manager + search history | `memory/` |
| Observability | ✅ Structured logging + metrics collection | `logger_config.py` |

## ⚠️ Important Notes

1. **Anti-Scraping**: E-commerce platforms have anti-scraping mechanisms. You may need to:
   - Reduce request frequency
   - Use proxy IPs
   - Handle CAPTCHAs (requires manual intervention)

2. **API Quotas**: Claude API has rate limits. Consider:
   - Using caching to reduce duplicate calls
   - Controlling search frequency

3. **Browser Resources**: Playwright consumes system resources. Recommendations:
   - Close browser instances promptly
   - Use headless mode (for production)

## 📝 Development Roadmap

- [ ] Add support for more e-commerce platforms (Amazon, Suning, etc.)
- [ ] Implement product image comparison
- [ ] Add price trend tracking
- [ ] Support price change notifications
- [ ] Web UI interface
- [ ] RESTful API endpoints
- [ ] Docker containerization for deployment

## 📄 License

MIT License

## 👤 Author

AI Agent Course Project

---

**Note**: Please ensure you have configured your Claude API key before use and comply with the terms of service of each e-commerce platform.
