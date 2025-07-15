#!/usr/bin/env python3
"""
K-Online Scraper - Main CLI Interface
Web scraping tool for K-Online company directory with domain generation.
"""
import click
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm
import colorama
from colorama import Fore, Style

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.k_online_scraper import create_scraper
from scraper.domain_generator import create_domain_generator
from utils.data_exporter import create_data_exporter
from config.settings import LOGGING_CONFIG, EXPORT_CONFIG, DOMAIN_CONFIG, SCRAPING_CONFIG

# Initialize colorama for cross-platform colored output
colorama.init()


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Set up logging configuration."""
    log_file = log_file or LOGGING_CONFIG.get('file', 'k_online_scraper.log')
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=LOGGING_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def print_banner():
    """Print application banner."""
    banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                           K-Online Scraper Tool                             ║
║                    Web Scraping & Domain Generation                         ║
║                                                                              ║
║  Extract company data from K-Online directory and generate domain variants  ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)


def print_statistics(stats: Dict[str, Any]):
    """Print scraping and processing statistics."""
    print(f"\n{Fore.GREEN}📊 Processing Statistics:{Style.RESET_ALL}")
    print(f"  • Total companies scraped: {stats.get('total_companies', 0)}")
    print(f"  • Companies with generated domains: {stats.get('companies_with_domains', 0)}")
    print(f"  • Total domains generated: {stats.get('total_domains', 0)}")
    print(f"  • Average domains per company: {stats.get('avg_domains_per_company', 0)}")
    
    if stats.get('status_distribution'):
        print(f"\n{Fore.YELLOW}🔍 Domain Status Distribution:{Style.RESET_ALL}")
        for status, count in stats['status_distribution'].items():
            print(f"  • {status.title()}: {count}")
    
    if stats.get('tld_distribution'):
        print(f"\n{Fore.BLUE}🌐 TLD Distribution:{Style.RESET_ALL}")
        for tld, count in stats['tld_distribution'].items():
            print(f"  • {tld}: {count}")


@click.group()
@click.option('--log-level', default='INFO', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
              help='Set logging level')
@click.option('--log-file', default=None, help='Log file path')
@click.pass_context
def cli(ctx, log_level, log_file):
    """K-Online Scraper - Extract company data and generate domains."""
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    ctx.obj['log_file'] = log_file
    setup_logging(log_level, log_file)


@cli.command()
@click.option('--output-format', '-f', default='csv', 
              type=click.Choice(['csv', 'json', 'excel']),
              help='Output format for exported data')
@click.option('--output-file', '-o', default=None,
              help='Output filename (without extension)')
@click.option('--max-pages', '-p', default=None, type=int,
              help='Maximum number of pages to scrape')
@click.option('--use-selenium', '-s', is_flag=True,
              help='Use Selenium for JavaScript-rendered content')
@click.option('--generate-domains', '-d', is_flag=True, default=True,
              help='Generate domain variants for companies')
@click.option('--check-availability', '-c', is_flag=True,
              help='Check domain availability (slower)')
@click.option('--max-domains', '-m', default=5, type=int,
              help='Maximum domain variants per company')
@click.pass_context
def scrape(ctx, output_format, output_file, max_pages, use_selenium, 
           generate_domains, check_availability, max_domains):
    """Scrape companies from K-Online directory and generate domains."""
    
    print_banner()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting K-Online scraping process")
    
    # Configuration
    domain_config = DOMAIN_CONFIG.copy()
    domain_config['check_domain_availability'] = check_availability
    domain_config['max_variants_per_company'] = max_domains
    
    companies = []
    
    try:
        # Initialize scraper
        with click.progressbar(length=100, label='Initializing scraper') as bar:
            scraper = create_scraper()
            bar.update(20)
            
            # Test connectivity
            test_result = scraper.test_scraping()
            bar.update(80)
            
            if not test_result['success']:
                click.echo(f"{Fore.RED}❌ Scraper test failed: {test_result.get('error')}{Style.RESET_ALL}")
                return
            
            click.echo(f"{Fore.GREEN}✅ Scraper test successful{Style.RESET_ALL}")
            click.echo(f"  • URL: {test_result['url']}")
            click.echo(f"  • Page title: {test_result['page_title']}")
            click.echo(f"  • Sample companies found: {test_result['sample_companies_found']}")
            bar.update(100)
        
        # Scrape companies
        click.echo(f"\n{Fore.YELLOW}🔍 Starting company scraping...{Style.RESET_ALL}")
        
        companies = scraper.scrape_companies(
            use_selenium=use_selenium,
            max_pages=max_pages
        )
        
        if not companies:
            click.echo(f"{Fore.RED}❌ No companies found during scraping{Style.RESET_ALL}")
            return
        
        click.echo(f"{Fore.GREEN}✅ Successfully scraped {len(companies)} companies{Style.RESET_ALL}")
        
        # Generate domains if requested
        if generate_domains:
            click.echo(f"\n{Fore.YELLOW}🌐 Generating domain variants...{Style.RESET_ALL}")
            
            domain_generator = create_domain_generator(domain_config)
            
            with tqdm(total=len(companies), desc="Processing companies") as pbar:
                processed_companies = []
                for company in companies:
                    # Generate domains for single company
                    result = domain_generator.process_companies([company])
                    if result:
                        processed_companies.extend(result)
                    pbar.update(1)
            
            companies = processed_companies
            
            # Get domain statistics
            stats = domain_generator.get_domain_statistics(companies)
            print_statistics(stats)
        
        # Export data
        click.echo(f"\n{Fore.YELLOW}💾 Exporting data...{Style.RESET_ALL}")
        
        exporter = create_data_exporter()
        output_path = exporter.export(companies, output_format, output_file)
        
        click.echo(f"{Fore.GREEN}✅ Data exported successfully to: {output_path}{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}⏹️  Scraping interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
    finally:
        # Cleanup
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.pass_context
def test(ctx):
    """Test the scraper connectivity and basic functionality."""
    
    print_banner()
    
    logger = logging.getLogger(__name__)
    logger.info("Running scraper test")
    
    try:
        scraper = create_scraper()
        
        with click.progressbar(length=100, label='Testing scraper') as bar:
            # Test basic connectivity
            test_result = scraper.test_scraping()
            bar.update(100)
        
        if test_result['success']:
            click.echo(f"\n{Fore.GREEN}✅ Scraper test successful!{Style.RESET_ALL}")
            click.echo(f"  • URL: {test_result['url']}")
            click.echo(f"  • Status Code: {test_result['status_code']}")
            click.echo(f"  • Page Title: {test_result['page_title']}")
            click.echo(f"  • Content Type: {test_result['content_type']}")
            click.echo(f"  • Page Size: {test_result['page_size']} bytes")
            click.echo(f"  • Sample Companies Found: {test_result['sample_companies_found']}")
            
            if test_result['sample_companies']:
                click.echo(f"\n{Fore.CYAN}📋 Sample Companies:{Style.RESET_ALL}")
                for i, company in enumerate(test_result['sample_companies'], 1):
                    click.echo(f"  {i}. {company.get('company_name', 'Unknown')}")
                    if company.get('city'):
                        click.echo(f"     City: {company['city']}")
        else:
            click.echo(f"\n{Fore.RED}❌ Scraper test failed!{Style.RESET_ALL}")
            click.echo(f"  Error: {test_result.get('error', 'Unknown error')}")
            click.echo(f"  URL: {test_result.get('url', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        click.echo(f"{Fore.RED}❌ Test failed with error: {e}{Style.RESET_ALL}")
    finally:
        if 'scraper' in locals():
            scraper.close()


@cli.command()
@click.argument('company_name')
@click.option('--tlds', '-t', multiple=True, default=['.de', '.com'],
              help='TLD variants to generate')
@click.option('--check-availability', '-c', is_flag=True,
              help='Check domain availability')
def generate_domains(company_name, tlds, check_availability):
    """Generate domain variants for a specific company name."""
    
    logger = logging.getLogger(__name__)
    
    domain_config = DOMAIN_CONFIG.copy()
    domain_config['tlds'] = list(tlds)
    domain_config['check_domain_availability'] = check_availability
    
    try:
        generator = create_domain_generator(domain_config)
        
        click.echo(f"\n{Fore.CYAN}🌐 Generating domains for: {company_name}{Style.RESET_ALL}")
        
        domains = generator.generate_full_domains(company_name)
        
        if domains:
            click.echo(f"\n{Fore.GREEN}Generated {len(domains)} domain variants:{Style.RESET_ALL}")
            for domain in domains:
                status_color = Fore.GREEN if domain['status'] == 'available' else Fore.RED if domain['status'] == 'taken' else Fore.YELLOW
                click.echo(f"  • {domain['domain']} ({status_color}{domain['status']}{Style.RESET_ALL})")
        else:
            click.echo(f"{Fore.RED}❌ No domains could be generated{Style.RESET_ALL}")
            
    except Exception as e:
        logger.error(f"Error generating domains: {e}")
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.option('--format', '-f', 'format_type', default='csv',
              type=click.Choice(['csv', 'json', 'excel']),
              help='Output format')
def demo(format_type):
    """Run a demonstration with sample data."""
    
    print_banner()
    
    logger = logging.getLogger(__name__)
    
    # Sample company data
    sample_companies = [
        {
            'company_name': 'Mustermann GmbH',
            'city': 'Berlin',
            'country': 'Deutschland',
            'industry': 'Maschinenbau'
        },
        {
            'company_name': 'Schneider & Partner AG',
            'city': 'München',
            'country': 'Deutschland',
            'industry': 'Consulting'
        },
        {
            'company_name': 'Tech Solutions Ltd.',
            'city': 'Hamburg',
            'country': 'Deutschland',
            'industry': 'Software'
        }
    ]
    
    try:
        click.echo(f"{Fore.YELLOW}🔄 Processing sample companies...{Style.RESET_ALL}")
        
        # Generate domains
        generator = create_domain_generator()
        processed_companies = generator.process_companies(sample_companies)
        
        # Get statistics
        stats = generator.get_domain_statistics(processed_companies)
        print_statistics(stats)
        
        # Export data
        click.echo(f"\n{Fore.YELLOW}💾 Exporting demo data...{Style.RESET_ALL}")
        
        exporter = create_data_exporter()
        output_path = exporter.export(processed_companies, format_type, 'demo_data')
        
        click.echo(f"{Fore.GREEN}✅ Demo data exported to: {output_path}{Style.RESET_ALL}")
        
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        click.echo(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    cli()