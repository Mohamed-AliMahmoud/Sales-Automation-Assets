"""
Domain generation module for K-Online scraper.
Generates potential domain names based on company names.
"""
import re
import logging
from typing import List, Dict, Set, Any
from config.settings import DOMAIN_CONFIG
from utils.validators import clean_company_name, validate_domain, check_domain_availability


class DomainGenerator:
    """Generate potential domain names from company names."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize domain generator with configuration."""
        self.config = config or DOMAIN_CONFIG
        self.logger = logging.getLogger(__name__)
        
    def generate_domain_variants(self, company_name: str) -> List[str]:
        """Generate multiple domain variants from company name."""
        if not company_name:
            return []
        
        # Clean and normalize company name
        base_name = clean_company_name(company_name)
        if not base_name:
            return []
        
        variants = set()
        
        # Basic variant (cleaned company name)
        variants.add(base_name)
        
        # Without hyphens
        no_hyphens = base_name.replace('-', '')
        if no_hyphens and no_hyphens != base_name:
            variants.add(no_hyphens)
        
        # Abbreviation (first letters of words)
        words = [word for word in base_name.split('-') if word]
        if len(words) > 1:
            abbreviation = ''.join(word[0] for word in words if word)
            if len(abbreviation) >= 2:
                variants.add(abbreviation)
        
        # Short variants (remove common words)
        short_variant = self._create_short_variant(base_name)
        if short_variant and short_variant != base_name:
            variants.add(short_variant)
        
        # Number variants (add common numbers)
        if len(variants) < self.config.get('max_variants_per_company', 5):
            for num in ['24', '365', '2024']:
                variants.add(f"{base_name}{num}")
        
        return list(variants)[:self.config.get('max_variants_per_company', 5)]
    
    def _create_short_variant(self, name: str) -> str:
        """Create a shorter variant by removing common words."""
        common_words = [
            'gmbh', 'ag', 'kg', 'ohg', 'ev', 'ek', 'ug', 'ltd', 'inc',
            'corp', 'llc', 'co', 'company', 'systems', 'solutions',
            'services', 'international', 'group', 'holding', 'consulting',
            'engineering', 'technology', 'tech', 'software', 'digital',
            'and', 'und', 'the', 'der', 'die', 'das'
        ]
        
        words = [word for word in name.split('-') if word.lower() not in common_words]
        return '-'.join(words) if words else name
    
    def generate_full_domains(self, company_name: str) -> List[Dict[str, str]]:
        """Generate full domain names with TLDs and status check."""
        variants = self.generate_domain_variants(company_name)
        tlds = self.config.get('tlds', ['.de', '.com'])
        
        domains = []
        
        for variant in variants:
            for tld in tlds:
                domain = f"{variant}{tld}"
                
                # Validate domain format
                if not validate_domain(domain):
                    continue
                
                domain_info = {
                    'domain': domain,
                    'variant': variant,
                    'tld': tld,
                    'status': 'unknown'
                }
                
                # Check availability if enabled
                if self.config.get('check_domain_availability', False):
                    try:
                        status = check_domain_availability(
                            domain, 
                            self.config.get('timeout_dns_check', 5)
                        )
                        domain_info['status'] = status
                    except Exception as e:
                        self.logger.warning(f"Error checking domain {domain}: {e}")
                        domain_info['status'] = 'error'
                
                domains.append(domain_info)
        
        return domains
    
    def process_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of companies and add generated domains."""
        results = []
        
        for company in companies:
            company_name = company.get('company_name', '')
            if not company_name:
                continue
            
            # Generate domains
            domains = self.generate_full_domains(company_name)
            
            # Create result with original company data and generated domains
            result = company.copy()
            result['generated_domains'] = domains
            result['domain_count'] = len(domains)
            
            # Add summary fields
            domain_list = [d['domain'] for d in domains]
            result['domain_list'] = ', '.join(domain_list)
            
            # Domain status summary
            status_counts = {}
            for domain in domains:
                status = domain['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            result['domain_status_summary'] = status_counts
            
            results.append(result)
            
            self.logger.info(f"Generated {len(domains)} domains for: {company_name}")
        
        return results
    
    def get_domain_statistics(self, processed_companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about generated domains."""
        total_companies = len(processed_companies)
        total_domains = sum(comp.get('domain_count', 0) for comp in processed_companies)
        
        # Status distribution
        status_distribution = {}
        tld_distribution = {}
        
        for company in processed_companies:
            domains = company.get('generated_domains', [])
            for domain in domains:
                status = domain['status']
                tld = domain['tld']
                
                status_distribution[status] = status_distribution.get(status, 0) + 1
                tld_distribution[tld] = tld_distribution.get(tld, 0) + 1
        
        avg_domains_per_company = total_domains / total_companies if total_companies > 0 else 0
        
        return {
            'total_companies': total_companies,
            'total_domains': total_domains,
            'avg_domains_per_company': round(avg_domains_per_company, 2),
            'status_distribution': status_distribution,
            'tld_distribution': tld_distribution
        }


def create_domain_generator(config: Dict[str, Any] = None) -> DomainGenerator:
    """Factory function to create domain generator instance."""
    return DomainGenerator(config)