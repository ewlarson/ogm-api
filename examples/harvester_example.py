#!/usr/bin/env python3
import os
import logging
from pathlib import Path

# Add the backend scripts directory to the path so we can import the harvester
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "scripts"))

from ogm_harvester import OGMHarvester


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_basic_usage():
    """Example of basic harvester usage."""
    print("=== Basic Harvester Usage ===")
    
    # Create a harvester instance
    harvester = OGMHarvester(
        ogm_path="backend/data/opengeometadata",
        schema_version="Aardvark"
    )
    
    # List available repositories
    repos = harvester.repositories()
    print(f"Found {len(repos)} repositories to harvest")
    print("First 5 repositories:", repos[:5])
    
    # Clone all repositories (this will take a while)
    print("\nCloning repositories...")
    cloned = harvester.clone_all()
    print(f"Cloned {len(cloned)} repositories")
    
    # Harvest documents
    print("\nHarvesting documents...")
    count = 0
    for record, path in harvester.docs_to_index():
        count += 1
        record_id = record.get('layer_slug_s') or record.get('dc_identifier_s')
        print(f"  {count}: {record_id} from {path}")
        
        # Limit to first 10 for demo
        if count >= 10:
            break
    
    print(f"\nTotal documents found: {count}")


def example_pull_updates():
    """Example of pulling updates from existing repositories."""
    print("\n=== Pulling Updates ===")
    
    harvester = OGMHarvester(ogm_path="backend/data/opengeometadata")
    
    # Pull updates from all repositories
    updated = harvester.pull_all()
    print(f"Updated {len(updated)} repositories")


def example_custom_processing():
    """Example of custom processing of harvested documents."""
    print("\n=== Custom Document Processing ===")
    
    harvester = OGMHarvester(
        ogm_path="backend/data/opengeometadata",
        schema_version="Aardvark"
    )
    
    # Process documents with custom logic
    spatial_records = []
    temporal_records = []
    
    for record, path in harvester.docs_to_index():
        # Check if record has spatial data
        if record.get('dcat_bbox') or record.get('locn_geometry'):
            spatial_records.append(record)
        
        # Check if record has temporal data
        if record.get('dct_temporal_sm') or record.get('dct_issued_s'):
            temporal_records.append(record)
    
    print(f"Records with spatial data: {len(spatial_records)}")
    print(f"Records with temporal data: {len(temporal_records)}")
    
    # Show some examples
    if spatial_records:
        example = spatial_records[0]
        print(f"\nExample spatial record:")
        print(f"  Title: {example.get('dct_title_s', 'N/A')}")
        print(f"  Bounding Box: {example.get('dcat_bbox', 'N/A')}")
        print(f"  Geometry: {example.get('locn_geometry', 'N/A')[:100]}...")


def example_filter_by_institution():
    """Example of filtering documents by institution."""
    print("\n=== Filtering by Institution ===")
    
    harvester = OGMHarvester(ogm_path="backend/data/opengeometadata")
    
    # Filter for specific institutions
    target_institutions = ['stanford', 'mit', 'harvard']
    institution_records = {}
    
    for record, path in harvester.docs_to_index():
        # Check if the path contains any of our target institutions
        for institution in target_institutions:
            if institution in path.lower():
                if institution not in institution_records:
                    institution_records[institution] = []
                institution_records[institution].append(record)
                break
    
    for institution, records in institution_records.items():
        print(f"{institution.capitalize()}: {len(records)} records")


def main():
    """Main function to run all examples."""
    setup_logging()
    
    print("OpenGeoMetadata Harvester Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_usage()
        example_pull_updates()
        example_custom_processing()
        example_filter_by_institution()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        logging.exception("Unexpected error")


if __name__ == "__main__":
    main()
