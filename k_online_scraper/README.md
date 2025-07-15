# K-Online Scraper Tool

A comprehensive Python-based web scraping tool that automatically extracts company information from the K-Online exhibitor directory and generates potential domain variants for each company.

## 🚀 Features

- **Web Scraping**: Robust scraping of K-Online exhibitor directory with error handling and rate limiting
- **Dual Engine Support**: Both requests/BeautifulSoup and Selenium WebDriver for JavaScript-heavy content
- **Domain Generation**: Intelligent domain variant generation based on company names
- **Multiple Export Formats**: CSV, JSON, and Excel export with detailed statistics
- **CLI Interface**: User-friendly command-line interface with progress indicators
- **Domain Validation**: Optional DNS lookup for domain availability checking
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Data Validation**: Robust data cleaning and validation

## 📋 Requirements

- Python 3.7+
- Chrome/Chromium browser (for Selenium)

## 🛠️ Installation

1. **Clone or download the project:**
```bash
cd k_online_scraper
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install ChromeDriver (for Selenium support):**
   - Download from [ChromeDriver](https://chromedriver.chromium.org/)
   - Or install via package manager:
     ```bash
     # Ubuntu/Debian
     sudo apt-get install chromium-chromedriver
     
     # macOS
     brew install chromedriver
     
     # Windows
     choco install chromedriver
     ```

## 🎯 Quick Start

### Test the scraper
```bash
python main.py test
```

### Basic scraping
```bash
python main.py scrape
```

### Advanced scraping with options
```bash
python main.py scrape --output-format excel --max-pages 5 --generate-domains --check-availability
```

### Generate domains for a specific company
```bash
python main.py generate-domains "Mustermann GmbH" --tlds .de --tlds .com --check-availability
```

### Run demonstration
```bash
python main.py demo --format json
```

## 📖 Usage Guide

### Command Overview

```bash
python main.py --help
```

### Available Commands

#### 1. **scrape** - Main scraping command
```bash
python main.py scrape [OPTIONS]
```

**Options:**
- `--output-format, -f`: Export format (csv/json/excel) - default: csv
- `--output-file, -o`: Custom output filename (without extension)
- `--max-pages, -p`: Maximum pages to scrape (default: all)
- `--use-selenium, -s`: Use Selenium for JavaScript content
- `--generate-domains, -d`: Generate domain variants (default: True)
- `--check-availability, -c`: Check domain availability via DNS
- `--max-domains, -m`: Maximum domain variants per company (default: 5)

**Examples:**
```bash
# Basic scraping to CSV
python main.py scrape

# Export to Excel with domain checking
python main.py scrape -f excel -c

# Scrape 10 pages using Selenium
python main.py scrape -p 10 -s

# Custom filename and format
python main.py scrape -f json -o "my_companies"
```

#### 2. **test** - Test scraper functionality
```bash
python main.py test
```

Validates connectivity and basic scraping functionality.

#### 3. **generate-domains** - Generate domains for specific company
```bash
python main.py generate-domains "Company Name" [OPTIONS]
```

**Options:**
- `--tlds, -t`: TLD variants (can be used multiple times)
- `--check-availability, -c`: Check domain availability

**Examples:**
```bash
# Generate domains for a company
python main.py generate-domains "Tech Solutions GmbH"

# With specific TLDs and availability check
python main.py generate-domains "Mustermann AG" -t .de -t .com -t .org -c
```

#### 4. **demo** - Run demonstration
```bash
python main.py demo [--format FORMAT]
```

Processes sample data to demonstrate functionality.

### Global Options

- `--log-level`: Set logging level (DEBUG/INFO/WARNING/ERROR)
- `--log-file`: Custom log file path

## 📊 Output Formats

### CSV Export
Structured tabular format with all company data and generated domains.

### JSON Export
```json
{
  "metadata": {
    "export_timestamp": "2024-01-01T12:00:00",
    "total_companies": 150,
    "fields": [...]
  },
  "companies": [
    {
      "company_name": "Example GmbH",
      "city": "Berlin",
      "generated_domains": [
        {
          "domain": "example.de",
          "variant": "example",
          "tld": ".de",
          "status": "available"
        }
      ]
    }
  ]
}
```

### Excel Export
Multi-sheet workbook containing:
- **Companies**: Main company data
- **Statistics**: Processing statistics
- **Domain_Details**: Detailed domain information

## ⚙️ Configuration

The tool uses configuration files in the `config/` directory:

### `config/settings.py`
- Scraping parameters (timeouts, delays, user agents)
- Domain generation settings
- Export configurations
- Logging settings

### Key Configuration Options

```python
# Scraping settings
SCRAPING_CONFIG = {
    "request_timeout": 30,
    "retry_attempts": 3,
    "delay_between_requests": 1.0,
    "max_concurrent_requests": 5
}

# Domain generation
DOMAIN_CONFIG = {
    "tlds": [".de", ".com", ".org", ".net"],
    "max_variants_per_company": 5,
    "check_domain_availability": False
}
```

## 🔧 Advanced Usage

### Custom Domain Generation
The domain generator creates variants by:
1. Cleaning company names (removing legal suffixes, special characters)
2. Creating abbreviations from multiple words
3. Generating variants with/without hyphens
4. Adding common number suffixes
5. Removing common business words

### Selenium vs Requests
- **Requests + BeautifulSoup**: Faster, lower resource usage
- **Selenium**: Required for JavaScript-heavy content, slower but more reliable

### Error Handling
The tool includes comprehensive error handling:
- Network timeouts and retries
- Invalid HTML parsing
- Domain validation errors
- Export failures

### Logging
Logs are written to both console and file:
- Default log file: `k_online_scraper.log`
- Configurable log levels
- Rotating log files to prevent disk space issues

## 📁 Project Structure

```
k_online_scraper/
├── main.py                 # Main CLI interface
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── scraper/
│   ├── __init__.py
│   ├── k_online_scraper.py # Core scraping logic
│   └── domain_generator.py # Domain generation
├── utils/
│   ├── __init__.py
│   ├── data_exporter.py    # Export functionality
│   └── validators.py       # Data validation
└── config/
    ├── __init__.py
    └── settings.py         # Configuration settings
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   ```
   Error: ChromeDriver executable needs to be in PATH
   ```
   **Solution**: Install ChromeDriver and ensure it's in your system PATH.

2. **Website blocking requests**
   ```
   Error: HTTP 403 Forbidden
   ```
   **Solution**: Use `--use-selenium` flag or adjust user agent in settings.

3. **No companies found**
   ```
   Warning: No companies found during scraping
   ```
   **Solution**: Run `python main.py test` to check connectivity and page structure.

4. **Memory issues with large datasets**
   **Solution**: Use `--max-pages` to limit scraping scope.

### Debug Mode
Enable detailed logging:
```bash
python main.py --log-level DEBUG scrape
```

### Testing Connectivity
```bash
python main.py test
```

## 📈 Performance Tips

1. **Use appropriate delays**: Adjust `delay_between_requests` in config
2. **Limit pages for testing**: Use `--max-pages` during development
3. **Disable domain checking**: Remove `-c` flag for faster processing
4. **Use requests mode**: Avoid `--use-selenium` unless necessary

## 🤝 Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include logging for debugging
4. Update documentation for new features
5. Test with various edge cases

## 📄 License

This tool is for educational and research purposes. Ensure compliance with website terms of service and applicable laws when scraping data.

## 🔗 Dependencies

- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **selenium**: Browser automation
- **pandas**: Data manipulation
- **openpyxl**: Excel export
- **click**: CLI interface
- **tqdm**: Progress bars
- **colorama**: Colored output
- **validators**: Data validation

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Test with the demo command
4. Use debug logging for detailed information

---

**Note**: This tool is designed for legitimate business research and data analysis. Always respect website terms of service and applicable privacy laws.