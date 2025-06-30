"""
Configuration file for Airtable Backup Script

Modify these settings to customize your backup behavior.
"""

# Airtable API Configuration
AIRTABLE_API_TOKEN = 'patTKf0uBAXQwq1L3.9f3c5fbf4fa8a3420afeb43c0e0b63c8a13d88162091e36a91ae3beffae5146d'
API_BASE_URL = 'https://api.airtable.com/v0'
API_META_URL = 'https://api.airtable.com/v0/meta'

# Backup Configuration
DEFAULT_OUTPUT_DIR = None  # None = auto-generate timestamped directory
INCLUDE_ATTACHMENTS = True
DOWNLOAD_EXISTING_ATTACHMENTS = False  # Skip if attachment already exists

# Output Format Configuration
ENABLE_JSON = True
ENABLE_YAML = True
ENABLE_NDJSON = True
ENABLE_CSV = True
ENABLE_SQLITE = True
ENABLE_PARQUET = True

# Performance Configuration
API_REQUEST_DELAY = 0.1  # Seconds between API requests
CHUNK_SIZE = 8192  # Bytes for file downloads
MAX_RETRIES = 3  # Maximum retry attempts for failed requests

# Logging Configuration
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# Error Handling
CONTINUE_ON_ERROR = True  # Continue processing other tables if one fails
SAVE_PARTIAL_DATA = True  # Save data even if some records fail

# File Naming
USE_SAFE_FILENAMES = True  # Remove special characters from filenames
MAX_FILENAME_LENGTH = 100  # Maximum length for generated filenames

# Database Configuration (SQLite)
SQLITE_TIMEOUT = 30  # Seconds
SQLITE_ISOLATION_LEVEL = None  # None = autocommit mode

# CSV Configuration
CSV_ENCODING = 'utf-8'
CSV_DELIMITER = ','
CSV_QUOTING = 'minimal'  # csv.QUOTE_MINIMAL

# YAML Configuration
YAML_DEFAULT_FLOW_STYLE = False
YAML_ALLOW_UNICODE = True 