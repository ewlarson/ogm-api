import logging

import requests
from fastapi import APIRouter
from jsonschema import ValidationError, validate

from .models import AardvarkRecord, ValidationResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_aardvark_record(request_body: AardvarkRecord):
    """Validate a single Aardvark JSON record against the OpenGeoMetadata schema."""
    try:
        # Get the JSON body from the request and exclude None values
        record = request_body.dict(exclude_none=True)

        # Fetch the Aardvark schema from OpenGeoMetadata
        schema_url = "https://opengeometadata.org/schema/geoblacklight-schema-aardvark.json"
        try:
            response = requests.get(schema_url, timeout=10)
            response.raise_for_status()
            schema = response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch schema from {schema_url}: {e}")
            return ValidationResponse(
                valid=False,
                errors=[{"field": "schema", "message": f"Failed to fetch schema: {str(e)}"}],
                warnings=[],
                profile=[
                    "https://opengeometadata.org/profile/aardvark",
                    "https://opengeometadata.org/profile/mcp/validate",
                ],
            )

        # Validate the record against the schema
        errors = []
        warnings = []
        schema_valid = True

        try:
            validate(instance=record, schema=schema)
        except ValidationError as e:
            schema_valid = False
            # Parse validation errors
            for error in e.context:
                field_path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                errors.append({"field": field_path, "message": error.message})
            # Also include the main error
            main_field = " -> ".join(str(p) for p in e.path) if e.path else "root"
            errors.append({"field": main_field, "message": e.message})

        # Additional custom validations for Aardvark-specific requirements
        # Check for required fields that might not be in the schema
        required_fields = ["dct_title_s", "gbl_mdVersion_s"]

        for field in required_fields:
            if field not in record or not record[field]:
                # Only add custom error if not already in schema errors
                field_error_exists = any(e.get("field") == field for e in errors)
                if not field_error_exists:
                    errors.append(
                        {
                            "field": field,
                            "message": "This field is required and must be a non-empty string.",
                        }
                    )

        # Check specific field values
        if "gbl_mdVersion_s" in record and record["gbl_mdVersion_s"] != "Aardvark":
            # Only add custom error if not already in schema errors
            version_error_exists = any(
                e.get("field") == "gbl_mdVersion_s" and "Aardvark" in e.get("message", "")
                for e in errors
            )
            if not version_error_exists:
                errors.append({"field": "gbl_mdVersion_s", "message": "Value must be 'Aardvark'."})

        # Check for common warnings (only if schema validation passed)
        if schema_valid:
            if "dcat_bbox" not in record and "solr_geom" not in record:
                warnings.append(
                    {
                        "field": "spatial_coverage",
                        "message": "Spatial coverage information is recommended (dcat_bbox or solr_geom).",
                    }
                )

        # Determine overall validity - record is valid if there are no errors
        valid = len(errors) == 0

        # Build the response
        return ValidationResponse(
            valid=valid,
            errors=errors,
            warnings=warnings,
            profile=[
                "https://opengeometadata.org/profile/aardvark",
                "https://opengeometadata.org/profile/mcp/validate",
            ],
        )

    except Exception as e:
        logger.error(f"Error validating record: {str(e)}", exc_info=True)
        return ValidationResponse(
            valid=False,
            errors=[{"field": "validation", "message": f"Validation error: {str(e)}"}],
            warnings=[],
            profile=[
                "https://opengeometadata.org/profile/aardvark",
                "https://opengeometadata.org/profile/mcp/validate",
            ],
        )
