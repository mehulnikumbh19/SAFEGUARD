from datetime import date, timedelta
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from calculations import (
    assign_risk_rating,
    chart_counts,
    compute_assessment_readiness_score,
    coverage_matrix,
    dashboard_metrics,
    days_between,
    domain_status_summary,
    evidence_age_bucket,
    flag_overdue_remediation,
    get_system_flags,
)
from config import Config, ensure_directories
from database import db, init_db
from exports import export_systems_csv, export_workbook
from imports import TEMPLATES, commit_import, preview_import
from models import (
    CONTROL_DOMAINS,
    FRAMEWORKS,
    ActivityLog,
    Control,
    Evidence,
    Observation,
    PolicyMapping,
    Remediation,
    System,
)
from reports import build_markdown_report
from seed_data import reset_database, seed_database


def create_app():
    ensure_directories()
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    @app.context_processor
    def inject_helpers():
        return {
            "assign_risk_rating": assign_risk_rating,
            "flag_overdue_remediation": flag_overdue_remediation,
            "days_between": days_between,
            "today": date.today,
        }

    @app.cli.command("reset-db")
    def reset_db_command():
        reset_database()
        seed_database()
        print("Database reset and seeded.")

    @app.route("/")
    def dashboard():
        systems = System.query.all()
        controls = Control.query.all()
        evidence = Evidence.query.all()
        observations = Observation.query.all()
        remediations = Remediation.query.all()
        metrics = dashboard_metrics(systems, controls, evidence, observations, remediations)
        top_risks = (
            Observation.query
            .filter(~Observation.observation_status.in_(["Closed", "Remediated", "Risk Accepted"]))
            .order_by(Observation.risk_score.desc())
            .limit(5)
            .all()
        )
        due_cutoff = date.today() + timedelta(days=30)
        reviews_due = System.query.filter(System.next_review_date <= due_cutoff).order_by(System.next_review_date).all()
        tests_due = Control.query.filter(Control.next_test_date <= due_cutoff).order_by(Control.next_test_date).limit(8).all()
        charts = {
            "controlStatus": chart_counts(controls, "implementation_status"),
            "evidenceStatus": chart_counts(evidence, "evidence_status"),
            "observationSeverity": chart_counts(observations, "severity"),
            "remediationStatus": chart_counts(remediations, "status"),
            "cloudProviders": chart_counts(systems, "cloud_provider"),
            "riskThemes": chart_counts(observations, "risk_theme"),
        }
        return render_template("dashboard.html", metrics=metrics, charts=charts, top_risks=top_risks, reviews_due=reviews_due, tests_due=tests_due)

    def _systems_query():
        query = System.query
        filters = {
            "environment": request.args.get("environment", ""),
            "cloud_provider": request.args.get("cloud_provider", ""),
            "criticality": request.args.get("criticality", ""),
            "data_classification": request.args.get("data_classification", ""),
            "assessment_status": request.args.get("assessment_status", ""),
            "sensitive_data_involved": request.args.get("sensitive_data_involved", ""),
            "q": request.args.get("q", "").strip(),
        }
        for field, value in filters.items():
            if not value or field in {"q", "sensitive_data_involved"}:
                continue
            query = query.filter(getattr(System, field) == value)
        if filters["sensitive_data_involved"]:
            query = query.filter(System.sensitive_data_involved == (filters["sensitive_data_involved"] == "true"))
        if filters["q"]:
            like = f"%{filters['q']}%"
            query = query.filter(
                db.or_(
                    System.system_name.ilike(like),
                    System.business_owner.ilike(like),
                    System.technical_owner.ilike(like),
                    System.data_types.ilike(like),
                )
            )
        return query.order_by(System.criticality, System.system_name), filters

    @app.route("/systems")
    def systems():
        query, filters = _systems_query()
        systems_list = query.all()
        if request.args.get("export") == "csv":
            return send_file(export_systems_csv(systems_list), as_attachment=True)
        return render_template("systems.html", systems=systems_list, filters=filters)

    @app.route("/systems/<int:system_id>")
    def system_detail(system_id):
        system = System.query.get_or_404(system_id)
        score = compute_assessment_readiness_score([system], system.controls, system.evidence, system.observations, system.remediations)
        mappings = PolicyMapping.query.join(Control).filter(Control.system_id == system.system_id).all()
        return render_template("system_detail.html", system=system, score=score, flags=get_system_flags(system), mappings=mappings)

    @app.route("/systems/<int:system_id>/export/<kind>")
    def export_system_report(system_id, kind):
        system = System.query.get_or_404(system_id)
        if kind == "excel":
            return send_file(export_workbook(f"SAFEGUARD_{system.system_name.replace(' ', '_')}.xlsx", system), as_attachment=True)
        return send_file(build_markdown_report(f"SAFEGUARD_{system.system_name.replace(' ', '_')}.md", system), as_attachment=True)

    @app.route("/controls")
    def controls():
        query = Control.query.join(System)
        filters = {key: request.args.get(key, "") for key in ["control_domain", "implementation_status", "evidence_status", "system_id", "control_owner"]}
        for field, value in filters.items():
            if not value:
                continue
            if field == "system_id":
                query = query.filter(Control.system_id == int(value))
            else:
                query = query.filter(getattr(Control, field) == value)
        controls_list = query.order_by(Control.control_domain, Control.control_name).all()
        return render_template("controls.html", controls=controls_list, systems=System.query.order_by(System.system_name).all(), filters=filters, summary=domain_status_summary(controls_list))

    @app.route("/evidence", methods=["GET", "POST"])
    def evidence():
        if request.method == "POST":
            evidence_item = Evidence.query.get_or_404(int(request.form["evidence_id"]))
            old_note = evidence_item.request_note or ""
            evidence_item.request_note = request.form.get("request_note", "")
            db.session.add(ActivityLog(entity_type="Evidence", entity_id=evidence_item.evidence_id, action="update", field_changed="request_note", old_value=old_note, new_value=evidence_item.request_note, actor="Local Assessor"))
            db.session.commit()
            flash("Evidence request note updated.", "success")
            return redirect(url_for("evidence"))
        evidence_list = Evidence.query.join(System).order_by(Evidence.expiration_date.asc().nullslast(), Evidence.evidence_name).all()
        buckets = {"current": 0, "expiring <=30 days": 0, "expired": 0}
        for item in evidence_list:
            buckets[evidence_age_bucket(item)] += 1
        request_list = [e for e in evidence_list if e.evidence_status in {"Missing", "Incomplete", "Outdated"} or e.request_note]
        return render_template("evidence.html", evidence=evidence_list, buckets=buckets, request_list=request_list)

    @app.route("/observations")
    def observations():
        observations_list = Observation.query.join(System).order_by(Observation.risk_score.desc(), Observation.due_date).all()
        matrix = {(l, i): 0 for l in range(1, 6) for i in range(1, 6)}
        for obs in observations_list:
            matrix[(obs.likelihood, obs.impact)] += 1
        return render_template("observations.html", observations=observations_list, matrix=matrix)

    @app.route("/remediation", methods=["GET", "POST"])
    def remediation():
        if request.method == "POST":
            item = Remediation.query.get_or_404(int(request.form["remediation_id"]))
            old_status = item.status
            item.status = request.form["status"]
            item.progress_notes = request.form.get("progress_notes", item.progress_notes)
            if item.status == "Closed" and not item.date_closed:
                item.date_closed = date.today()
            db.session.add(ActivityLog(entity_type="Remediation", entity_id=item.remediation_id, action="status-change", field_changed="status", old_value=old_status, new_value=item.status, actor="Local Assessor"))
            db.session.commit()
            flash("Remediation status updated.", "success")
            return redirect(url_for("remediation"))
        remediations = Remediation.query.join(System).order_by(Remediation.target_date).all()
        status_counts = chart_counts(remediations, "status")
        return render_template("remediation.html", remediations=remediations, status_counts=status_counts)

    @app.route("/policy_mapping")
    def policy_mapping():
        mappings = PolicyMapping.query.join(Control).order_by(PolicyMapping.framework, Control.control_domain).all()
        return render_template("policy_mapping.html", mappings=mappings)

    @app.route("/coverage")
    def coverage():
        mappings = PolicyMapping.query.all()
        matrix = coverage_matrix(mappings, CONTROL_DOMAINS, FRAMEWORKS)
        return render_template("coverage.html", matrix=matrix, domains=CONTROL_DOMAINS, frameworks=FRAMEWORKS)

    @app.route("/risk_register")
    def risk_register():
        observations_list = Observation.query.join(System).order_by(Observation.risk_score.desc(), Observation.due_date).all()
        if request.args.get("export") == "csv":
            rows = []
            for obs in observations_list:
                rem = obs.remediation
                rows.append({
                    "risk_theme": obs.risk_theme,
                    "severity": obs.severity,
                    "risk_score": obs.risk_score,
                    "risk_rating": assign_risk_rating(obs.risk_score),
                    "affected_system": obs.system.system_name,
                    "owner": obs.owner,
                    "status": obs.observation_status,
                    "target_date": rem.target_date if rem else "",
                    "days_overdue": (date.today() - rem.target_date).days if rem and flag_overdue_remediation(rem) else "",
                })
            import pandas as pd
            from config import EXPORT_DIR
            path = EXPORT_DIR / "risk_register.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            return send_file(path, as_attachment=True)
        return render_template("risk_register.html", observations=observations_list)

    @app.route("/activity_log")
    def activity_log():
        entity_type = request.args.get("entity_type", "")
        query = ActivityLog.query
        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)
        logs = query.order_by(ActivityLog.timestamp.desc()).limit(250).all()
        entity_types = [row[0] for row in db.session.query(ActivityLog.entity_type).distinct().order_by(ActivityLog.entity_type).all()]
        return render_template("activity_log.html", logs=logs, entity_types=entity_types, selected=entity_type)

    @app.route("/reports")
    def reports():
        systems = System.query.all()
        controls = Control.query.all()
        evidence = Evidence.query.all()
        observations = Observation.query.all()
        remediations = Remediation.query.all()
        score = compute_assessment_readiness_score(systems, controls, evidence, observations, remediations)
        return render_template("reports.html", score=score, systems=systems, controls=controls, evidence=evidence, observations=observations, remediations=remediations)

    @app.route("/reports/export/<kind>")
    def export_report(kind):
        if kind == "excel":
            return send_file(export_workbook(), as_attachment=True)
        return send_file(build_markdown_report(), as_attachment=True)

    @app.route("/import", methods=["GET", "POST"])
    def import_page():
        result = None
        if request.method == "POST":
            kind = request.form["kind"]
            file = request.files.get("file")
            if not file:
                flash("Choose a CSV file first.", "warning")
                return redirect(url_for("import_page"))
            result = preview_import(kind, file)
            if request.form.get("commit") == "1" and result["valid"]:
                created = commit_import(kind, result["valid"])
                flash(f"Imported {created} {kind} row(s). Rejected rows were skipped.", "success")
                return redirect(url_for("import_page"))
        return render_template("import.html", templates=TEMPLATES, result=result)

    @app.route("/sample_imports/<path:filename>")
    def sample_import(filename):
        return send_file(Path("sample_imports") / filename, as_attachment=True)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        if not System.query.first():
            seed_database()
    app.run(debug=True)
