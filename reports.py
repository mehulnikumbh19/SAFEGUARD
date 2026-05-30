from pathlib import Path

from calculations import assign_risk_rating, compute_assessment_readiness_score, flag_overdue_remediation
from config import EXPORT_DIR
from models import Control, Evidence, Observation, Remediation, System


def build_markdown_report(filename="SAFEGUARD_Report.md", system=None):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    systems = [system] if system else System.query.order_by(System.system_name).all()
    system_ids = [s.system_id for s in systems]
    controls = Control.query.filter(Control.system_id.in_(system_ids)).all()
    evidence = Evidence.query.filter(Evidence.system_id.in_(system_ids)).all()
    observations = Observation.query.filter(Observation.system_id.in_(system_ids)).all()
    remediations = Remediation.query.filter(Remediation.system_id.in_(system_ids)).all()
    readiness = compute_assessment_readiness_score(systems, controls, evidence, observations, remediations)

    high_risks = [o for o in observations if assign_risk_rating(o.risk_score) in {"High", "Critical"} and o.observation_status not in {"Closed", "Remediated", "Risk Accepted"}]
    overdue = [r for r in remediations if flag_overdue_remediation(r)]
    sensitive = [s for s in systems if s.sensitive_data_involved or s.data_classification == "Restricted"]

    lines = [
        "# SAFEGUARD Management Report",
        "",
        f"Scope: {'All systems' if not system else system.system_name}",
        "Assessment period: Mar 2025 - May 2025",
        f"Assessment Readiness Score: {readiness}/100",
        "",
        "## Assessment Overview",
        f"- Systems reviewed: {len(systems)}",
        f"- Controls reviewed: {len(controls)}",
        f"- Evidence records: {len(evidence)}",
        f"- Open high/critical observations: {len(high_risks)}",
        f"- Overdue remediation items: {len(overdue)}",
        "",
        "## Control Implementation Summary",
    ]
    for status in ["Implemented", "Partially Implemented", "Not Implemented", "Not Assessed", "Not Applicable"]:
        lines.append(f"- {status}: {sum(1 for c in controls if c.implementation_status == status)}")

    lines.extend(["", "## Evidence Health Summary"])
    for status in ["Accepted", "Available", "Needs Review", "Missing", "Incomplete", "Outdated"]:
        lines.append(f"- {status}: {sum(1 for e in evidence if e.evidence_status == status)}")

    lines.extend(["", "## High-Risk Observations"])
    if high_risks:
        for observation in sorted(high_risks, key=lambda o: o.risk_score, reverse=True):
            lines.append(f"- {observation.system.system_name}: {observation.observation_title} ({assign_risk_rating(observation.risk_score)}, score {observation.risk_score})")
    else:
        lines.append("- No open high or critical observations.")

    lines.extend(["", "## Overdue Remediation"])
    if overdue:
        for remediation in overdue:
            lines.append(f"- {remediation.system.system_name}: {remediation.observation.observation_title} owned by {remediation.remediation_owner}, target {remediation.target_date}")
    else:
        lines.append("- No overdue remediation items.")

    lines.extend(["", "## Sensitive-Data Systems"])
    for s in sensitive:
        lines.append(f"- {s.system_name}: {s.data_classification}; {s.data_types}")

    lines.extend([
        "",
        "## Cloud Control Concerns",
        "- Confirm logging evidence is current for production cloud services.",
        "- Refresh encryption and key-management evidence for PHI/payment systems.",
        "- Review AWS-style service exports for IAM, S3, API Gateway, CloudTrail, CloudWatch, and KMS control coverage.",
        "",
        "## Recommended Next Steps",
        "1. Close or risk-accept overdue high/critical remediation items.",
        "2. Refresh missing and outdated evidence requests.",
        "3. Validate SSO/MFA and privileged-access coverage for production systems.",
        "4. Update management summary after evidence owners respond.",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
