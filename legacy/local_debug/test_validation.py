#!/usr/bin/env python3
"""
Test script for the validation endpoint.
"""

import requests
import json

# Test data
valid_record = {
    "id": "test-123",
    "dct_title_s": "Test Dataset",
    "dct_description_s": "A test dataset for validation",
    "gbl_mdVersion_s": "Aardvark",
    "dct_accessRights_s": "Public",
    "dcat_bbox": "ENVELOPE(-180, 180, 90, -90)",
    "dct_creator_sm": ["Test Creator"],
    "dct_publisher_s": "Test Publisher",
    "dct_issued_s": "2023-01-01",
    "dct_language_sm": ["English"],
    "dct_subject_sm": ["Test Subject"],
    "gbl_resourceClass_sm": ["Datasets"],
    "gbl_resourceType_sm": ["Dataset"]
}

invalid_record_missing_fields = {
    "dct_description_s": "Missing required fields",
    "gbl_mdVersion_s": "InvalidVersion"
}

invalid_record_wrong_version = {
    "id": "test-456",
    "dct_title_s": "Test Dataset",
    "dct_description_s": "Test description",
    "gbl_mdVersion_s": "InvalidVersion",
    "dct_accessRights_s": "Public",
    "gbl_resourceClass_sm": ["Datasets"],
    "gbl_resourceType_sm": ["Dataset"]
}

def test_validation_endpoint():
    """Test the validation endpoint with valid and invalid records."""
    base_url = "http://localhost:8000/api/v1"  # Use local server
    
    print("Testing validation endpoint...")
    print("=" * 50)
    
    # Test with valid record
    print("1. Testing with valid record:")
    try:
        response = requests.post(f"{base_url}/validate", json=valid_record)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Errors: {len(result.get('errors', []))}")
        print(f"Warnings: {len(result.get('warnings', []))}")
        if result.get('errors'):
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error['field']}: {error['message']}")
        if result.get('warnings'):
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning['field']}: {warning['message']}")
    except Exception as e:
        print(f"Error testing valid record: {e}")
    
    print("\n" + "-" * 50)
    
    # Test with invalid record (missing fields)
    print("2. Testing with invalid record (missing fields):")
    try:
        response = requests.post(f"{base_url}/validate", json=invalid_record_missing_fields)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Errors: {len(result.get('errors', []))}")
        print(f"Warnings: {len(result.get('warnings', []))}")
        if result.get('errors'):
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error['field']}: {error['message']}")
        if result.get('warnings'):
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning['field']}: {warning['message']}")
    except Exception as e:
        print(f"Error testing invalid record: {e}")
    
    print("\n" + "-" * 50)
    
    # Test with invalid record (wrong version)
    print("3. Testing with invalid record (wrong version):")
    try:
        response = requests.post(f"{base_url}/validate", json=invalid_record_wrong_version)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Errors: {len(result.get('errors', []))}")
        print(f"Warnings: {len(result.get('warnings', []))}")
        if result.get('errors'):
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error['field']}: {error['message']}")
        if result.get('warnings'):
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning['field']}: {warning['message']}")
    except Exception as e:
        print(f"Error testing invalid record: {e}")
    
    print("\n" + "-" * 50)
    
    # Test with invalid JSON
    print("4. Testing with invalid JSON:")
    try:
        response = requests.post(f"{base_url}/validate", data="invalid json", headers={"Content-Type": "application/json"})
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Valid: {result.get('valid')}")
        print(f"Errors: {len(result.get('errors', []))}")
        if result.get('errors'):
            print("Errors:")
            for error in result['errors']:
                print(f"  - {error['field']}: {error['message']}")
    except Exception as e:
        print(f"Error testing invalid JSON: {e}")

if __name__ == "__main__":
    test_validation_endpoint()
