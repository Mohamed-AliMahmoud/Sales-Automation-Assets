"""
K-Online directory web scraper.
Extracts company information from the K-Online exhibitor directory.
"""
import requests
import time
import logging
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
from config.settings import K_ONLINE_BASE_URL, SCRAPING_CONFIG, SELENIUM_CONFIG, get_headers
from utils.validators import validate_company_data, parse_address, normalize_phone_number


class KOnlineScraper:
    """Web scraper for K-Online exhibitor directory."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the scraper with configuration."""
        self.config = config or SCRAPING_CONFIG
        self.selenium_config = SELENIUM_CONFIG
        self.base_url = K_ONLINE_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        self.logger = logging.getLogger(__name__)
        self.driver = None
        
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup."""
        self.close()
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error closing WebDriver: {e}")
            self.driver = None
        
        if self.session:
            self.session.close()
    
    def _setup_selenium_driver(self) -> webdriver.Chrome:
        """Set up Selenium WebDriver with proper configuration."""
        chrome_options = Options()
        
        if self.selenium_config.get('headless', True):
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--user-agent={self.config["user_agent"]}')
        
        window_size = self.selenium_config.get('window_size', (1920, 1080))
        chrome_options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(self.selenium_config.get('implicit_wait', 10))
            driver.set_page_load_timeout(self.selenium_config.get('page_load_timeout', 30))
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium driver: {e}")
            raise
    
    def _make_request(self, url: str, retries: int = None) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        retries = retries or self.config.get('retry_attempts', 3)
        timeout = self.config.get('request_timeout', 30)
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(self.config.get('delay_between_requests', 1.0))
                else:
                    self.logger.error(f"All {retries} attempts failed for {url}")
                    return None
        
        return None
    
    def _parse_company_from_element(self, element, source_url: str = None) -> Optional[Dict[str, Any]]:
        """Parse company information from a BeautifulSoup element."""
        try:
            company_data = {}
            
            # Extract company name
            name_element = element.find(['h2', 'h3', 'h4'], class_=re.compile(r'.*name.*|.*title.*', re.I))
            if not name_element:
                name_element = element.find(['h2', 'h3', 'h4'])
            
            if name_element:
                company_data['company_name'] = name_element.get_text(strip=True)
            else:
                # Try to find name in other elements
                strong_elements = element.find_all('strong')
                for strong in strong_elements:
                    text = strong.get_text(strip=True)
                    if len(text) > 5 and not any(char.isdigit() for char in text[:5]):
                        company_data['company_name'] = text
                        break
            
            if not company_data.get('company_name'):
                return None
            
            # Extract address information
            address_text = ""
            address_elements = element.find_all(['p', 'div'], class_=re.compile(r'.*address.*|.*contact.*', re.I))
            for addr_elem in address_elements:
                addr_text = addr_elem.get_text(strip=True)
                if addr_text:
                    address_text += addr_text + "\n"
            
            if address_text:
                # Parse address components
                parsed_address = parse_address(address_text)
                company_data.update(parsed_address)
                company_data['address'] = address_text.strip()
            
            # Extract phone number
            phone_patterns = [
                r'(\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9})',
                r'(Tel\.?\s*:?\s*\+?\d[\d\s\-\(\)]{7,})',
                r'(Telefon\s*:?\s*\+?\d[\d\s\-\(\)]{7,})'
            ]
            
            text_content = element.get_text()
            for pattern in phone_patterns:
                match = re.search(pattern, text_content, re.I)
                if match:
                    phone = normalize_phone_number(match.group(1))
                    if phone:
                        company_data['phone'] = phone
                        break
            
            # Extract email
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            email_match = re.search(email_pattern, text_content)
            if email_match:
                company_data['email'] = email_match.group(1)
            
            # Extract website
            website_links = element.find_all('a', href=True)
            for link in website_links:
                href = link.get('href', '')
                if href.startswith('http') and 'k-online.de' not in href:
                    company_data['website'] = href
                    break
            
            # Extract booth number
            booth_pattern = r'(Stand|Booth|Halle)\s*:?\s*([A-Z]?\d+[A-Z]?\d*)'
            booth_match = re.search(booth_pattern, text_content, re.I)
            if booth_match:
                company_data['booth_number'] = booth_match.group(2)
            
            # Extract industry/category
            category_elements = element.find_all(['span', 'div'], class_=re.compile(r'.*category.*|.*industry.*|.*sector.*', re.I))
            for cat_elem in category_elements:
                cat_text = cat_elem.get_text(strip=True)
                if cat_text:
                    company_data['industry'] = cat_text
                    break
            
            # Add source URL
            company_data['source_url'] = source_url or self.base_url
            
            # Validate and clean the data
            return validate_company_data(company_data)
            
        except Exception as e:
            self.logger.warning(f"Error parsing company element: {e}")
            return None
    
    def _scrape_page_with_requests(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single page using requests and BeautifulSoup."""
        response = self._make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        companies = []
        
        # Common selectors for company listings
        company_selectors = [
            '.exhibitor-item',
            '.company-item',
            '.listing-item',
            '.directory-entry',
            '[class*="exhibitor"]',
            '[class*="company"]',
            '[class*="listing"]'
        ]
        
        company_elements = []
        for selector in company_selectors:
            elements = soup.select(selector)
            if elements:
                company_elements = elements
                self.logger.info(f"Found {len(elements)} company elements using selector: {selector}")
                break
        
        # Fallback: look for common patterns
        if not company_elements:
            # Try to find elements with company-like content
            all_divs = soup.find_all(['div', 'article', 'section'])
            for div in all_divs:
                text = div.get_text(strip=True)
                # Check if this might be a company listing
                if (len(text) > 50 and 
                    any(keyword in text.lower() for keyword in ['gmbh', 'ag', 'kg', 'ltd', 'inc', 'corp']) and
                    (re.search(r'\d{5}', text) or '@' in text)):  # Has postal code or email
                    company_elements.append(div)
        
        self.logger.info(f"Processing {len(company_elements)} potential company elements")
        
        for element in company_elements:
            company = self._parse_company_from_element(element, url)
            if company:
                companies.append(company)
        
        return companies
    
    def _scrape_page_with_selenium(self, url: str) -> List[Dict[str, Any]]:
        """Scrape a single page using Selenium for JavaScript-rendered content."""
        if not self.driver:
            self.driver = self._setup_selenium_driver()
        
        try:
            self.driver.get(url)
            
            # Wait for content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Use the same parsing logic as requests method
            companies = []
            company_selectors = [
                '.exhibitor-item',
                '.company-item', 
                '.listing-item',
                '.directory-entry',
                '[class*="exhibitor"]',
                '[class*="company"]',
                '[class*="listing"]'
            ]
            
            company_elements = []
            for selector in company_selectors:
                elements = soup.select(selector)
                if elements:
                    company_elements = elements
                    self.logger.info(f"Found {len(elements)} company elements using selector: {selector}")
                    break
            
            for element in company_elements:
                company = self._parse_company_from_element(element, url)
                if company:
                    companies.append(company)
            
            return companies
            
        except TimeoutException:
            self.logger.error(f"Timeout waiting for page to load: {url}")
            return []
        except WebDriverException as e:
            self.logger.error(f"WebDriver error: {e}")
            return []
    
    def _discover_pagination_urls(self, base_url: str) -> List[str]:
        """Discover pagination URLs from the main directory page."""
        urls = [base_url]
        
        try:
            response = self._make_request(base_url)
            if not response:
                return urls
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for pagination elements
            pagination_selectors = [
                '.pagination a',
                '.pager a', 
                '.page-numbers a',
                '[class*="page"] a',
                'a[href*="page"]',
                'a[href*="offset"]'
            ]
            
            page_links = set()
            for selector in pagination_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        page_links.add(full_url)
            
            if page_links:
                urls.extend(list(page_links))
                self.logger.info(f"Discovered {len(page_links)} additional pages")
            
            # Try to find "next" page pattern
            next_links = soup.find_all('a', text=re.compile(r'next|weiter|more|mehr', re.I))
            for link in next_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in urls:
                        urls.append(full_url)
            
        except Exception as e:
            self.logger.warning(f"Error discovering pagination: {e}")
        
        return urls
    
    def scrape_companies(self, use_selenium: bool = False, max_pages: int = None) -> List[Dict[str, Any]]:
        """
        Scrape companies from K-Online directory.
        
        Args:
            use_selenium: Whether to use Selenium for JavaScript-rendered content
            max_pages: Maximum number of pages to scrape (None for all)
        
        Returns:
            List of company dictionaries
        """
        self.logger.info("Starting K-Online directory scraping")
        
        # Discover all pages to scrape
        urls_to_scrape = self._discover_pagination_urls(self.base_url)
        
        if max_pages:
            urls_to_scrape = urls_to_scrape[:max_pages]
        
        self.logger.info(f"Will scrape {len(urls_to_scrape)} pages")
        
        all_companies = []
        
        for i, url in enumerate(urls_to_scrape, 1):
            self.logger.info(f"Scraping page {i}/{len(urls_to_scrape)}: {url}")
            
            try:
                if use_selenium:
                    companies = self._scrape_page_with_selenium(url)
                else:
                    companies = self._scrape_page_with_requests(url)
                
                self.logger.info(f"Found {len(companies)} companies on page {i}")
                all_companies.extend(companies)
                
                # Rate limiting
                if i < len(urls_to_scrape):
                    delay = self.config.get('delay_between_requests', 1.0)
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Error scraping page {i} ({url}): {e}")
                continue
        
        self.logger.info(f"Scraping completed. Total companies found: {len(all_companies)}")
        return all_companies
    
    def test_scraping(self) -> Dict[str, Any]:
        """Test the scraping functionality and return diagnostics."""
        self.logger.info("Running scraping test")
        
        # Test basic connectivity
        response = self._make_request(self.base_url)
        if not response:
            return {
                'success': False,
                'error': 'Could not connect to K-Online website',
                'url': self.base_url
            }
        
        # Test HTML parsing
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('title')
        
        # Try to extract some sample data
        sample_companies = self._scrape_page_with_requests(self.base_url)
        
        return {
            'success': True,
            'url': self.base_url,
            'status_code': response.status_code,
            'page_title': title.get_text(strip=True) if title else 'Unknown',
            'sample_companies_found': len(sample_companies),
            'sample_companies': sample_companies[:3] if sample_companies else [],
            'page_size': len(response.content),
            'content_type': response.headers.get('content-type', 'Unknown')
        }


def create_scraper(config: Dict[str, Any] = None) -> KOnlineScraper:
    """Factory function to create scraper instance."""
    return KOnlineScraper(config)