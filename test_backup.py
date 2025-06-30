#!/usr/bin/env python3
"""
Test script for Airtable Backup functionality

This script tests the basic functionality without performing a full backup.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from airtable_backup_improved import AirtableBackup
import requests

def test_api_connection():
    """Test the Airtable API connection."""
    print("Testing Airtable API connection...")
    
    from airtable_backup_improved import headers, API_META_URL
    
    try:
        response = requests.get(f'{API_META_URL}/bases', headers=headers)
        response.raise_for_status()
        
        bases = response.json()['bases']
        print(f"✓ API connection successful")
        print(f"✓ Found {len(bases)} accessible bases")
        
        for base in bases[:3]:  # Show first 3 bases
            print(f"  - {base['name']} ({base['id']})")
            
        if len(bases) > 3:
            print(f"  ... and {len(bases) - 3} more bases")
            
        return True
        
    except Exception as e:
        print(f"✗ API connection failed: {e}")
        return False

def test_directory_creation():
    """Test directory creation functionality."""
    print("\nTesting directory creation...")
    
    try:
        test_backup = AirtableBackup(output_dir="test_backup")
        
        # Check if directories were created
        expected_dirs = [
            'data', 'data/json', 'data/yaml', 'data/ndjson', 
            'data/csv', 'data/sqlite', 'data/parquet',
            'attachments', 'logs', 'metadata', 'reports'
        ]
        
        for dir_name in expected_dirs:
            dir_path = test_backup.output_dir / dir_name
            if dir_path.exists():
                print(f"✓ Created directory: {dir_name}")
            else:
                print(f"✗ Failed to create directory: {dir_name}")
                return False
                
        # Clean up test directory
        import shutil
        shutil.rmtree(test_backup.output_dir)
        print("✓ Test directory cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Directory creation test failed: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available."""
    print("\nTesting dependencies...")
    
    dependencies = {
        'requests': 'HTTP requests',
        'yaml': 'YAML processing',
        'sqlite3': 'SQLite database',
        'pathlib': 'Path handling',
        'logging': 'Logging functionality'
    }
    
    optional_dependencies = {
        'pandas': 'Parquet support',
        'sqlite_utils': 'Enhanced SQLite operations'
    }
    
    all_good = True
    
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError:
            print(f"✗ {module}: {description} - MISSING")
            all_good = False
            
    print("\nOptional dependencies:")
    for module, description in optional_dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError:
            print(f"⚠ {module}: {description} - Not available (will use fallback)")
            
    return all_good

def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from config import AIRTABLE_API_TOKEN, API_BASE_URL
        
        if AIRTABLE_API_TOKEN and AIRTABLE_API_TOKEN != 'your_api_token_here':
            print("✓ API token configured")
        else:
            print("✗ API token not configured")
            return False
            
        print(f"✓ API base URL: {API_BASE_URL}")
        return True
        
    except ImportError:
        print("✗ Configuration file not found")
        return False
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Airtable Backup Test Suite")
    print("=" * 40)
    
    tests = [
        ("Configuration", test_configuration),
        ("Dependencies", test_dependencies),
        ("Directory Creation", test_directory_creation),
        ("API Connection", test_api_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name} Test:")
        print("-" * 20)
        
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} test PASSED")
            else:
                print(f"✗ {test_name} test FAILED")
        except Exception as e:
            print(f"✗ {test_name} test ERROR: {e}")
            
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The backup script should work correctly.")
        print("\nTo run a full backup:")
        print("  python airtable_backup_improved.py")
    else:
        print("⚠ Some tests failed. Please fix the issues before running a backup.")
        
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 