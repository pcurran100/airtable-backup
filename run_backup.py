#!/usr/bin/env python3
"""
Airtable Backup Launcher

A simple launcher script that provides options for running the backup.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description='Airtable Backup Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_backup.py                    # Run backup with default settings
  python3 run_backup.py --test             # Run tests only
  python3 run_backup.py --output /path/to/backup  # Custom output directory
  python3 run_backup.py --dry-run          # Show what would be backed up
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run tests only (no backup)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Custom output directory for backup'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be backed up without actually doing it'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    if args.test:
        print("Running tests...")
        from test_backup import main as run_tests
        success = run_tests()
        sys.exit(0 if success else 1)
    
    if args.dry_run:
        print("DRY RUN MODE - No backup will be performed")
        print("=" * 50)
        
        try:
            from airtable_backup_improved import headers, API_META_URL
            import requests
            
            response = requests.get(f'{API_META_URL}/bases', headers=headers)
            response.raise_for_status()
            bases = response.json()['bases']
            
            print(f"Found {len(bases)} accessible bases:")
            for base in bases:
                print(f"  - {base['name']} ({base['id']})")
                
                # Get tables for this base
                try:
                    tables_response = requests.get(
                        f'{API_META_URL}/bases/{base["id"]}/tables', 
                        headers=headers
                    )
                    tables_response.raise_for_status()
                    tables = tables_response.json().get('tables', [])
                    print(f"    Tables: {len(tables)}")
                    for table in tables[:3]:  # Show first 3 tables
                        print(f"      - {table['name']}")
                    if len(tables) > 3:
                        print(f"      ... and {len(tables) - 3} more")
                except Exception as e:
                    print(f"    Error fetching tables: {e}")
                    
            default_output = f"airtable_backup_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
            print(f"\nBackup would be saved to: {args.output or default_output}")
            print("Formats: JSON, YAML, NDJSON, CSV, SQLite, Parquet")
            
        except Exception as e:
            print(f"Error during dry run: {e}")
            sys.exit(1)
            
        return
    
    # Run the actual backup
    try:
        from airtable_backup_improved import AirtableBackup
        
        print("Starting Airtable backup...")
        print("=" * 50)
        
        backup = AirtableBackup(output_dir=args.output)
        backup.backup_workspace()
        
        print("\n" + "=" * 50)
        print("Backup completed successfully!")
        print(f"Output directory: {backup.output_dir}")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\nBackup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Backup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 