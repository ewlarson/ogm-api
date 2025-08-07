# OpenGeoMetadata Harvester

A Python implementation that mimics the Ruby GeoCombine::Harvester class for harvesting Geoblacklight documents from OpenGeoMetadata repositories for indexing.

## Overview

The Harvester class provides functionality to:

- Clone OpenGeoMetadata repositories from GitHub
- Pull updates from existing repositories
- Harvest Geoblacklight JSON documents
- Filter documents by schema version (e.g., "Aardvark")
- Process documents for indexing

## Installation

The harvester is included in this repository and requires no additional dependencies beyond Python standard library modules.

## Usage

### Command Line Interface

The harvester can be used directly from the command line:

```bash
# List available repositories
python scripts/harvester.py --action list

# Clone all repositories
python scripts/harvester.py --action clone

# Pull updates from existing repositories
python scripts/harvester.py --action pull

# Harvest documents (clones/pulls first, then harvests)
python scripts/harvester.py --action harvest

# Use custom path and schema version
python scripts/harvester.py --ogm-path /path/to/repos --schema-version Aardvark

# Enable verbose logging
python scripts/harvester.py --verbose
```

### Python API

```python
from scripts.harvester import Harvester

# Create harvester instance
harvester = Harvester(
    ogm_path="tmp/opengeometadata",
    schema_version="Aardvark"
)

# List repositories
repos = harvester.repositories()
print(f"Found {len(repos)} repositories")

# Clone all repositories
cloned = harvester.clone_all()
print(f"Cloned {len(cloned)} repositories")

# Pull updates
updated = harvester.pull_all()
print(f"Updated {len(updated)} repositories")

# Harvest documents
for record, path in harvester.docs_to_index():
    record_id = record.get('layer_slug_s') or record.get('dc_identifier_s')
    print(f"Found record: {record_id} at {path}")
```

## Configuration

### Environment Variables

- `OGM_PATH`: Path to store OpenGeoMetadata repositories (defaults to `tmp/opengeometadata`)
- `SCHEMA_VERSION`: Schema version to filter for (defaults to "Aardvark")

### Denylist

The harvester automatically excludes certain repositories that are not metadata repositories:

- GeoCombine
- aardvark
- metadata-issues
- ogm_utils-python
- opengeometadata.github.io
- opengeometadata-rails
- gbl-1_to_aardvark

## Features

### Repository Management

- **Clone**: Clone repositories that don't exist locally
- **Pull**: Update existing repositories with latest changes
- **Filter**: Automatically filter out archived, empty, or denylisted repositories

### Document Harvesting

- **Recursive Search**: Finds all JSON files in repository directories
- **Schema Filtering**: Filters documents by schema version (e.g., "Aardvark")
- **File Filtering**: Skips `layers.json` files and non-JSON files
- **Error Handling**: Gracefully handles malformed JSON and file access errors

### Logging

- Configurable logging levels (INFO, DEBUG)
- Detailed progress reporting
- Error logging with context

## Examples

See `examples/harvester_example.py` for comprehensive usage examples including:

- Basic usage
- Pulling updates
- Custom document processing
- Filtering by institution

## Integration with Indexing

The harvester is designed to work with indexing systems. You can use the `docs_to_index()` generator to feed documents to your indexer:

```python
from scripts.harvester import Harvester

harvester = Harvester()
for record, path in harvester.docs_to_index():
    # Process record for indexing
    indexer.add_document(record)
```

## Error Handling

The harvester includes robust error handling:

- Network errors when fetching repository lists
- Git command failures
- JSON parsing errors
- File access errors
- Repository-specific issues (archived, empty, etc.)

## Performance Considerations

- Uses shallow clones (`--depth 1`) to minimize download size
- Processes documents as a generator to minimize memory usage
- Includes progress logging for long-running operations

## Comparison with Ruby Version

This Python implementation provides the same core functionality as the Ruby GeoCombine::Harvester:

| Feature | Ruby Version | Python Version |
|---------|-------------|----------------|
| Repository cloning | ✅ | ✅ |
| Repository pulling | ✅ | ✅ |
| Document harvesting | ✅ | ✅ |
| Schema filtering | ✅ | ✅ |
| Denylist filtering | ✅ | ✅ |
| Error handling | ✅ | ✅ |
| Logging | ✅ | ✅ |
| Command line interface | ❌ | ✅ |

## Troubleshooting

### Common Issues

1. **Git not found**: Ensure git is installed and in your PATH
2. **Permission errors**: Check write permissions for the OGM path
3. **Network errors**: Verify internet connectivity and GitHub API access
4. **Memory issues**: For large repositories, consider processing in batches

### Debug Mode

Enable verbose logging to see detailed information:

```bash
python scripts/harvester.py --verbose --action harvest
```

## Contributing

The harvester is designed to be extensible. Common extension points:

- Custom document filters
- Additional repository sources
- Different output formats
- Integration with specific indexing systems
