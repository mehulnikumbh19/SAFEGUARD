from datetime import datetime

from calculations import calculate_risk_score
from database import db
from models import (
    ASSESSMENT_STATUSES,
    CLOUD_PROVIDERS,
    CONTROL_DOMAINS,
    CRITICALITIES,
    DATA_CLASSIFICATIONS,
    EVIDENCE_STATUSES,
    EVIDENCE_TYPES,
    FRAMEWORKS,
    IMPLEMENTATION_STATUSES,
    OBSERVATION_STATUSES,
    RISK_THEMES,
    SYSTEM_ENVIRONMENTS,
    SYSTEM_TYPES,
    TESTING_METHODS,
    ActivityLog,
    Control,
    Evidence,
    Observation,
    PolicyMapping,
    System,
)


TEMPLATES = {
    "systems": [
        "system_name", "business_owner", "technical_owner", "environment", "system_type",
        "data_classification", "sensitive_data_involved", "data_types", "cloud_provider",
        "aws_service_type", "internet_facing", "criticality", "assessment_status",
        "last_reviewed_date", "next_review_date", "notes",
    ],
    "controls": [
        "system_name", "control_domain", "control_name", "control_objective",
        "expected_implementation", "implementation_status", "control_owner",
        "evidence_required", "evidence_status", "testing_method", "assessor_notes",
        "last_tested_date", "next_test_date",
    ],
    "evidence": [
        "system_name", "control_name", "evidence_name", "evidence_type",
        "evidence_description", "evidence_source", "evidence_owner", "collection_method",
        "evidence_status", "date_collected", "expiration_date", "file_path_or_link",
        "review_notes", "request_note",
    ],
    "observations": [
        "system_name", "control_name", "observation_title", "observation_description",
        "risk_theme", "severity", "likelihood", "impact", "business_impact",
        "compliance_impact", "recommended_action", "observation_status", "owner",
        "due_date", "closure_evidence", "closure_notes",
    ],
    "policy_mappings": [
        "control_name", "framework", "policy_reference", "requirement_summary",
        "mapped_control_objective", "evidence_expectation", "notes",
    ],
}


ENUM_VALIDATORS = {
    "environment": SYSTEM_ENVIRONMENTS,
    "system_type": SYSTEM_TYPES,
    "data_classification": DATA_CLASSIFICATIONS,
    "cloud_provider": CLOUD_PROVIDERS,
    "criticality": CRITICALITIES,
    "assessment_status": ASSESSMENT_STATUSES,
    "control_domain": CONTROL_DOMAINS,
    "implementation_status": IMPLEMENTATION_STATUSES,
    "evidence_status": EVIDENCE_STATUSES,
    "testing_method": TESTING_METHODS,
    "evidence_type": EVIDENCE_TYPES,
    "risk_theme": RISK_THEMES,
    "observation_status": OBSERVATION_STATUSES,
    "framework": FRAMEWORKS,
}


def _isna(value):
    # NaN is the only value not equal to itself; also treat None as missing.
    return value is None or (isinstance(value, float) and value != value)


def parse_date(value):
    if _isna(value) or value == "":
        return None
    if hasattr(value, "date"):
        return value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "1", "y"}


def validate_headers(kind, df):
    required = TEMPLATES[kind]
    missing = [column for column in required if column not in df.columns]
    extra = [column for column in df.columns if column not in required]
    return missing, extra


def validate_row(kind, row):
    errors = []
    for field, allowed in ENUM_VALIDATORS.items():
        if field in row and not _isna(row[field]) and str(row[field]).strip():
            if str(row[field]).strip() not in allowed:
                errors.append(f"{field} has invalid value '{row[field]}'")
    if kind in {"controls", "evidence", "observations"}:
        if not System.query.filter_by(system_name=str(row.get("system_name", "")).strip()).first():
            errors.append("system_name does not match an existing system")
    if kind in {"evidence", "observations", "policy_mappings"} and str(row.get("control_name", "")).strip():
        if not Control.query.filter_by(control_name=str(row.get("control_name")).strip()).first():
            errors.append("control_name does not match an existing control")
    return errors


def preview_import(kind, file_storage):
    import pandas as pd

    df = pd.read_csv(file_storage)
    missing, extra = validate_headers(kind, df)
    if missing:
        return {"valid": [], "errors": [{"row": "header", "errors": [f"Missing columns: {', '.join(missing)}"]}], "extra": extra}

    valid = []
    errors = []
    for idx, row in df.iterrows():
        row_dict = {col: ("" if pd.isna(row[col]) else row[col]) for col in TEMPLATES[kind]}
        row_errors = validate_row(kind, row_dict)
        if row_errors:
            errors.append({"row": idx + 2, "errors": row_errors})
        else:
            valid.append(row_dict)
    return {"valid": valid, "errors": errors, "extra": extra}


def _activity(entity_type, entity_id, action):
    db.session.add(ActivityLog(entity_type=entity_type, entity_id=entity_id, action=action, actor="CSV Import"))


def commit_import(kind, rows):
    created = 0
    for row in rows:
        if kind == "systems":
            obj = System(
                system_name=row["system_name"],
                business_owner=row["business_owner"],
                technical_owner=row["technical_owner"],
                environment=row["environment"],
                system_type=row["system_type"],
                data_classification=row["data_classification"],
                sensitive_data_involved=parse_bool(row["sensitive_data_involved"]),
                data_types=row["data_types"],
                cloud_provider=row["cloud_provider"],
                aws_service_type=row["aws_service_type"],
                internet_facing=parse_bool(row["internet_facing"]),
                criticality=row["criticality"],
                assessment_status=row["assessment_status"],
                last_reviewed_date=parse_date(row["last_reviewed_date"]),
                next_review_date=parse_date(row["next_review_date"]),
                notes=row["notes"],
            )
        elif kind == "controls":
            system = System.query.filter_by(system_name=row["system_name"]).first()
            obj = Control(
                system_id=system.system_id,
                control_domain=row["control_domain"],
                control_name=row["control_name"],
                control_objective=row["control_objective"],
                expected_implementation=row["expected_implementation"],
                implementation_status=row["implementation_status"],
                control_owner=row["control_owner"],
                evidence_required=parse_bool(row["evidence_required"]),
                evidence_status=row["evidence_status"],
                testing_method=row["testing_method"],
                assessor_notes=row["assessor_notes"],
                last_tested_date=parse_date(row["last_tested_date"]),
                next_test_date=parse_date(row["next_test_date"]),
            )
        elif kind == "evidence":
            system = System.query.filter_by(system_name=row["system_name"]).first()
            control = Control.query.filter_by(control_name=row["control_name"]).first()
            obj = Evidence(
                system_id=system.system_id,
                control_id=control.control_id if control else None,
                evidence_name=row["evidence_name"],
                evidence_type=row["evidence_type"],
                evidence_description=row["evidence_description"],
                evidence_source=row["evidence_source"],
                evidence_owner=row["evidence_owner"],
                collection_method=row["collection_method"],
                evidence_status=row["evidence_status"],
                date_collected=parse_date(row["date_collected"]),
                expiration_date=parse_date(row["expiration_date"]),
                file_path_or_link=row["file_path_or_link"],
                review_notes=row["review_notes"],
                request_note=row["request_note"],
            )
        elif kind == "observations":
            system = System.query.filter_by(system_name=row["system_name"]).first()
            control = Control.query.filter_by(control_name=row["control_name"]).first()
            likelihood = int(row["likelihood"])
            impact = int(row["impact"])
            obj = Observation(
                system_id=system.system_id,
                control_id=control.control_id if control else None,
                observation_title=row["observation_title"],
                observation_description=row["observation_description"],
                risk_theme=row["risk_theme"],
                severity=row.get("severity", "Medium"),
                likelihood=likelihood,
                impact=impact,
                risk_score=calculate_risk_score(likelihood, impact),
                business_impact=row["business_impact"],
                compliance_impact=row["compliance_impact"],
                recommended_action=row["recommended_action"],
                observation_status=row["observation_status"],
                owner=row["owner"],
                due_date=parse_date(row["due_date"]),
                closure_evidence=row["closure_evidence"],
                closure_notes=row["closure_notes"],
            )
        else:
            control = Control.query.filter_by(control_name=row["control_name"]).first()
            obj = PolicyMapping(
                control_id=control.control_id,
                framework=row["framework"],
                policy_reference=row["policy_reference"],
                requirement_summary=row["requirement_summary"],
                mapped_control_objective=row["mapped_control_objective"],
                evidence_expectation=row["evidence_expectation"],
                notes=row["notes"],
            )

        db.session.add(obj)
        db.session.flush()
        _activity(obj.__class__.__name__, obj.__mapper__.primary_key_from_instance(obj)[0], "create")
        created += 1
    db.session.commit()
    return created
