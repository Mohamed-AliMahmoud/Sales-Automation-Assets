"""
Validation utilities for the K-Online scraper.
"""
import re
import socket
import urllib.parse
from typing import Optional, List, Dict, Any
import validators as external_validators


def validate_url(url: str) -> bool:
    """Validate if a URL is properly formatted."""
    try:
        return external_validators.url(url)
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """Validate if an email address is properly formatted."""
    try:
        return external_validators.email(email)
    except Exception:
        return False


def validate_domain(domain: str) -> bool:
    """Validate if a domain name is properly formatted."""
    try:
        return external_validators.domain(domain)
    except Exception:
        return False


def clean_company_name(name: str) -> str:
    """Clean and normalize company name for domain generation."""
    if not name:
        return ""
    
    # Remove common legal suffixes
    legal_suffixes = [
        "GmbH", "AG", "KG", "OHG", "e.V.", "e.K.", "UG", "Ltd.", "Inc.", 
        "Corp.", "LLC", "Co.", "& Co.", "mbH", "gGmbH"
    ]
    
    cleaned = name
    for suffix in legal_suffixes:
        cleaned = re.sub(rf'\b{re.escape(suffix)}\b', '', cleaned, flags=re.IGNORECASE)
    
    # Remove special characters and normalize
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    cleaned = re.sub(r'\s+', '-', cleaned.strip())
    cleaned = cleaned.lower()
    
    # Replace umlauts and special characters
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c'
    }
    
    for char, replacement in replacements.items():
        cleaned = cleaned.replace(char, replacement)
    
    # Remove multiple consecutive hyphens
    cleaned = re.sub(r'-+', '-', cleaned)
    cleaned = cleaned.strip('-')
    
    return cleaned


def validate_company_data(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean company data."""
    validated_data = {}
    
    # Required field: company_name
    company_name = company_data.get('company_name', '').strip()
    if company_name:
        validated_data['company_name'] = company_name
    else:
        raise ValueError("Company name is required")
    
    # Optional fields with validation
    fields_mapping = {
        'address': str,
        'city': str,
        'country': str,
        'postal_code': str,
        'phone': str,
        'email': str,
        'website': str,
        'description': str,
        'industry': str,
        'booth_number': str,
        'contact_person': str
    }
    
    for field, field_type in fields_mapping.items():
        value = company_data.get(field, '')
        if value:
            if field == 'email' and not validate_email(value):
                continue  # Skip invalid emails
            elif field == 'website' and not validate_url(value):
                continue  # Skip invalid URLs
            else:
                validated_data[field] = field_type(value).strip()
    
    return validated_data


def check_domain_availability(domain: str, timeout: int = 5) -> str:
    """
    Check if a domain is available by performing DNS lookup.
    Returns: 'available', 'taken', 'error'
    """
    if not validate_domain(domain):
        return 'error'
    
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(domain)
        return 'taken'
    except socket.gaierror:
        return 'available'
    except Exception:
        return 'error'


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number format."""
    if not phone:
        return ""
    
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone)
    
    # Add country code if missing (assume Germany)
    if normalized and not normalized.startswith('+'):
        if normalized.startswith('0'):
            normalized = '+49' + normalized[1:]
        else:
            normalized = '+49' + normalized
    
    return normalized


def extract_postal_code(address_text: str) -> Optional[str]:
    """Extract postal code from address text."""
    if not address_text:
        return None
    
    # German postal code pattern (5 digits)
    postal_pattern = r'\b(\d{5})\b'
    match = re.search(postal_pattern, address_text)
    
    return match.group(1) if match else None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    # Remove or replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim and limit length
    sanitized = sanitized.strip('_')[:100]
    
    return sanitized


def validate_export_format(format_name: str) -> bool:
    """Validate if export format is supported."""
    supported_formats = ['csv', 'json', 'excel', 'xlsx']
    return format_name.lower() in supported_formats


def parse_address(address_text: str) -> Dict[str, str]:
    """Parse address text into components."""
    if not address_text:
        return {}
    
    result = {}
    
    # Extract postal code
    postal_code = extract_postal_code(address_text)
    if postal_code:
        result['postal_code'] = postal_code
    
    # Split address into lines
    lines = [line.strip() for line in address_text.split('\n') if line.strip()]
    
    if lines:
        result['address'] = lines[0]
        
        # Try to extract city from the line with postal code
        for line in lines:
            if postal_code and postal_code in line:
                city_part = line.replace(postal_code, '').strip()
                if city_part:
                    result['city'] = city_part
                break
    
    return result