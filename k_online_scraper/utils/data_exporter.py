"""
Data export utilities for K-Online scraper.
Supports CSV, JSON, and Excel formats.
"""
import json
import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
from config.settings import EXPORT_CONFIG, OUTPUT_FIELDS, get_output_directory
from utils.validators import sanitize_filename, validate_export_format


class DataExporter:
    """Handle data export in multiple formats."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize data exporter with configuration."""
        self.config = config or EXPORT_CONFIG
        self.logger = logging.getLogger(__name__)
        self.output_dir = get_output_directory()
        
    def _generate_filename(self, format_type: str, custom_name: str = None) -> str:
        """Generate filename for export."""
        if custom_name:
            base_name = sanitize_filename(custom_name)
        else:
            base_name = self.config.get('filename_prefix', 'k_online_companies')
        
        if self.config.get('include_timestamp', True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = f"{base_name}_{timestamp}"
        
        # Add appropriate extension
        extensions = {
            'csv': '.csv',
            'json': '.json',
            'excel': '.xlsx',
            'xlsx': '.xlsx'
        }
        
        extension = extensions.get(format_type.lower(), '.csv')
        return f"{base_name}{extension}"
    
    def _prepare_data_for_export(self, companies: List[Dict[str, Any]], 
                                 fields: List[str] = None) -> List[Dict[str, Any]]:
        """Prepare company data for export by flattening and selecting fields."""
        if not fields:
            fields = OUTPUT_FIELDS
        
        export_data = []
        
        for company in companies:
            row = {}
            
            for field in fields:
                if field == 'generated_domains':
                    # Flatten domains into a readable format
                    domains = company.get('generated_domains', [])
                    domain_strings = [f"{d['domain']} ({d['status']})" for d in domains]
                    row[field] = '; '.join(domain_strings)
                elif field == 'domain_status':
                    # Create summary of domain statuses
                    domains = company.get('generated_domains', [])
                    status_summary = {}
                    for domain in domains:
                        status = domain['status']
                        status_summary[status] = status_summary.get(status, 0) + 1
                    row[field] = ', '.join([f"{k}: {v}" for k, v in status_summary.items()])
                elif field == 'scrape_timestamp':
                    row[field] = datetime.now().isoformat()
                elif field == 'source_url':
                    row[field] = company.get('source_url', 'https://www.k-online.de/vis/v1/de/directory/a')
                else:
                    row[field] = company.get(field, '')
            
            export_data.append(row)
        
        return export_data
    
    def export_to_csv(self, companies: List[Dict[str, Any]], 
                     filename: str = None, fields: List[str] = None) -> str:
        """Export companies data to CSV format."""
        if not validate_export_format('csv'):
            raise ValueError("CSV format not supported")
        
        filename = filename or self._generate_filename('csv')
        filepath = os.path.join(self.output_dir, filename)
        
        export_data = self._prepare_data_for_export(companies, fields)
        
        if not export_data:
            self.logger.warning("No data to export")
            return filepath
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(export_data[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(export_data)
                
            self.logger.info(f"Successfully exported {len(export_data)} companies to CSV: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_to_json(self, companies: List[Dict[str, Any]], 
                      filename: str = None, fields: List[str] = None) -> str:
        """Export companies data to JSON format."""
        if not validate_export_format('json'):
            raise ValueError("JSON format not supported")
        
        filename = filename or self._generate_filename('json')
        filepath = os.path.join(self.output_dir, filename)
        
        # For JSON, we can keep the full structure
        export_data = []
        for company in companies:
            if fields:
                # Filter fields if specified
                filtered_company = {field: company.get(field, '') for field in fields}
            else:
                filtered_company = company.copy()
            
            # Add metadata
            filtered_company['scrape_timestamp'] = datetime.now().isoformat()
            filtered_company['source_url'] = company.get('source_url', 'https://www.k-online.de/vis/v1/de/directory/a')
            
            export_data.append(filtered_company)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump({
                    'metadata': {
                        'export_timestamp': datetime.now().isoformat(),
                        'total_companies': len(export_data),
                        'fields': fields or list(companies[0].keys()) if companies else []
                    },
                    'companies': export_data
                }, jsonfile, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Successfully exported {len(export_data)} companies to JSON: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def export_to_excel(self, companies: List[Dict[str, Any]], 
                       filename: str = None, fields: List[str] = None) -> str:
        """Export companies data to Excel format."""
        if not validate_export_format('excel'):
            raise ValueError("Excel format not supported")
        
        filename = filename or self._generate_filename('excel')
        filepath = os.path.join(self.output_dir, filename)
        
        export_data = self._prepare_data_for_export(companies, fields)
        
        if not export_data:
            self.logger.warning("No data to export")
            return filepath
        
        try:
            # Create DataFrame
            df = pd.DataFrame(export_data)
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Companies', index=False)
                
                # Statistics sheet
                stats_data = self._generate_export_statistics(companies)
                if stats_data:
                    stats_df = pd.DataFrame(list(stats_data.items()), columns=['Metric', 'Value'])
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                # Domain details sheet (if domains exist)
                domain_details = self._prepare_domain_details(companies)
                if domain_details:
                    domain_df = pd.DataFrame(domain_details)
                    domain_df.to_excel(writer, sheet_name='Domain_Details', index=False)
            
            self.logger.info(f"Successfully exported {len(export_data)} companies to Excel: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            raise
    
    def _prepare_domain_details(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare detailed domain information for export."""
        domain_details = []
        
        for company in companies:
            company_name = company.get('company_name', '')
            domains = company.get('generated_domains', [])
            
            for domain in domains:
                detail = {
                    'company_name': company_name,
                    'domain': domain.get('domain', ''),
                    'variant': domain.get('variant', ''),
                    'tld': domain.get('tld', ''),
                    'status': domain.get('status', ''),
                }
                domain_details.append(detail)
        
        return domain_details
    
    def _generate_export_statistics(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics about the exported data."""
        if not companies:
            return {}
        
        total_companies = len(companies)
        companies_with_domains = sum(1 for c in companies if c.get('generated_domains'))
        total_domains = sum(len(c.get('generated_domains', [])) for c in companies)
        
        # Domain status statistics
        status_counts = {}
        for company in companies:
            for domain in company.get('generated_domains', []):
                status = domain.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'Total Companies': total_companies,
            'Companies with Domains': companies_with_domains,
            'Total Generated Domains': total_domains,
            'Average Domains per Company': round(total_domains / total_companies if total_companies > 0 else 0, 2),
            **{f'Domains {status.title()}': count for status, count in status_counts.items()}
        }
    
    def export(self, companies: List[Dict[str, Any]], format_type: str = None, 
              filename: str = None, fields: List[str] = None) -> str:
        """Export data in the specified format."""
        format_type = format_type or self.config.get('default_format', 'csv')
        format_type = format_type.lower()
        
        if format_type == 'csv':
            return self.export_to_csv(companies, filename, fields)
        elif format_type == 'json':
            return self.export_to_json(companies, filename, fields)
        elif format_type in ['excel', 'xlsx']:
            return self.export_to_excel(companies, filename, fields)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


def create_data_exporter(config: Dict[str, Any] = None) -> DataExporter:
    """Factory function to create data exporter instance."""
    return DataExporter(config)