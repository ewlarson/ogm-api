from typing import Optional

from pydantic import BaseModel, Field


class AardvarkRecord(BaseModel):
    """Aardvark metadata record for validation."""

    id: Optional[str] = Field(None, description="Unique identifier for the record")
    dct_title_s: Optional[str] = Field(None, description="Title of the resource")
    dct_description_s: Optional[str] = Field(None, description="Description of the resource")
    gbl_mdVersion_s: Optional[str] = Field(
        None, description="Metadata version (must be 'Aardvark')"
    )
    dct_accessRights_s: Optional[str] = Field(None, description="Access rights for the resource")
    dcat_bbox: Optional[str] = Field(None, description="Bounding box in ENVELOPE format")
    dct_creator_sm: Optional[list] = Field(None, description="List of creators")
    dct_publisher_s: Optional[str] = Field(None, description="Publisher of the resource")
    dct_issued_s: Optional[str] = Field(None, description="Date issued")
    dct_language_sm: Optional[list] = Field(None, description="List of languages")
    dct_subject_sm: Optional[list] = Field(None, description="List of subjects")
    gbl_resourceClass_sm: Optional[list] = Field(None, description="List of resource classes")
    gbl_resourceType_sm: Optional[list] = Field(None, description="List of resource types")

    class Config:
        extra = "allow"  # Allow additional fields not defined in the model


class ValidationResponse(BaseModel):
    """Response model for validation results."""

    valid: bool = Field(..., description="Whether the record is valid")
    errors: list = Field(..., description="List of validation errors")
    warnings: list = Field(..., description="List of validation warnings")
    profile: list = Field(..., description="Profile information")
