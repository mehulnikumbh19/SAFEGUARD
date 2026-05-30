from datetime import datetime

from database import db


SYSTEM_ENVIRONMENTS = ["Production", "Staging", "Development", "Test"]
SYSTEM_TYPES = [
    "Web Application", "API Service", "Database", "SaaS Platform", "Cloud Storage",
    "Identity Service", "Logging Pipeline", "Internal Admin Tool", "Payment System",
    "Healthcare Data System",
]
DATA_CLASSIFICATIONS = ["Public", "Internal", "Confidential", "Restricted"]
DATA_TYPES = [
    "PII", "PHI", "Payment Data", "Authentication Logs", "Security Event Logs",
    "Internal Confidential", "Customer Data",
]
CLOUD_PROVIDERS = ["AWS", "Azure", "GCP", "SaaS", "On-Prem"]
AWS_SERVICE_TYPES = [
    "IAM", "S3", "RDS", "EC2", "Lambda", "CloudTrail", "CloudWatch", "KMS",
    "API Gateway", "Secrets Manager",
]
CRITICALITIES = ["Critical", "High", "Medium", "Low"]
ASSESSMENT_STATUSES = [
    "Not Started", "In Review", "Pending Evidence", "Gap Identified",
    "Remediation In Progress", "Reviewed", "Closed",
]

CONTROL_DOMAINS = [
    "Access Control", "SSO/MFA", "User Permissions", "Privileged Access",
    "Encryption at Rest", "Encryption in Transit", "Logging and Monitoring",
    "Cloud Configuration", "Configuration Baseline", "Change Management",
    "Vulnerability Management", "Secrets Management",
]
IMPLEMENTATION_STATUSES = [
    "Implemented", "Partially Implemented", "Not Implemented", "Not Applicable",
    "Not Assessed",
]
EVIDENCE_STATUSES = ["Available", "Missing", "Incomplete", "Outdated", "Needs Review", "Accepted"]
TESTING_METHODS = [
    "Configuration Review", "Screenshot Review", "Access Export Review",
    "Log Sample Review", "Policy Mapping", "Interview/Walkthrough",
    "Ticket Review", "Automated Check",
]
EVIDENCE_TYPES = [
    "SSO Configuration", "MFA Policy", "IAM Export", "User Access Review",
    "Admin Access Report", "KMS Configuration", "TLS Certificate",
    "Encryption Setting", "CloudTrail Logs", "CloudWatch Logs", "SIEM Log Sample",
    "Security Group Export", "S3 Bucket Policy", "Vulnerability Scan",
    "Configuration Export", "Change Ticket", "Policy Document",
    "Architecture Diagram", "Screenshot",
]
RISK_THEMES = [
    "Excessive Access", "Missing MFA", "Weak Privileged Access Control",
    "Missing Encryption", "Weak TLS Configuration", "Missing Logging",
    "Incomplete Audit Trail", "Public Cloud Exposure", "Weak Configuration Baseline",
    "Missing Evidence", "Outdated Evidence", "Hardcoded Secrets", "Unreviewed Access",
    "Overdue Remediation",
]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
OBSERVATION_STATUSES = ["Open", "In Progress", "Pending Evidence", "Risk Accepted", "Remediated", "Closed"]
REMEDIATION_PRIORITIES = ["Critical", "High", "Medium", "Low"]
REMEDIATION_STATUSES = ["Open", "In Progress", "Pending Validation", "Blocked", "Risk Accepted", "Closed"]
FRAMEWORKS = [
    "Internal Security Policy", "NIST SP 800-53", "CIS Controls", "ISO 27001",
    "SOC 2", "HIPAA", "PCI DSS", "AWS Well-Architected Security Pillar",
]


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class System(TimestampMixin, db.Model):
    __tablename__ = "systems"

    system_id = db.Column(db.Integer, primary_key=True)
    system_name = db.Column(db.String(160), nullable=False, unique=True)
    business_owner = db.Column(db.String(120), nullable=False)
    technical_owner = db.Column(db.String(120), nullable=False)
    environment = db.Column(db.String(40), nullable=False)
    system_type = db.Column(db.String(80), nullable=False)
    data_classification = db.Column(db.String(40), nullable=False)
    sensitive_data_involved = db.Column(db.Boolean, default=False, nullable=False)
    data_types = db.Column(db.String(260), default="")
    cloud_provider = db.Column(db.String(40), nullable=False)
    aws_service_type = db.Column(db.String(80), default="")
    internet_facing = db.Column(db.Boolean, default=False, nullable=False)
    criticality = db.Column(db.String(40), nullable=False)
    assessment_status = db.Column(db.String(80), nullable=False)
    last_reviewed_date = db.Column(db.Date)
    next_review_date = db.Column(db.Date)
    notes = db.Column(db.Text, default="")

    controls = db.relationship("Control", back_populates="system", cascade="all, delete-orphan")
    evidence = db.relationship("Evidence", back_populates="system", cascade="all, delete-orphan")
    observations = db.relationship("Observation", back_populates="system", cascade="all, delete-orphan")
    remediations = db.relationship("Remediation", back_populates="system", cascade="all, delete-orphan")


class Control(TimestampMixin, db.Model):
    __tablename__ = "controls"

    control_id = db.Column(db.Integer, primary_key=True)
    system_id = db.Column(db.Integer, db.ForeignKey("systems.system_id"), nullable=False)
    control_domain = db.Column(db.String(80), nullable=False)
    control_name = db.Column(db.String(180), nullable=False)
    control_objective = db.Column(db.Text, nullable=False)
    expected_implementation = db.Column(db.Text, nullable=False)
    implementation_status = db.Column(db.String(40), nullable=False)
    control_owner = db.Column(db.String(120), nullable=False)
    evidence_required = db.Column(db.Boolean, default=True, nullable=False)
    evidence_status = db.Column(db.String(40), nullable=False)
    testing_method = db.Column(db.String(80), nullable=False)
    assessor_notes = db.Column(db.Text, default="")
    last_tested_date = db.Column(db.Date)
    next_test_date = db.Column(db.Date)

    system = db.relationship("System", back_populates="controls")
    evidence = db.relationship("Evidence", back_populates="control", cascade="all, delete-orphan")
    observations = db.relationship("Observation", back_populates="control", cascade="all, delete-orphan")
    policy_mappings = db.relationship("PolicyMapping", back_populates="control", cascade="all, delete-orphan")


class Evidence(TimestampMixin, db.Model):
    __tablename__ = "evidence"

    evidence_id = db.Column(db.Integer, primary_key=True)
    system_id = db.Column(db.Integer, db.ForeignKey("systems.system_id"), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey("controls.control_id"), nullable=True)
    evidence_name = db.Column(db.String(180), nullable=False)
    evidence_type = db.Column(db.String(80), nullable=False)
    evidence_description = db.Column(db.Text, default="")
    evidence_source = db.Column(db.String(160), default="")
    evidence_owner = db.Column(db.String(120), nullable=False)
    collection_method = db.Column(db.String(120), default="")
    evidence_status = db.Column(db.String(40), nullable=False)
    date_collected = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    file_path_or_link = db.Column(db.String(260), default="")
    review_notes = db.Column(db.Text, default="")
    request_note = db.Column(db.Text, default="")

    system = db.relationship("System", back_populates="evidence")
    control = db.relationship("Control", back_populates="evidence")


class Observation(TimestampMixin, db.Model):
    __tablename__ = "observations"

    observation_id = db.Column(db.Integer, primary_key=True)
    system_id = db.Column(db.Integer, db.ForeignKey("systems.system_id"), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey("controls.control_id"), nullable=True)
    observation_title = db.Column(db.String(180), nullable=False)
    observation_description = db.Column(db.Text, nullable=False)
    risk_theme = db.Column(db.String(80), nullable=False)
    severity = db.Column(db.String(40), nullable=False)
    likelihood = db.Column(db.Integer, nullable=False)
    impact = db.Column(db.Integer, nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    business_impact = db.Column(db.Text, default="")
    compliance_impact = db.Column(db.Text, default="")
    recommended_action = db.Column(db.Text, default="")
    observation_status = db.Column(db.String(40), nullable=False)
    owner = db.Column(db.String(120), nullable=False)
    due_date = db.Column(db.Date)
    closure_evidence = db.Column(db.Text, default="")
    closure_notes = db.Column(db.Text, default="")

    system = db.relationship("System", back_populates="observations")
    control = db.relationship("Control", back_populates="observations")
    remediation = db.relationship("Remediation", back_populates="observation", uselist=False, cascade="all, delete-orphan")


class Remediation(TimestampMixin, db.Model):
    __tablename__ = "remediations"

    remediation_id = db.Column(db.Integer, primary_key=True)
    observation_id = db.Column(db.Integer, db.ForeignKey("observations.observation_id"), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey("systems.system_id"), nullable=False)
    remediation_owner = db.Column(db.String(120), nullable=False)
    action_plan = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(40), nullable=False)
    target_date = db.Column(db.Date)
    status = db.Column(db.String(40), nullable=False)
    progress_notes = db.Column(db.Text, default="")
    validation_required = db.Column(db.Boolean, default=True, nullable=False)
    validation_method = db.Column(db.String(160), default="")
    closure_evidence = db.Column(db.Text, default="")
    date_closed = db.Column(db.Date)

    observation = db.relationship("Observation", back_populates="remediation")
    system = db.relationship("System", back_populates="remediations")


class PolicyMapping(TimestampMixin, db.Model):
    __tablename__ = "policy_mappings"

    mapping_id = db.Column(db.Integer, primary_key=True)
    control_id = db.Column(db.Integer, db.ForeignKey("controls.control_id"), nullable=False)
    framework = db.Column(db.String(120), nullable=False)
    policy_reference = db.Column(db.String(120), nullable=False)
    requirement_summary = db.Column(db.Text, nullable=False)
    mapped_control_objective = db.Column(db.Text, nullable=False)
    evidence_expectation = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, default="")

    control = db.relationship("Control", back_populates="policy_mappings")


class ActivityLog(TimestampMixin, db.Model):
    __tablename__ = "activity_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(80), nullable=False)
    field_changed = db.Column(db.String(120), default="")
    old_value = db.Column(db.Text, default="")
    new_value = db.Column(db.Text, default="")
    actor = db.Column(db.String(120), default="Local Assessor")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


ENUMS = {
    "environment": SYSTEM_ENVIRONMENTS,
    "system_type": SYSTEM_TYPES,
    "data_classification": DATA_CLASSIFICATIONS,
    "cloud_provider": CLOUD_PROVIDERS,
    "aws_service_type": AWS_SERVICE_TYPES,
    "criticality": CRITICALITIES,
    "assessment_status": ASSESSMENT_STATUSES,
    "control_domain": CONTROL_DOMAINS,
    "implementation_status": IMPLEMENTATION_STATUSES,
    "evidence_status": EVIDENCE_STATUSES,
    "testing_method": TESTING_METHODS,
    "evidence_type": EVIDENCE_TYPES,
    "risk_theme": RISK_THEMES,
    "severity": SEVERITIES,
    "observation_status": OBSERVATION_STATUSES,
    "priority": REMEDIATION_PRIORITIES,
    "status": REMEDIATION_STATUSES,
    "framework": FRAMEWORKS,
}
