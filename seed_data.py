from datetime import date, timedelta

from calculations import calculate_risk_score
from database import db
from models import ActivityLog, Control, Evidence, Observation, PolicyMapping, Remediation, System


TODAY = date.today()


SYSTEM_SEEDS = [
    ("Customer Identity Portal", "Maya Patel", "Jordan Lee", "Production", "Identity Service", "Restricted", True, "PII, Authentication Logs, Customer Data", "AWS", "IAM", True, "Critical", "Pending Evidence"),
    ("Payment Processing API", "Daniel Kim", "Priya Shah", "Production", "Payment System", "Restricted", True, "Payment Data, PII, Security Event Logs", "AWS", "API Gateway", True, "Critical", "Gap Identified"),
    ("Healthcare Records Service", "Alicia Gomez", "Sam Rivera", "Production", "Healthcare Data System", "Restricted", True, "PHI, PII, Internal Confidential", "AWS", "RDS", False, "Critical", "Remediation In Progress"),
    ("AWS S3 Data Lake", "Nina Brooks", "Ethan Wong", "Production", "Cloud Storage", "Confidential", True, "Customer Data, Internal Confidential", "AWS", "S3", False, "High", "In Review"),
    ("Internal Admin Console", "Omar Singh", "Riley Chen", "Production", "Internal Admin Tool", "Confidential", True, "Internal Confidential, Authentication Logs", "AWS", "EC2", False, "High", "Pending Evidence"),
    ("Security Logging Pipeline", "Grace Allen", "Liam Carter", "Production", "Logging Pipeline", "Confidential", True, "Security Event Logs, Authentication Logs", "AWS", "CloudWatch", False, "High", "Reviewed"),
    ("Vendor Risk Platform", "Hannah Park", "Morgan Fox", "Production", "SaaS Platform", "Internal", False, "Internal Confidential", "SaaS", "", False, "Medium", "Reviewed"),
    ("Employee Access Portal", "Victor Nguyen", "Taylor Morgan", "Production", "Web Application", "Confidential", True, "PII, Authentication Logs", "Azure", "", True, "High", "In Review"),
    ("Claims Processing Service", "Iris Young", "Noah Scott", "Staging", "API Service", "Restricted", True, "PHI, Customer Data", "AWS", "Lambda", False, "High", "Pending Evidence"),
    ("Metrics Reporting API", "Leah Stone", "Chris Evans", "Development", "API Service", "Internal", False, "Internal Confidential", "GCP", "", False, "Medium", "Not Started"),
]


CONTROL_BLUEPRINTS = [
    ("SSO/MFA", "SSO and MFA Enforcement", "Ensure workforce identities authenticate through SSO with MFA enforced.", "SSO configured with MFA for normal and privileged users.", "Configuration Review"),
    ("User Permissions", "User Access Review", "Verify user access is reviewed and aligned to role need.", "Quarterly access review evidence and owner sign-off.", "Access Export Review"),
    ("Privileged Access", "Privileged Account Control", "Confirm administrator access is restricted, approved, and monitored.", "Privileged roles are reviewed, time-bound, and MFA protected.", "Access Export Review"),
    ("Encryption at Rest", "Data Encryption at Rest", "Confirm sensitive data stores use approved encryption controls.", "Encryption enabled with managed keys or documented compensating controls.", "Configuration Review"),
    ("Logging and Monitoring", "Security Logging Coverage", "Confirm security-relevant activity is logged and reviewable.", "Cloud/service logs retained and connected to monitoring.", "Log Sample Review"),
]


OBSERVATION_SEEDS = [
    ("Customer Identity Portal", "SSO/MFA", "MFA not enforced for privileged users", "Privileged access paths do not have current MFA enforcement evidence.", "Missing MFA", "High", 4, 4, "Privileged accounts could be misused without a second factor.", "Supports access-control and audit-readiness concerns.", "Enforce MFA and attach current policy evidence.", "Open", "Jordan Lee", 18),
    ("Employee Access Portal", "User Permissions", "user access review evidence outdated", "Most recent access review is older than 12 months.", "Outdated Evidence", "Medium", 3, 3, "Dormant or excessive access may remain active.", "Weakens periodic access review defensibility.", "Complete a fresh access review and retain approval evidence.", "In Progress", "Taylor Morgan", 28),
    ("Metrics Reporting API", "Logging and Monitoring", "CloudTrail logging not enabled for one service", "Cloud activity evidence is missing for the API review scope.", "Missing Logging", "High", 4, 4, "Security events may not be reconstructable.", "Creates incomplete audit trail risk.", "Enable cloud activity logs and provide sample log evidence.", "Open", "Chris Evans", 12),
    ("Healthcare Records Service", "Encryption at Rest", "KMS key rotation evidence missing", "Encryption exists but key rotation evidence was not provided.", "Missing Encryption", "High", 3, 5, "Protected health data key hygiene cannot be confirmed.", "Impacts HIPAA-aligned control evidence.", "Provide KMS configuration and rotation evidence.", "Pending Evidence", "Sam Rivera", 9),
    ("AWS S3 Data Lake", "Cloud Configuration", "S3 bucket policy requires review", "Bucket policy grants are broad and require owner validation.", "Public Cloud Exposure", "Medium", 3, 3, "Data lake objects may be exposed to unintended principals.", "Cloud configuration review evidence is incomplete.", "Review policy, remove broad grants, and attach export evidence.", "Open", "Ethan Wong", 20),
    ("Payment Processing API", "Encryption in Transit", "TLS certificate evidence incomplete", "TLS certificate and cipher evidence did not include the production endpoint.", "Weak TLS Configuration", "Medium", 3, 4, "Payment traffic assurance cannot be fully demonstrated.", "Impacts PCI DSS-aligned evidence package.", "Provide certificate scan and endpoint configuration.", "In Progress", "Priya Shah", 16),
    ("Internal Admin Console", "Privileged Access", "production admin access not reviewed", "Admin access export has not been reviewed by the owner.", "Unreviewed Access", "High", 4, 4, "Excessive production administration access may persist.", "Weakens privileged access control evidence.", "Complete admin access review and remove stale accounts.", "Open", "Riley Chen", 7),
    ("Claims Processing Service", "Vulnerability Management", "vulnerability remediation overdue", "High-risk vulnerability ticket remains open past the target date.", "Overdue Remediation", "High", 4, 4, "Known weakness may remain exploitable.", "Remediation SLA evidence is not met.", "Patch or risk-accept with accountable approval.", "Open", "Noah Scott", -10),
    ("Security Logging Pipeline", "Logging and Monitoring", "logging retention period not documented", "Retention duration was not clearly documented for security logs.", "Incomplete Audit Trail", "Medium", 2, 4, "Investigations may lack expected history.", "Policy mapping requires retention rationale.", "Document retention and link policy reference.", "Pending Evidence", "Liam Carter", 25),
    ("Payment Processing API", "Encryption at Rest", "payment API encryption evidence missing", "Database encryption evidence is missing for payment transaction records.", "Missing Encryption", "Critical", 4, 5, "Payment data exposure risk cannot be ruled out.", "Creates PCI DSS-aligned evidence gap.", "Provide encryption setting export and key-management reference.", "Open", "Priya Shah", 5),
    ("Vendor Risk Platform", "Policy Mapping", "policy reference not mapped for vendor evidence", "Vendor risk controls are not mapped to internal evidence expectations.", "Missing Evidence", "Low", 2, 2, "Management reporting lacks clear policy traceability.", "SOC 2 evidence package may need manual explanation.", "Map vendor risk review to internal policy and SOC 2 criteria.", "Open", "Morgan Fox", 35),
    ("Customer Identity Portal", "Secrets Management", "hardcoded secret review not evidenced", "Secret scanning evidence was not included in the configuration export.", "Hardcoded Secrets", "Medium", 3, 3, "Credential exposure review cannot be confirmed.", "Secrets management control evidence is incomplete.", "Attach scan result or ticket showing no hardcoded secrets.", "Open", "Jordan Lee", 22),
    ("AWS S3 Data Lake", "Configuration Baseline", "baseline drift review incomplete", "Configuration baseline export does not include drift review status.", "Weak Configuration Baseline", "Medium", 3, 3, "Unauthorized changes may not be detected.", "Baseline evidence is incomplete.", "Export baseline status and reviewer notes.", "In Progress", "Ethan Wong", 24),
    ("Employee Access Portal", "SSO/MFA", "MFA exception list requires owner approval", "Exception list exists but lacks business owner approval.", "Missing MFA", "Medium", 3, 4, "Users may retain unmanaged MFA exceptions.", "Access exception governance evidence is weak.", "Approve, expire, or remove listed exceptions.", "Pending Evidence", "Taylor Morgan", 14),
    ("Security Logging Pipeline", "Change Management", "change ticket evidence incomplete", "Recent logging pipeline change lacks validation evidence.", "Missing Evidence", "Low", 2, 2, "Logging changes may not be fully validated.", "Change management evidence is incomplete.", "Attach change ticket validation and approval notes.", "Open", "Liam Carter", 40),
]


def _d(days):
    return TODAY + timedelta(days=days)


def _log(entity_type, entity_id, action, field="", old="", new="", actor="Seed Loader"):
    db.session.add(ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field_changed=field,
        old_value=str(old or ""),
        new_value=str(new or ""),
        actor=actor,
    ))


def reset_database():
    db.drop_all()
    db.create_all()


def seed_database():
    if System.query.first():
        return

    systems = {}
    for idx, seed in enumerate(SYSTEM_SEEDS):
        system = System(
            system_name=seed[0],
            business_owner=seed[1],
            technical_owner=seed[2],
            environment=seed[3],
            system_type=seed[4],
            data_classification=seed[5],
            sensitive_data_involved=seed[6],
            data_types=seed[7],
            cloud_provider=seed[8],
            aws_service_type=seed[9],
            internet_facing=seed[10],
            criticality=seed[11],
            assessment_status=seed[12],
            last_reviewed_date=_d(-75 + idx * 5),
            next_review_date=_d(10 + idx * 7),
            notes=f"Seeded review scope for {seed[0]} covering access, logging, encryption, and cloud configuration evidence.",
        )
        db.session.add(system)
        db.session.flush()
        systems[system.system_name] = system
        _log("System", system.system_id, "create", "system_name", "", system.system_name)

    controls = {}
    status_cycle = ["Implemented", "Partially Implemented", "Implemented", "Not Implemented", "Not Assessed"]
    evidence_cycle = ["Accepted", "Needs Review", "Available", "Missing", "Incomplete"]
    for system_index, system in enumerate(systems.values()):
        blueprints = CONTROL_BLUEPRINTS[:]
        if system.system_name in {"AWS S3 Data Lake", "Metrics Reporting API", "Security Logging Pipeline"}:
            blueprints.append(("Cloud Configuration", "Cloud Service Configuration Review", "Confirm cloud service settings align to expected security baseline.", "Configuration exports reviewed for public exposure, logging, and encryption.", "Configuration Review"))
        if system.system_name in {"Claims Processing Service", "Metrics Reporting API", "Security Logging Pipeline"}:
            blueprints.append(("Vulnerability Management", "Vulnerability Remediation Evidence", "Confirm vulnerabilities are tracked and remediated on time.", "Scan and ticket evidence show prioritized remediation.", "Ticket Review"))
        if system.system_name in {"Customer Identity Portal", "Payment Processing API", "Internal Admin Console"}:
            blueprints.append(("Secrets Management", "Secrets Handling Review", "Confirm secrets are stored and rotated through approved services.", "Secrets Manager/KMS references and scan evidence are available.", "Automated Check"))
        for control_index, bp in enumerate(blueprints):
            status = status_cycle[(system_index + control_index) % len(status_cycle)]
            evidence_status = evidence_cycle[(system_index + control_index) % len(evidence_cycle)]
            control = Control(
                system_id=system.system_id,
                control_domain=bp[0],
                control_name=bp[1],
                control_objective=bp[2],
                expected_implementation=bp[3],
                implementation_status=status,
                control_owner=system.technical_owner,
                evidence_required=True,
                evidence_status=evidence_status,
                testing_method=bp[4],
                assessor_notes=f"{bp[0]} reviewed for {system.system_name}.",
                last_tested_date=_d(-60 + control_index * 9),
                next_test_date=_d(15 + control_index * 14),
            )
            db.session.add(control)
            db.session.flush()
            controls[(system.system_name, control.control_domain)] = control
            _log("Control", control.control_id, "create", "implementation_status", "", status)

    evidence_rows = []
    evidence_templates = [
        ("SSO Configuration", "SSO configuration export", "Identity provider", "Admin Console Export", 180),
        ("MFA Policy", "MFA policy screenshot", "Identity provider", "Screenshot Review", 180),
        ("User Access Review", "Quarterly access review", "Access review workbook", "Owner Attestation", 365),
        ("Admin Access Report", "Privileged role export", "IAM", "Access Export", 180),
        ("KMS Configuration", "KMS key configuration", "AWS KMS", "Configuration Export", 365),
        ("TLS Certificate", "TLS endpoint evidence", "Certificate scan", "Automated Scan", 90),
        ("CloudTrail Logs", "CloudTrail log sample", "AWS CloudTrail", "Log Sample", 180),
        ("CloudWatch Logs", "CloudWatch retention export", "AWS CloudWatch", "Configuration Export", 365),
        ("Security Group Export", "Security group export", "AWS EC2", "Configuration Export", 180),
        ("S3 Bucket Policy", "Bucket policy export", "AWS S3", "Configuration Export", 180),
        ("Vulnerability Scan", "Vulnerability scan result", "Scanner", "Automated Scan", 365),
        ("Configuration Export", "Service configuration export", "Cloud console", "Configuration Export", 180),
    ]
    statuses = ["Accepted", "Available", "Needs Review", "Missing", "Incomplete", "Outdated"]
    for index, system in enumerate(systems.values()):
        for offset, tmpl in enumerate(evidence_templates[index % 4:index % 4 + 4]):
            status = statuses[(index + offset) % len(statuses)]
            collected = _d(-30 - (index * 21) - offset * 15)
            expires = collected + timedelta(days=tmpl[4])
            if status in {"Missing", "Incomplete"}:
                collected = None
                expires = None
            evidence_rows.append((system, tmpl, status, collected, expires))
    # Ensure a few specific automation gaps are visible on first run.
    evidence_rows.append((systems["Payment Processing API"], ("Encryption Setting", "Payment database encryption export", "RDS", "Configuration Export", 365), "Missing", None, None))
    evidence_rows.append((systems["Customer Identity Portal"], ("MFA Policy", "Privileged MFA evidence", "Identity provider", "Screenshot Review", 180), "Missing", None, None))
    evidence_rows.append((systems["Employee Access Portal"], ("User Access Review", "Employee portal access review", "Access workbook", "Owner Attestation", 365), "Outdated", _d(-440), _d(-75)))

    for system, tmpl, status, collected, expires in evidence_rows:
        matched_control = next((c for c in system.controls if tmpl[0].split()[0].lower() in c.control_name.lower() or c.control_domain.split()[0].lower() in tmpl[0].lower()), None)
        evidence = Evidence(
            system_id=system.system_id,
            control_id=matched_control.control_id if matched_control else None,
            evidence_name=tmpl[1],
            evidence_type=tmpl[0],
            evidence_description=f"{tmpl[1]} used to support reviewer testing for {system.system_name}.",
            evidence_source=tmpl[2],
            evidence_owner=system.technical_owner,
            collection_method=tmpl[3],
            evidence_status=status,
            date_collected=collected,
            expiration_date=expires,
            file_path_or_link=f"evidence/{system.system_name.lower().replace(' ', '-')}/{tmpl[0].lower().replace(' ', '-')}.pdf" if status not in {"Missing", "Incomplete"} else "",
            review_notes="Seeded evidence record; some entries intentionally require follow-up.",
            request_note="Please provide refreshed evidence with owner approval." if status in {"Missing", "Incomplete", "Outdated"} else "",
        )
        db.session.add(evidence)
        db.session.flush()
        _log("Evidence", evidence.evidence_id, "create", "evidence_status", "", status)

    observations = []
    for seed in OBSERVATION_SEEDS:
        system = systems[seed[0]]
        control = controls.get((seed[0], seed[1])) or (system.controls[0] if system.controls else None)
        score = calculate_risk_score(seed[6], seed[7])
        observation = Observation(
            system_id=system.system_id,
            control_id=control.control_id if control else None,
            observation_title=seed[2],
            observation_description=seed[3],
            risk_theme=seed[4],
            severity=seed[5],
            likelihood=seed[6],
            impact=seed[7],
            risk_score=score,
            business_impact=seed[8],
            compliance_impact=seed[9],
            recommended_action=seed[10],
            observation_status=seed[11],
            owner=seed[12],
            due_date=_d(seed[13]),
        )
        db.session.add(observation)
        db.session.flush()
        observations.append(observation)
        _log("Observation", observation.observation_id, "create", "risk_score", "", score)

    for index, observation in enumerate(observations[:12]):
        remediation = Remediation(
            observation_id=observation.observation_id,
            system_id=observation.system_id,
            remediation_owner=observation.owner,
            action_plan=observation.recommended_action,
            priority=observation.severity if observation.severity in {"Critical", "High", "Medium", "Low"} else "Medium",
            target_date=observation.due_date,
            status=["Open", "In Progress", "Pending Validation", "Blocked", "Risk Accepted", "Open"][index % 6],
            progress_notes="Seeded remediation item with status aligned to the observation workflow.",
            validation_required=True,
            validation_method="Assessor reviews updated evidence and control owner attestation.",
            closure_evidence="",
        )
        db.session.add(remediation)
        db.session.flush()
        _log("Remediation", remediation.remediation_id, "create", "status", "", remediation.status)

    frameworks = [
        "Internal Security Policy", "NIST SP 800-53", "CIS Controls", "ISO 27001",
        "SOC 2", "HIPAA", "PCI DSS", "AWS Well-Architected Security Pillar",
    ]
    all_controls = Control.query.order_by(Control.control_id).all()
    for index, control in enumerate(all_controls[:25]):
        framework = frameworks[index % len(frameworks)]
        mapping = PolicyMapping(
            control_id=control.control_id,
            framework=framework,
            policy_reference=f"{framework.split()[0].upper()}-{100 + index}",
            requirement_summary=f"Paraphrased expectation for {control.control_domain.lower()} controls with documented owner review.",
            mapped_control_objective=control.control_objective,
            evidence_expectation=f"Current evidence showing {control.expected_implementation.lower()}",
            notes="Short paraphrased mapping only; no proprietary framework text copied.",
        )
        db.session.add(mapping)
        db.session.flush()
        _log("PolicyMapping", mapping.mapping_id, "create", "framework", "", framework)

    db.session.commit()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        reset_database()
        seed_database()
        print("SAFeguard database reset and seeded.")
