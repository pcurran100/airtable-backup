#!/usr/bin/env python3
"""
Airtable Backup Script - Improved Version

This script creates comprehensive backups of Airtable workspaces in multiple formats:
- JSON (structured and raw)
- YAML
- NDJSON (newline-delimited JSON)
- SQLite
- CSV (for flat data)
- Parquet (for large datasets)

Features:
- Comprehensive logging
- Progressive file writing (not just at the end)
- Better error handling
- Organized folder structure
- Attachment downloading
- Progress tracking
"""

import os
import json
import yaml
import csv
import sqlite3
import requests
import urllib.parse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
import sys

# Try to import optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: pandas not available. Parquet export will be skipped.")

try:
    import sqlite_utils
    SQLITE_UTILS_AVAILABLE = True
except ImportError:
    SQLITE_UTILS_AVAILABLE = False
    print("Warning: sqlite_utils not available. Using standard sqlite3.")

# Configuration
AIRTABLE_API_TOKEN = 'patTKf0uBAXQwq1L3.9f3c5fbf4fa8a3420afeb43c0e0b63c8a13d88162091e36a91ae3beffae5146d'
API_BASE_URL = 'https://api.airtable.com/v0'
API_META_URL = 'https://api.airtable.com/v0/meta'

# Headers for API requests
headers = {
    'Authorization': f'Bearer {AIRTABLE_API_TOKEN}',
    'Content-Type': 'application/json'
}

class AirtableBackup:
    """Main class for handling Airtable backups."""
    
    def __init__(self, output_dir: str = None):
        """Initialize the backup process."""
        self.backup_date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.output_dir = Path(output_dir) if output_dir else Path(f'airtable_backup_{self.backup_date}')
        self.setup_logging()
        self.stats = {
            'bases_processed': 0,
            'tables_processed': 0,
            'records_processed': 0,
            'attachments_downloaded': 0,
            'errors': []
        }
        
        # Create output directory structure
        self.create_directory_structure()
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        log_dir = self.output_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log filename with timestamp
        log_file = log_dir / f'backup_{self.backup_date}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting Airtable backup process")
        self.logger.info(f"Output directory: {self.output_dir}")
        
    def create_directory_structure(self):
        """Create the organized directory structure."""
        directories = [
            'data',
            'data/json',
            'data/yaml', 
            'data/ndjson',
            'data/csv',
            'data/sqlite',
            'data/parquet',
            'attachments',
            'logs',
            'metadata',
            'reports'
        ]
        
        for directory in directories:
            (self.output_dir / directory).mkdir(parents=True, exist_ok=True)
            
        self.logger.info("Directory structure created")
        
    def fetch_base_ids(self) -> Dict[str, str]:
        """Fetch all base IDs accessible by the API token."""
        try:
            self.logger.info("Fetching base information...")
            response = requests.get(f'{API_META_URL}/bases', headers=headers)
            response.raise_for_status()
            
            bases = response.json()['bases']
            base_info = {base['id']: base['name'] for base in bases}
            
            self.logger.info(f"Found {len(base_info)} bases")
            for base_id, name in base_info.items():
                self.logger.info(f"  - {name} ({base_id})")
                
            return base_info
            
        except Exception as e:
            self.logger.error(f"Error fetching base IDs: {e}")
            raise
            
    def fetch_tables(self, base_id: str) -> List[Dict]:
        """Fetch the list of tables for the given base."""
        try:
            response = requests.get(f'{API_META_URL}/bases/{base_id}/tables', headers=headers)
            response.raise_for_status()
            tables = response.json().get('tables', [])
            
            self.logger.info(f"Found {len(tables)} tables in base {base_id}")
            return tables
            
        except Exception as e:
            self.logger.error(f"Error fetching tables for base {base_id}: {e}")
            raise
            
    def fetch_records(self, base_id: str, table_name: str, table_folder: Path) -> List[Dict]:
        """Fetch all records from a table with pagination."""
        records = []
        offset = None
        page_count = 0
        
        try:
            self.logger.info(f"Fetching records from table '{table_name}'...")
            
            while True:
                page_count += 1
                encoded_table_name = urllib.parse.quote(table_name)
                fixed_table_name = encoded_table_name.replace("/", "%2F")
                
                params = {'offset': offset} if offset else {}
                response = requests.get(
                    f'{API_BASE_URL}/{base_id}/{fixed_table_name}', 
                    headers=headers, 
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                page_records = data['records']
                records.extend(page_records)
                
                self.logger.info(f"  Page {page_count}: {len(page_records)} records")
                
                # Download attachments for this page
                for record in page_records:
                    self.process_attachments(record, table_folder)
                
                # Write progressive output for this page
                self.write_progressive_output(base_id, table_name, records, page_count)
                
                offset = data.get('offset')
                if not offset:
                    break
                    
                # Small delay to be respectful to the API
                time.sleep(0.1)
                
            self.logger.info(f"Total records fetched: {len(records)}")
            return records
            
        except Exception as e:
            self.logger.error(f"Error fetching records from table '{table_name}': {e}")
            self.stats['errors'].append(f"Table {table_name}: {str(e)}")
            return records
            
    def process_attachments(self, record: Dict, table_folder: Path):
        """Process and download attachments from a record."""
        attachments_dir = table_folder / 'attachments'
        attachments_dir.mkdir(exist_ok=True)
        
        for field, value in record['fields'].items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'url' in item:
                        self.download_attachment(item['url'], attachments_dir, item.get('filename', 'attachment'))
                        
    def download_attachment(self, url: str, folder: Path, filename: str):
        """Download an attachment and save it to the specified folder."""
        try:
            # Clean filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            filepath = folder / safe_filename
            
            if not filepath.exists():  # Don't re-download if already exists
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                        
                self.stats['attachments_downloaded'] += 1
                self.logger.debug(f"Downloaded attachment: {safe_filename}")
                
        except Exception as e:
            self.logger.warning(f"Failed to download attachment {filename}: {e}")
            
    def write_progressive_output(self, base_id: str, table_name: str, records: List[Dict], page_count: int):
        """Write output files progressively as data is fetched."""
        safe_table_name = self.sanitize_filename(table_name)
        
        # Write JSON (append mode for progressive writing)
        json_file = self.output_dir / 'data' / 'json' / f'{base_id}_{safe_table_name}.json'
        with open(json_file, 'w') as f:
            json.dump(records, f, indent=2)
            
        # Write NDJSON (append mode)
        ndjson_file = self.output_dir / 'data' / 'ndjson' / f'{base_id}_{safe_table_name}.ndjson'
        with open(ndjson_file, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')
                
        # Write YAML (full rewrite each time)
        yaml_file = self.output_dir / 'data' / 'yaml' / f'{base_id}_{safe_table_name}.yaml'
        with open(yaml_file, 'w') as f:
            yaml.dump(records, f, default_flow_style=False, allow_unicode=True)
            
        # Write CSV (flattened data)
        csv_file = self.output_dir / 'data' / 'csv' / f'{base_id}_{safe_table_name}.csv'
        self.write_csv(records, csv_file)
        
        # Write SQLite
        sqlite_file = self.output_dir / 'data' / 'sqlite' / f'{base_id}.db'
        self.write_sqlite(records, sqlite_file, safe_table_name)
        
        # Write Parquet if available
        if PANDAS_AVAILABLE:
            parquet_file = self.output_dir / 'data' / 'parquet' / f'{base_id}_{safe_table_name}.parquet'
            self.write_parquet(records, parquet_file)
            
        self.logger.info(f"  Progressive output written (page {page_count})")
        
    def sanitize_filename(self, name: str) -> str:
        """Sanitize a filename/directory name by removing or replacing invalid characters."""
        # Replace forward slashes and other problematic characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        return sanitized.strip()
        
    def write_csv(self, records: List[Dict], filepath: Path):
        """Write records to CSV format (flattened)."""
        if not records:
            return
            
        # Flatten the records for CSV
        flattened_records = []
        all_fieldnames = set()  # Collect all possible fieldnames
        
        for record in records:
            flat_record = {'id': record['id']}
            for field, value in record['fields'].items():
                if isinstance(value, list):
                    # Handle lists (like attachments, linked records)
                    if value and isinstance(value[0], dict) and 'url' in value[0]:
                        # Attachments
                        flat_record[field] = '; '.join([item.get('url', '') for item in value])
                    else:
                        # Other lists
                        flat_record[field] = '; '.join([str(item) for item in value])
                else:
                    flat_record[field] = str(value) if value is not None else ''
            flattened_records.append(flat_record)
            all_fieldnames.update(flat_record.keys())
            
        if flattened_records:
            # Use all collected fieldnames, sorted for consistency
            fieldnames = sorted(list(all_fieldnames))
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_records)
                
    def write_sqlite(self, records: List[Dict], filepath: Path, table_name: str):
        """Write records to SQLite database."""
        if not records:
            return
            
        try:
            # Sanitize table name for SQLite (remove special characters)
            safe_table_name = "".join(c for c in table_name if c.isalnum() or c == '_').strip()
            if not safe_table_name or safe_table_name[0].isdigit():
                safe_table_name = f"table_{safe_table_name}"
            
            if SQLITE_UTILS_AVAILABLE:
                # Use sqlite_utils for better handling
                db = sqlite_utils.Database(str(filepath))
                processed_records = []
                
                for record in records:
                    fields = record['fields'].copy()
                    fields['id'] = record['id']
                    
                    # Process attachment fields
                    for field, value in fields.items():
                        if isinstance(value, list):
                            attachment_urls = [
                                attachment['url'] for attachment in value 
                                if isinstance(attachment, dict) and 'url' in attachment
                            ]
                            fields[field] = ", ".join(attachment_urls) if attachment_urls else str(value)
                            
                    processed_records.append(fields)
                    
                db[safe_table_name].upsert_all(processed_records, pk='id', alter=True)
            else:
                # Fallback to standard sqlite3
                conn = sqlite3.connect(str(filepath))
                cursor = conn.cursor()
                
                # Collect all possible fieldnames from all records
                all_fieldnames = set()
                for record in records:
                    all_fieldnames.update(record['fields'].keys())
                
                # Create table if not exists with all possible fields
                if records:
                    columns = ['id TEXT PRIMARY KEY'] + [f'{field} TEXT' for field in sorted(all_fieldnames)]
                    create_sql = f"CREATE TABLE IF NOT EXISTS {safe_table_name} ({', '.join(columns)})"
                    cursor.execute(create_sql)
                    
                    # Insert records
                    for record in records:
                        fields = record['fields'].copy()
                        fields['id'] = record['id']
                        
                        # Ensure all fields are present (fill missing with None)
                        for field in all_fieldnames:
                            if field not in fields:
                                fields[field] = None
                        
                        placeholders = ', '.join(['?' for _ in fields])
                        columns = ', '.join(fields.keys())
                        values = list(fields.values())
                        
                        cursor.execute(f"INSERT OR REPLACE INTO {safe_table_name} ({columns}) VALUES ({placeholders})", values)
                        
                conn.commit()
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error writing to SQLite: {e}")
            
    def write_parquet(self, records: List[Dict], filepath: Path):
        """Write records to Parquet format."""
        if not PANDAS_AVAILABLE or not records:
            return
            
        try:
            # Convert to DataFrame
            df_data = []
            for record in records:
                row = {'id': record['id']}
                for field, value in record['fields'].items():
                    if isinstance(value, list):
                        row[field] = str(value)  # Convert lists to strings
                    else:
                        row[field] = value
                df_data.append(row)
                
            df = pd.DataFrame(df_data)
            df.to_parquet(filepath, index=False)
            
        except Exception as e:
            self.logger.error(f"Error writing to Parquet: {e}")
            
    def save_name_mapping(self, base_info: Dict[str, str]):
        """Save a mapping of original names to sanitized names for reference."""
        mapping = {
            'backup_date': self.backup_date,
            'bases': {},
            'tables': {}
        }
        
        # Map base names
        for base_id, base_name in base_info.items():
            safe_base_name = self.sanitize_filename(base_name)
            mapping['bases'][base_id] = {
                'original_name': base_name,
                'sanitized_name': safe_base_name
            }
            
            # Map table names for this base
            try:
                tables = self.fetch_tables(base_id)
                for table in tables:
                    table_name = table['name']
                    safe_table_name = self.sanitize_filename(table_name)
                    mapping['tables'][f"{base_id}_{table_name}"] = {
                        'base_id': base_id,
                        'base_name': base_name,
                        'original_name': table_name,
                        'sanitized_name': safe_table_name
                    }
            except Exception as e:
                self.logger.warning(f"Could not fetch tables for base {base_name}: {e}")
        
        # Save mapping as JSON
        mapping_file = self.output_dir / 'metadata' / 'name_mapping.json'
        with open(mapping_file, 'w') as f:
            json.dump(mapping, f, indent=2)
            
        self.logger.info("Name mapping saved")
        
    def save_metadata(self, base_info: Dict[str, str]):
        """Save metadata about the backup."""
        metadata = {
            'backup_date': self.backup_date,
            'bases': base_info,
            'statistics': self.stats,
            'formats': ['json', 'yaml', 'ndjson', 'csv', 'sqlite'] + (['parquet'] if PANDAS_AVAILABLE else [])
        }
        
        # Save as JSON
        metadata_file = self.output_dir / 'metadata' / 'backup_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Save as YAML
        metadata_yaml = self.output_dir / 'metadata' / 'backup_metadata.yaml'
        with open(metadata_yaml, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
            
        # Save name mapping
        self.save_name_mapping(base_info)
            
        self.logger.info("Metadata saved")
        
    def generate_report(self):
        """Generate a summary report."""
        report = f"""
Airtable Backup Report
=====================

Backup Date: {self.backup_date}
Output Directory: {self.output_dir}

Statistics:
- Bases Processed: {self.stats['bases_processed']}
- Tables Processed: {self.stats['tables_processed']}
- Records Processed: {self.stats['records_processed']}
- Attachments Downloaded: {self.stats['attachments_downloaded']}
- Errors: {len(self.stats['errors'])}

Output Formats:
- JSON: {self.output_dir}/data/json/
- YAML: {self.output_dir}/data/yaml/
- NDJSON: {self.output_dir}/data/ndjson/
- CSV: {self.output_dir}/data/csv/
- SQLite: {self.output_dir}/data/sqlite/
- Parquet: {self.output_dir}/data/parquet/ (if pandas available)

Attachments: {self.output_dir}/attachments/
Logs: {self.output_dir}/logs/
Metadata: {self.output_dir}/metadata/

"""
        
        if self.stats['errors']:
            report += "\nErrors:\n"
            for error in self.stats['errors']:
                report += f"- {error}\n"
                
        report_file = self.output_dir / 'reports' / 'backup_report.txt'
        with open(report_file, 'w') as f:
            f.write(report)
            
        self.logger.info("Backup report generated")
        
    def backup_workspace(self):
        """Perform the complete backup of the Airtable workspace."""
        try:
            self.logger.info("Starting Airtable workspace backup...")
            
            # Fetch all bases
            base_info = self.fetch_base_ids()
            
            # Process each base
            for base_id, base_name in base_info.items():
                self.logger.info(f"\nProcessing base: {base_name} ({base_id})")
                
                # Create base-specific directories (sanitize base name)
                safe_base_name = self.sanitize_filename(base_name)
                base_folder = self.output_dir / 'data' / 'json' / safe_base_name
                base_folder.mkdir(parents=True, exist_ok=True)
                
                # Save base ID file
                id_file = base_folder / f"{base_id}.txt"
                with open(id_file, 'w') as f:
                    f.write(base_id)
                    
                # Fetch and process tables
                tables = self.fetch_tables(base_id)
                for table in tables:
                    table_name = table['name']
                    self.logger.info(f"\nProcessing table: {table_name}")
                    
                    # Create table folder (sanitize table name)
                    safe_table_name = self.sanitize_filename(table_name)
                    table_folder = base_folder / safe_table_name
                    table_folder.mkdir(exist_ok=True)
                    
                    # Fetch records
                    records = self.fetch_records(base_id, table_name, table_folder)
                    
                    # Update statistics
                    self.stats['records_processed'] += len(records)
                    self.stats['tables_processed'] += 1
                    
                    self.logger.info(f"Completed table: {table_name} ({len(records)} records)")
                    
                self.stats['bases_processed'] += 1
                self.logger.info(f"Completed base: {base_name}")
                
            # Save metadata and generate report
            self.save_metadata(base_info)
            self.generate_report()
            
            self.logger.info("\n" + "="*50)
            self.logger.info("BACKUP COMPLETED SUCCESSFULLY!")
            self.logger.info(f"Total records processed: {self.stats['records_processed']}")
            self.logger.info(f"Total attachments downloaded: {self.stats['attachments_downloaded']}")
            self.logger.info(f"Output directory: {self.output_dir}")
            self.logger.info("="*50)
            
        except KeyboardInterrupt:
            self.logger.warning("Backup interrupted by user")
            self.generate_report()
            raise
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            self.generate_report()
            raise

def main():
    """Main entry point."""
    try:
        backup = AirtableBackup()
        backup.backup_workspace()
    except KeyboardInterrupt:
        print("\nBackup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 