"""
Configuration settings for the K-Online scraper.
"""
import os
from typing import List, Dict, Any

# Base URL for K-Online directory
K_ONLINE_BASE_URL = "https://www.k-online.de/vis/v1/de/directory/a"

# Scraping settings
SCRAPING_CONFIG = {
    "request_timeout": 30,
    "retry_attempts": 3,
    "delay_between_requests": 1.0,  # seconds
    "max_concurrent_requests": 5,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Selenium settings
SELENIUM_CONFIG = {
    "implicit_wait": 10,
    "page_load_timeout": 30,
    "headless": True,
    "window_size": (1920, 1080)
}

# Domain generation settings
DOMAIN_CONFIG = {
    "tlds": [".de", ".com", ".org", ".net", ".eu", ".at", ".ch"],
    "max_variants_per_company": 5,
    "check_domain_availability": False,  # Set to True for DNS lookup
    "timeout_dns_check": 5
}

# Export settings
EXPORT_CONFIG = {
    "default_format": "csv",
    "output_directory": "output",
    "filename_prefix": "k_online_companies",
    "include_timestamp": True
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "k_online_scraper.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# Fields to extract from company listings
COMPANY_FIELDS = [
    "company_name",
    "address",
    "city",
    "country",
    "postal_code",
    "phone",
    "email",
    "website",
    "description",
    "industry",
    "booth_number",
    "contact_person"
]

# Output fields for export
OUTPUT_FIELDS = [
    "company_name",
    "address",
    "city", 
    "country",
    "postal_code",
    "phone",
    "email",
    "original_website",
    "generated_domains",
    "domain_status",
    "source_url",
    "scrape_timestamp"
]

def get_output_directory() -> str:
    """Get the output directory path, create if it doesn't exist."""
    output_dir = EXPORT_CONFIG["output_directory"]
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def get_headers() -> Dict[str, str]:
    """Get HTTP headers for requests."""
    return {
        "User-Agent": SCRAPING_CONFIG["user_agent"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }