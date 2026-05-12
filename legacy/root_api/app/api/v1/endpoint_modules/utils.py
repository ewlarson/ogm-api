from typing import Optional


def format_file_size(size_str: Optional[str]) -> Optional[str]:
    """Convert file size string to human-readable format."""
    if not size_str:
        return None

    try:
        # Try to parse as bytes
        size_bytes = int(size_str)
    except (ValueError, TypeError):
        return size_str

    # Convert to human readable format
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"


def clean_dict(data: dict) -> dict:
    """Remove null and empty entries from a dictionary recursively."""
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue
        elif isinstance(value, dict):
            cleaned_value = clean_dict(value)
            if cleaned_value:  # Only include if not empty after cleaning
                cleaned[key] = cleaned_value
        elif isinstance(value, list):
            if value:  # Only include non-empty lists
                cleaned[key] = value
        elif isinstance(value, str):
            if value.strip():  # Only include non-empty strings
                cleaned[key] = value
        else:
            # Include all other non-None values
            cleaned[key] = value

    return cleaned


def map_to_aardvark_fields(resource_dict: dict) -> dict:
    """Map database column names to official Aardvark field names."""
    # Mapping from database column names to official Aardvark field names
    field_mapping = {
        # Most fields already match, but some need mapping
        "dct_accessrights_s": "dct_accessRights_s",  # Note the capital R
        "pcdm_memberof_sm": "pcdm_memberOf_sm",  # Note the capital O
        "gbl_displaynote_sm": "gbl_displayNote_sm",  # Note the capital N
        "gbl_resourceclass_sm": "gbl_resourceClass_sm",  # Note the capital C
        "gbl_resourcetype_sm": "gbl_resourceType_sm",  # Note the capital T
        "gbl_mdversion_s": "gbl_mdVersion_s",  # Note the capital V
        "gbl_mdmodified_dt": "gbl_mdModified_dt",  # Note the capital M
        "gbl_indexyear_im": "gbl_indexYear_im",  # Note the capital Y
        "gbl_daterange_drsim": "gbl_dateRange_drsim",  # Note the capital R
        "dct_identifier_sm": "dct_identifier_sm",  # Already correct
        "dct_references_s": "dct_references_s",  # Already correct
        "dct_rights_sm": "dct_rights_sm",  # Already correct
        "dct_rightsholder_sm": "dct_rightsHolder_sm",  # Note the capital H
        "dct_spatial_sm": "dct_spatial_sm",  # Already correct
        "dct_temporal_sm": "dct_temporal_sm",  # Already correct
        "dct_subject_sm": "dct_subject_sm",  # Already correct
        "dct_language_sm": "dct_language_sm",  # Already correct
        "dct_creator_sm": "dct_creator_sm",  # Already correct
        "dct_publisher_s": "dct_publisher_s",  # Already correct
        "dct_issued_s": "dct_issued_s",  # Already correct
        "dct_title_s": "dct_title_s",  # Already correct
        "dct_description_sm": "dct_description_sm",  # Already correct
        "dcat_bbox": "dcat_bbox",  # Already correct
        "dcat_centroid": "dcat_centroid",  # Already correct
        "dcat_keyword_sm": "dcat_keyword_sm",  # Already correct
        "locn_geometry": "locn_geometry",  # Already correct
        "pcdm_memberof_sm": "pcdm_memberOf_sm",  # Note the capital O
        "schema_provider_s": "schema_provider_s",  # Already correct
    }

    mapped_dict = {}
    for key, value in resource_dict.items():
        # Use the mapped field name if it exists, otherwise use the original
        mapped_key = field_mapping.get(key, key)
        mapped_dict[mapped_key] = value

    return mapped_dict
