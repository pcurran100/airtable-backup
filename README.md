# Airtable Backup Script - Improved Version

A comprehensive Python script for backing up entire Airtable workspaces in multiple formats with robust error handling, logging, and progressive output.

## Features

- **Multiple Output Formats**: JSON, YAML, NDJSON, CSV, SQLite, and Parquet
- **Progressive Writing**: Files are written throughout the process, not just at the end
- **Comprehensive Logging**: Detailed logs of all operations
- **Attachment Downloading**: Automatically downloads file attachments
- **Organized Structure**: Clean, hierarchical folder organization
- **Error Handling**: Robust error handling with detailed error reporting
- **Progress Tracking**: Real-time progress updates
- **Metadata & Reports**: Automatic generation of backup metadata and reports

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Update the `AIRTABLE_API_TOKEN` in `airtable_backup_improved.py` with your Airtable API token
2. The API token should have access to all bases you want to backup

## Usage

### Basic Usage
```bash
python airtable_backup_improved.py
```

### Custom Output Directory
```python
from airtable_backup_improved import AirtableBackup

backup = AirtableBackup(output_dir="/path/to/custom/backup/directory")
backup.backup_workspace()
```

## Output Structure

The script creates a timestamped backup directory with the following structure:

```
airtable_backup_YYYY-MM-DD_HH-MM-SS/
├── data/
│   ├── json/           # JSON format files
│   ├── yaml/           # YAML format files
│   ├── ndjson/         # Newline-delimited JSON files
│   ├── csv/            # CSV format files (flattened)
│   ├── sqlite/         # SQLite database files
│   └── parquet/        # Parquet format files (if pandas available)
├── attachments/        # Downloaded file attachments
├── logs/              # Detailed operation logs
├── metadata/          # Backup metadata and configuration
└── reports/           # Summary reports
```

## File Formats

### JSON
- Raw Airtable record format
- Preserves all field types and structures
- Good for data analysis and processing

### YAML
- Human-readable format
- Good for configuration and documentation
- Preserves data structure

### NDJSON (Newline-delimited JSON)
- One JSON object per line
- Good for streaming and processing large datasets
- Easy to parse line by line

### CSV
- Flattened data format
- Good for spreadsheet applications
- Lists and complex fields are converted to strings

### SQLite
- Relational database format
- Good for querying and analysis
- Supports SQL operations

### Parquet
- Columnar storage format
- Excellent for large datasets
- Good compression and query performance

## Logging

The script provides comprehensive logging:

- **Console Output**: Real-time progress updates
- **Log Files**: Detailed logs saved to `logs/backup_YYYY-MM-DD_HH-MM-SS.log`
- **Log Levels**: INFO, WARNING, ERROR, DEBUG

## Error Handling

- **Graceful Degradation**: Continues processing even if individual tables fail
- **Error Collection**: All errors are collected and reported
- **Partial Backups**: Partial data is preserved even if the process is interrupted
- **Retry Logic**: Built-in retry mechanisms for transient failures

## Progress Tracking

The script provides real-time feedback:

- Base processing progress
- Table processing progress
- Record count updates
- Attachment download progress
- Error reporting

## Metadata and Reports

### Metadata Files
- `metadata/backup_metadata.json`: Complete backup information
- `metadata/backup_metadata.yaml`: YAML version of metadata

### Reports
- `reports/backup_report.txt`: Human-readable summary report

## Interruption Handling

The script handles interruptions gracefully:

- **Keyboard Interrupt (Ctrl+C)**: Saves current progress and generates report
- **Process Termination**: Partial data is preserved
- **Network Issues**: Retries with exponential backoff

## Performance Considerations

- **API Rate Limiting**: Built-in delays to respect Airtable API limits
- **Memory Usage**: Progressive writing prevents memory buildup
- **Disk Space**: Monitor available disk space for large backups
- **Network**: Stable internet connection recommended

## Troubleshooting

### Common Issues

1. **API Token Issues**
   - Verify your API token is correct
   - Ensure the token has necessary permissions

2. **Network Errors**
   - Check internet connection
   - Verify Airtable API accessibility

3. **Disk Space**
   - Monitor available disk space
   - Large attachments can consume significant space

4. **Permission Errors**
   - Ensure write permissions in output directory
   - Check file system permissions

### Debug Mode

To enable debug logging, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Dependencies

- **requests**: HTTP requests to Airtable API
- **PyYAML**: YAML file handling
- **sqlite-utils**: Enhanced SQLite operations
- **pandas**: Data manipulation and Parquet support
- **pyarrow**: Parquet file format support

## License

This script is provided as-is for backup purposes. Please ensure you comply with Airtable's terms of service and API usage guidelines.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the script.

## Support

For issues or questions:
1. Check the logs in the `logs/` directory
2. Review the error messages in the console output
3. Verify your API token and permissions
4. Check network connectivity and Airtable API status 