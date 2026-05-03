import logging
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PUBLICATION_STATE = "published"

# Map legacy `items` columns to the modern `resources` schema. Keep this list
# intentionally limited to fields that exist in the legacy production table.
LEGACY_ITEMS_TO_RESOURCE_COLUMNS = [
    ("id", "id"),
    ("dct_title_s", "dct_title_s"),
    ("dct_alternative_sm", "dct_alternative_sm"),
    ("dct_description_sm", "dct_description_sm"),
    ("dct_language_sm", "dct_language_sm"),
    ("gbl_displayNote_sm", "gbl_displaynote_sm"),
    ("dct_creator_sm", "dct_creator_sm"),
    ("dct_publisher_sm", "dct_publisher_sm"),
    ("schema_provider_s", "schema_provider_s"),
    ("gbl_resourceClass_sm", "gbl_resourceclass_sm"),
    ("gbl_resourceType_sm", "gbl_resourcetype_sm"),
    ("dct_subject_sm", "dct_subject_sm"),
    ("dcat_theme_sm", "dcat_theme_sm"),
    ("dcat_keyword_sm", "dcat_keyword_sm"),
    ("dct_temporal_sm", "dct_temporal_sm"),
    ("dct_issued_s", "dct_issued_s"),
    ("gbl_indexYear_im", "gbl_indexyear_im"),
    ("gbl_dateRange_drsim", "gbl_daterange_drsim"),
    ("dct_spatial_sm", "dct_spatial_sm"),
    ("locn_geometry", "locn_geometry"),
    ("dcat_bbox", "dcat_bbox"),
    ("dcat_centroid", "dcat_centroid"),
    ("dct_relation_sm", "dct_relation_sm"),
    ("pcdm_memberOf_sm", "pcdm_memberof_sm"),
    ("dct_isPartOf_sm", "dct_ispartof_sm"),
    ("dct_source_sm", "dct_source_sm"),
    ("dct_isVersionOf_sm", "dct_isversionof_sm"),
    ("dct_replaces_sm", "dct_replaces_sm"),
    ("dct_isReplacedBy_sm", "dct_isreplacedby_sm"),
    ("dct_rights_sm", "dct_rights_sm"),
    ("dct_rightsHolder_sm", "dct_rightsholder_sm"),
    ("dct_license_sm", "dct_license_sm"),
    ("dct_accessRights_s", "dct_accessrights_s"),
    ("dct_format_s", "dct_format_s"),
    ("gbl_fileSize_s", "gbl_filesize_s"),
    ("gbl_wxsIdentifier_s", "gbl_wxsidentifier_s"),
    ("dct_references_s", "dct_references_s"),
    ("dct_identifier_sm", "dct_identifier_sm"),
    ("gbl_mdModified_dt", "gbl_mdmodified_dt"),
    ("gbl_mdVersion_s", "gbl_mdversion_s"),
    ("gbl_suppressed_b", "gbl_suppressed_b"),
    ("gbl_georeferenced_b", "gbl_georeferenced_b"),
]


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def _quote_ident(identifier: str) -> str:
    return f'"{identifier}"'


def build_backfill_statement():
    target_columns = [target for target, _ in LEGACY_ITEMS_TO_RESOURCE_COLUMNS]
    target_columns.extend(["publication_state", "b1g_publication_state_s"])

    insert_columns_sql = ", ".join(_quote_ident(column) for column in target_columns)
    select_columns_sql = ", ".join(
        _quote_ident(source) for _, source in LEGACY_ITEMS_TO_RESOURCE_COLUMNS
    )

    return text(
        f"""
        INSERT INTO resources ({insert_columns_sql})
        SELECT
            {select_columns_sql},
            :publication_state,
            :publication_state
        FROM items
        ON CONFLICT (id) DO NOTHING
        """
    )


def backfill_resources_from_legacy_items():
    """Copy legacy `items` rows into `resources` without touching existing rows."""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:2345/btaa_ogm_api"
    )
    engine = create_engine(_normalize_database_url(database_url))
    inspector = inspect(engine)

    if not inspector.has_table("items"):
        logger.info("Legacy table 'items' does not exist. Skipping resources backfill.")
        return

    if not inspector.has_table("resources"):
        logger.error("Table 'resources' does not exist. Cannot backfill from 'items'.")
        return

    item_columns = {column["name"] for column in inspector.get_columns("items")}
    missing_columns = sorted(
        {
            source_column
            for _, source_column in LEGACY_ITEMS_TO_RESOURCE_COLUMNS
            if source_column not in item_columns
        }
    )
    if missing_columns:
        logger.error(
            "Legacy table 'items' is missing required columns for backfill: %s",
            ", ".join(missing_columns),
        )
        return

    with engine.begin() as conn:
        items_count = conn.execute(text("SELECT COUNT(*) FROM items")).scalar() or 0
        if items_count == 0:
            logger.info("Legacy table 'items' is empty. Nothing to backfill.")
            return

        resources_before = conn.execute(text("SELECT COUNT(*) FROM resources")).scalar() or 0
        missing_before = (
            conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM items i
                    LEFT JOIN resources r ON r.id = i.id
                    WHERE r.id IS NULL
                    """
                )
            ).scalar()
            or 0
        )

        if missing_before == 0:
            logger.info(
                "Resources table already contains every legacy item row (%s records).",
                resources_before,
            )
            return

        logger.info(
            "Backfilling resources from legacy items: items=%s resources_before=%s missing=%s",
            items_count,
            resources_before,
            missing_before,
        )
        conn.execute(
            build_backfill_statement(), {"publication_state": DEFAULT_PUBLICATION_STATE}
        )

        resources_after = conn.execute(text("SELECT COUNT(*) FROM resources")).scalar() or 0
        logger.info(
            "Finished backfilling resources from legacy items: inserted=%s resources_after=%s",
            resources_after - resources_before,
            resources_after,
        )


if __name__ == "__main__":
    backfill_resources_from_legacy_items()
