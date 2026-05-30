from collections import Counter, defaultdict
from datetime import date, timedelta


RISK_COLORS = {
    "Critical": "danger",
    "High": "orange",
    "Medium": "warning",
    "Low": "success",
}


def today():
    return date.today()


def calculate_risk_score(likelihood, impact):
    return int(likelihood or 0) * int(impact or 0)


def assign_risk_rating(score):
    score = int(score or 0)
    if score >= 17:
        return "Critical"
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def is_evidence_expired(evidence, as_of=None):
    as_of = as_of or today()
    return bool(evidence.expiration_date and evidence.expiration_date < as_of)


def is_evidence_outdated(evidence, as_of=None):
    as_of = as_of or today()
    if is_evidence_expired(evidence, as_of):
        return True
    if evidence.evidence_status in {"Missing", "Incomplete", "Outdated"}:
        return True
    aging_types = {"User Access Review", "Vulnerability Scan"}
    if evidence.evidence_type in aging_types and evidence.date_collected:
        return evidence.date_collected < as_of - timedelta(days=365)
    return False


def evidence_age_bucket(evidence, as_of=None):
    as_of = as_of or today()
    if not evidence.expiration_date:
        return "current"
    if evidence.expiration_date < as_of:
        return "expired"
    if evidence.expiration_date <= as_of + timedelta(days=30):
        return "expiring <=30 days"
    return "current"


def flag_missing_evidence(control):
    return control.evidence_required and control.evidence_status in {"Missing", "Incomplete", "Outdated", "Needs Review"}


def flag_overdue_remediation(remediation, as_of=None):
    as_of = as_of or today()
    return bool(remediation.target_date and remediation.target_date < as_of and remediation.status != "Closed")


def highlight_sensitive_data_system(system):
    data_types = system.data_types or ""
    return system.sensitive_data_involved or any(token in data_types for token in ["PII", "PHI", "Payment Data"])


def _has_evidence(system, type_tokens, accepted_statuses=None):
    accepted_statuses = accepted_statuses or {"Available", "Accepted", "Needs Review"}
    for evidence in system.evidence:
        haystack = f"{evidence.evidence_type} {evidence.evidence_name}".lower()
        if any(token.lower() in haystack for token in type_tokens) and evidence.evidence_status in accepted_statuses:
            if not is_evidence_outdated(evidence):
                return True
    return False


def highlight_production_without_logging_evidence(system):
    if system.environment != "Production":
        return False
    return not _has_evidence(system, ["CloudTrail", "CloudWatch", "SIEM", "Log"])


def highlight_phi_payment_missing_encryption(system):
    data_types = system.data_types or ""
    if "PHI" not in data_types and "Payment Data" not in data_types:
        return False
    return not _has_evidence(system, ["KMS", "Encryption", "TLS Certificate"])


def highlight_privileged_access_missing_mfa(system):
    has_privileged_control = any(c.control_domain == "Privileged Access" for c in system.controls)
    if not has_privileged_control:
        return False
    return not _has_evidence(system, ["MFA", "SSO"])


def get_system_flags(system):
    flags = []
    if highlight_sensitive_data_system(system):
        flags.append({"severity": "Medium", "rule": "Sensitive data system", "detail": "System stores or processes sensitive data."})
    if highlight_production_without_logging_evidence(system):
        flags.append({"severity": "High", "rule": "Production logging evidence gap", "detail": "Production system lacks current logging evidence."})
    if highlight_phi_payment_missing_encryption(system):
        flags.append({"severity": "Critical", "rule": "Encryption evidence missing", "detail": "PHI/payment system lacks current encryption evidence."})
    if highlight_privileged_access_missing_mfa(system):
        flags.append({"severity": "High", "rule": "Privileged MFA evidence missing", "detail": "Privileged access controls lack current MFA/SSO evidence."})
    missing_controls = [c for c in system.controls if flag_missing_evidence(c)]
    if missing_controls:
        flags.append({"severity": "Medium", "rule": "Control evidence gaps", "detail": f"{len(missing_controls)} control(s) need evidence review."})
    overdue = [r for r in system.remediations if flag_overdue_remediation(r)]
    if overdue:
        flags.append({"severity": "High", "rule": "Overdue remediation", "detail": f"{len(overdue)} remediation item(s) are overdue."})
    return flags


def compute_assessment_readiness_score(systems, controls, evidence, observations, remediations):
    controls = list(controls)
    evidence = list(evidence)
    observations = list(observations)
    remediations = list(remediations)

    implemented = sum(1 for c in controls if c.implementation_status in {"Implemented", "Not Applicable"})
    control_pct = implemented / len(controls) if controls else 1

    good_evidence = sum(1 for e in evidence if e.evidence_status in {"Available", "Accepted"} and not is_evidence_outdated(e))
    evidence_pct = good_evidence / len(evidence) if evidence else 1

    open_high = sum(1 for o in observations if o.observation_status not in {"Closed", "Remediated", "Risk Accepted"} and assign_risk_rating(o.risk_score) in {"High", "Critical"})
    overdue = sum(1 for r in remediations if flag_overdue_remediation(r))

    risk_penalty = min(open_high * 5, 25)
    overdue_penalty = min(overdue * 4, 20)
    raw_score = (control_pct * 45) + (evidence_pct * 35) + 20 - risk_penalty - overdue_penalty
    return max(0, min(100, round(raw_score)))


def dashboard_metrics(systems, controls, evidence, observations, remediations):
    systems = list(systems)
    controls = list(controls)
    evidence = list(evidence)
    observations = list(observations)
    remediations = list(remediations)
    open_obs = [o for o in observations if o.observation_status not in {"Closed", "Remediated", "Risk Accepted"}]

    return {
        "total_systems": len(systems),
        "systems_pending_evidence": sum(1 for s in systems if s.assessment_status == "Pending Evidence"),
        "controls_reviewed": len(controls),
        "controls_implemented": sum(1 for c in controls if c.implementation_status == "Implemented"),
        "partially_implemented": sum(1 for c in controls if c.implementation_status == "Partially Implemented"),
        "not_implemented": sum(1 for c in controls if c.implementation_status == "Not Implemented"),
        "missing_evidence": sum(1 for e in evidence if e.evidence_status == "Missing"),
        "outdated_evidence": sum(1 for e in evidence if is_evidence_outdated(e)),
        "open_observations": len(open_obs),
        "high_critical_observations": sum(1 for o in open_obs if assign_risk_rating(o.risk_score) in {"High", "Critical"}),
        "overdue_remediations": sum(1 for r in remediations if flag_overdue_remediation(r)),
        "restricted_data_systems": sum(1 for s in systems if s.data_classification == "Restricted"),
        "phi_payment_systems": sum(1 for s in systems if "PHI" in (s.data_types or "") or "Payment Data" in (s.data_types or "")),
        "cloud_systems_reviewed": sum(1 for s in systems if s.cloud_provider in {"AWS", "Azure", "GCP", "SaaS"}),
        "readiness_score": compute_assessment_readiness_score(systems, controls, evidence, observations, remediations),
    }


def chart_counts(items, attr):
    return dict(Counter(getattr(item, attr, None) or "Unknown" for item in items))


def domain_status_summary(controls):
    summary = defaultdict(Counter)
    for control in controls:
        summary[control.control_domain][control.implementation_status] += 1
    return {domain: dict(counts) for domain, counts in summary.items()}


def coverage_matrix(mappings, domains, frameworks):
    mapped = defaultdict(set)
    for mapping in mappings:
        if mapping.control:
            mapped[mapping.framework].add(mapping.control.control_domain)
    return {
        framework: {domain: domain in mapped[framework] for domain in domains}
        for framework in frameworks
    }


def days_between(start, end=None):
    if not start:
        return None
    end = end or today()
    return (end - start).days
