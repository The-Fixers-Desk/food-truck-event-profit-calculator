import sqlite3
import os
from dataclasses import replace
from datetime import datetime, timedelta
from io import BytesIO
import json
from pathlib import Path
import tempfile

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from app.data_safety import (
    BackupValidationError,
    create_automatic_recovery_snapshot,
    create_customer_backup,
    database_from_recovery_archive,
    stage_restore_backup,
)

from app.business_defaults_form import defaults_to_form, validate_defaults_form
from app.calculations import calculate_event_scenario
from app.comparison import build_comparison
from app.database import (
    FinalScenarioDeletionError,
    ScenarioNameConflict,
    business_defaults_setup_is_complete,
    create_event_scenario,
    create_event_with_initial_scenario,
    clear_customer_data,
    delete_all_events,
    delete_event,
    delete_event_scenario,
    list_saved_events,
    load_business_defaults,
    load_event_scenario,
    overwrite_event_scenario,
    rename_event,
    rename_event_scenario,
    reset_business_defaults,
    save_business_defaults,
    saved_event_counts,
    close_database,
    get_database,
)
from app.event_inputs_form import (
    blank_event_inputs_form,
    calculation_result_data,
    calculate_demand_preview,
    customer_warning_data,
    event_scenario_to_form,
    protection_reductions,
    scenario_from_form_values,
    validate_and_calculate_event_analysis,
    weather_allows_protection,
)

main = Blueprint("main", __name__)


def _workspace_scenario_summaries(event_id: int) -> list[dict]:
    """Return calculation-backed scenario cards for one saved Event."""
    event = next(
        (item for item in list_saved_events() if item["id"] == event_id),
        None,
    )
    if event is None:
        return []
    summaries = []
    for item in reversed(event["scenarios"]):
        _, _, scenario = load_event_scenario(item["id"])
        result = calculate_event_scenario(scenario)
        evaluation = result.profit_target_evaluation
        if result.business_profit < 0:
            status, tone = "Not worth it", "danger"
        elif evaluation is not None and evaluation.is_met is False:
            status, tone = "Borderline", "warning"
        else:
            status, tone = "Worth it", "success"
        summaries.append(
            {
                **item,
                "status": status,
                "tone": tone,
                "analysis": calculation_result_data(result),
            }
        )
    return summaries


@main.before_request
def require_business_defaults_setup():
    """Keep setup-dependent screens behind persisted valid Defaults."""
    if current_app.config.get("RECOVERY_MODE"):
        if request.endpoint not in {
            "main.data_safety",
            "main.restore_backup",
        }:
            return redirect(url_for("main.data_safety"))
        return None
    if not current_app.config.get("ENFORCE_SETUP", True):
        return None
    if request.endpoint in {
        "main.home",
        "main.welcome",
        "main.defer_onboarding",
        "main.defaults",
        "main.finish_defaults_later",
        "main.data_safety",
        "main.download_backup",
        "main.restore_backup",
        "main.download_sample_format",
        "main.delete_all_saved_events",
        "main.reset_saved_defaults",
        "main.clear_all_customer_data",
    }:
        return None
    if (
        request.endpoint == "main.dashboard"
        and session.get("onboarding_deferred")
    ):
        return None
    if not business_defaults_setup_is_complete():
        flash(
            "Set up your business defaults before analyzing an event.",
            "info",
        )
        return redirect(url_for("main.welcome"))
    return None


@main.get("/")
def home():
    """Open Welcome on first use and Dashboard after setup."""
    if current_app.config.get("RECOVERY_MODE"):
        return redirect(url_for("main.data_safety"))
    if (
        business_defaults_setup_is_complete()
        or session.get("onboarding_deferred")
    ):
        return redirect(url_for("main.dashboard"))
    return render_template("welcome.html", active_page="welcome")


@main.get("/welcome")
def welcome():
    """Display onboarding only while setup remains incomplete."""
    if business_defaults_setup_is_complete():
        return redirect(url_for("main.dashboard"))
    return render_template("welcome.html", active_page="welcome")


@main.post("/welcome/defer")
def defer_onboarding():
    """Let a first-time customer explore the Dashboard before setup."""
    session["onboarding_deferred"] = True
    return redirect(url_for("main.dashboard"))


@main.get("/dashboard")
def dashboard():
    """Display persisted setup and saved-analysis context."""
    setup_complete = business_defaults_setup_is_complete()
    if not setup_complete and not session.get("onboarding_deferred"):
        return redirect(url_for("main.welcome"))
    if setup_complete:
        event_count, scenario_count = saved_event_counts()
        recent_events = list_saved_events()[:3]
    else:
        event_count, scenario_count, recent_events = 0, 0, []
    return render_template(
        "dashboard.html",
        active_page="dashboard",
        event_count=event_count,
        scenario_count=scenario_count,
        recent_events=recent_events,
        setup_complete=setup_complete,
    )


@main.get("/system-states")
def system_states():
    """Display deterministic reusable system states for support review."""
    return render_template("system_states.html", active_page="system")


@main.get("/data-safety")
def data_safety():
    """Display customer backup, restore, and recovery controls."""
    event_count, scenario_count = (0, 0)
    defaults_count = 0
    if not current_app.config.get("RECOVERY_MODE", False):
        event_count, scenario_count = saved_event_counts()
        defaults_count = int(business_defaults_setup_is_complete())
    marker = current_app.config["DATA_PATHS"].root / "last-export.txt"
    last_export = marker.read_text(encoding="utf-8").strip() if marker.exists() else None
    return render_template(
        "data_safety.html",
        active_page="data_safety",
        recovery_mode=current_app.config.get("RECOVERY_MODE", False),
        restore_error=None,
        event_count=event_count,
        scenario_count=scenario_count,
        defaults_count=defaults_count,
        last_export=last_export,
    )


@main.post("/data-safety/backup")
def download_backup():
    """Create and download a fresh consistent database snapshot."""
    if current_app.config.get("RECOVERY_MODE"):
        abort(503)
    try:
        payload, filename = create_customer_backup(
            get_database(),
            current_app.config["DATA_PATHS"],
        )
    except (OSError, sqlite3.Error, BackupValidationError):
        current_app.logger.exception("Customer backup creation failed.")
        abort(500)
    marker = current_app.config["DATA_PATHS"].root / "last-export.txt"
    marker.write_text(datetime.now().astimezone().isoformat(timespec="minutes"), encoding="utf-8")
    return send_file(
        payload,
        as_attachment=True,
        download_name=filename,
        mimetype="application/zip",
    )


@main.post("/data-safety/restore")
def restore_backup():
    """Validate and atomically replace all customer data from a backup."""
    upload = request.files.get("backup_file")
    if request.form.get("confirm_restore") != "yes":
        return _render_restore_error(
            "Confirm that restoring will replace all current saved data."
        )
    if upload is None or not upload.filename.lower().endswith(".ftbackup"):
        return _render_restore_error("Choose a valid .ftbackup file.")
    paths = current_app.config["DATA_PATHS"]
    try:
        payload = upload.stream.read(current_app.config["MAX_CONTENT_LENGTH"] + 1)
        with tempfile.TemporaryDirectory(dir=paths.staging) as temporary:
            working = Path(temporary)
            staged = stage_restore_backup(payload, paths, working)
            recovery_mode = current_app.config.get("RECOVERY_MODE", False)
            recovery = None
            if recovery_mode:
                close_database()
                damaged_name = (
                    f"damaged-{Path(temporary).name}.sqlite"
                )
                damaged = paths.safe_child(
                    paths.automatic_recovery, damaged_name
                )
                os.replace(paths.database, damaged)
            else:
                live = get_database()
                recovery = create_automatic_recovery_snapshot(
                    live,
                    paths,
                    "pre-restore",
                    logger=current_app.logger,
                )
                close_database()
            try:
                os.replace(staged, paths.database)
                restored = get_database()
                from app.migrations import migrate_database

                migrate_database(restored)
                load_business_defaults()
                saved_event_counts()
            except Exception:
                current_app.logger.exception(
                    "Restore replacement failed; applying recovery snapshot."
                )
                close_database()
                if recovery is not None:
                    rollback = working / "rollback.sqlite"
                    database_from_recovery_archive(recovery, rollback)
                    os.replace(rollback, paths.database)
                elif recovery_mode and damaged.exists():
                    os.replace(damaged, paths.database)
                get_database()
                raise
    except BackupValidationError as error:
        current_app.logger.warning("Backup restore validation failed: %s", error)
        return _render_restore_error(str(error))
    except (OSError, sqlite3.Error):
        current_app.logger.exception("Backup restore failed.")
        abort(500)
    current_app.config["RECOVERY_MODE"] = False
    session.clear()
    flash("Backup restored successfully.", "success")
    if business_defaults_setup_is_complete():
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.welcome"))


def _render_restore_error(message: str):
    return render_template(
        "data_safety.html",
        active_page="data_safety",
        recovery_mode=current_app.config.get("RECOVERY_MODE", False),
        restore_error=message,
    ), 400


@main.route("/events/new", methods=("GET", "POST"))
def calculator():
    """Display the Event Inputs screen."""
    errors = {}
    workspace = False
    identity = None
    analysis = None
    active_event_id = None
    active_scenario_id = None
    active_scenario_name = None
    save_error = None
    if request.method == "POST":
        identity, form_values, errors, result = (
            validate_and_calculate_event_analysis(
                request.form
            )
        )
        if result is not None:
            try:
                scenario = scenario_from_form_values(
                    form_values, "Original estimate"
                )
                active_event_id, active_scenario_id = (
                    create_event_with_initial_scenario(identity, scenario)
                )
            except sqlite3.Error:
                current_app.logger.exception(
                    "Event and initial Scenario persistence failed."
                )
                save_error = (
                    "The event could not be saved. Please try again."
                )
            else:
                workspace = True
                _, identity, scenario = load_event_scenario(
                    active_scenario_id
                )
                form_values = event_scenario_to_form(identity, scenario)
                active_scenario_name = scenario.scenario_name
                analysis = calculation_result_data(
                    calculate_event_scenario(scenario)
                )
    else:
        form_values = blank_event_inputs_form(load_business_defaults())

    return render_template(
        "calculator.html",
        active_page="saved_events" if workspace else "calculator",
        form_values=form_values,
        errors=errors,
        protection_reductions=protection_reductions(form_values),
        show_event_protection=weather_allows_protection(form_values),
        workspace=workspace,
        event_identity=identity,
        analysis=analysis,
        active_event_id=active_event_id,
        active_scenario_id=active_scenario_id,
        active_scenario_name=active_scenario_name,
        workspace_scenarios=(
            _workspace_scenario_summaries(active_event_id)
            if workspace else []
        ),
        save_error=save_error,
    )


@main.post("/event-inputs/demand-preview")
def demand_preview():
    """Return a calculation-backed shared-demand preview without saving."""
    preview, errors = calculate_demand_preview(request.form)
    if errors:
        return jsonify({"ready": False, "errors": errors})
    return jsonify({"ready": True, **preview})


@main.post("/event-inputs/finish-later")
def finish_event_inputs_later():
    """Return from a locally preserved incomplete Event Inputs draft."""
    flash("Your event draft is saved on this device.", "info")
    return redirect(url_for("main.dashboard"))


@main.post("/event-inputs/warnings")
def event_input_warnings():
    """Return contextual structured warnings without persistence writes."""
    _, _, errors, result = validate_and_calculate_event_analysis(
        request.form,
        require_identity=False,
    )
    if errors:
        return jsonify({"ready": False, "warnings": []})
    return jsonify({"ready": True, "warnings": customer_warning_data(result)})


@main.get("/data-safety/sample-format")
def download_sample_format():
    """Download a harmless description of the versioned backup format."""
    sample = {
        "product": "Food Truck Event Profit Calculator",
        "backup_extension": ".ftbackup",
        "contents": ["manifest.json", "database.sqlite"],
        "includes": ["business defaults", "events", "scenarios", "labor", "additional costs"],
        "note": "Use Export all data in the app to create a restorable backup.",
    }
    return send_file(
        BytesIO(json.dumps(sample, indent=2).encode("utf-8")),
        as_attachment=True,
        download_name="food-truck-calculator-backup-format.json",
        mimetype="application/json",
    )


def _require_data_action_confirmation(expected: str):
    if request.form.get("confirmation") != expected:
        flash("Confirm the exact data you want to remove.", "error")
        return redirect(url_for("main.data_safety"))
    return None


@main.post("/data-safety/delete-events")
def delete_all_saved_events():
    """Delete saved Events while preserving Business Defaults."""
    rejected = _require_data_action_confirmation("delete-events")
    if rejected:
        return rejected
    delete_all_events()
    flash("All saved events and scenarios were deleted.", "success")
    return redirect(url_for("main.data_safety"))


@main.post("/data-safety/reset-defaults")
def reset_saved_defaults():
    """Reset Business Defaults while preserving saved Events."""
    rejected = _require_data_action_confirmation("reset-defaults")
    if rejected:
        return rejected
    reset_business_defaults()
    session.pop("onboarding_deferred", None)
    flash("Business defaults were reset.", "success")
    return redirect(url_for("main.data_safety"))


@main.post("/data-safety/clear")
def clear_all_customer_data():
    """Clear all customer-created data after high-friction confirmation."""
    if request.form.get("confirmation_phrase", "").strip() != "CLEAR ALL DATA":
        flash('Type "CLEAR ALL DATA" to confirm.', "error")
        return redirect(url_for("main.data_safety"))
    clear_customer_data()
    session.clear()
    flash("All customer data was cleared.", "success")
    return redirect(url_for("main.welcome"))


@main.post("/event-analysis/calculate")
def recalculate_event_analysis():
    """Validate and calculate current workspace assumptions without saving."""
    _, _, errors, result = validate_and_calculate_event_analysis(
        request.form
    )
    if errors:
        return jsonify(
            {
                "valid": False,
                "errors": errors,
                "status": (
                    "Results have not updated. Correct the highlighted "
                    "fields."
                ),
            }
        )
    return jsonify(
        {
            "valid": True,
            "result": calculation_result_data(result),
            "status": "Analysis updated.",
        }
    )


@main.post("/event-analysis/save")
def save_event_analysis():
    """Save current valid assumptions as a sibling or overwrite the active one."""
    _, values, errors, result = validate_and_calculate_event_analysis(
        request.form
    )
    if errors:
        return jsonify(
            {
                "saved": False,
                "errors": errors,
                "message": "Correct the highlighted values before saving.",
            }
        )
    try:
        event_id = int(request.form.get("active_event_id", ""))
        scenario_id = int(request.form.get("active_scenario_id", ""))
    except ValueError:
        return jsonify(
            {
                "saved": False,
                "save_error": "The active scenario could not be identified.",
            }
        ), 400

    mode = request.form.get("save_mode", "new")
    try:
        stored_event_id, _, stored = load_event_scenario(scenario_id)
        if stored_event_id != event_id:
            raise ValueError("The active scenario does not match.")
        if mode == "new":
            name = request.form.get("scenario_name", "").strip()
            if not name:
                return jsonify(
                    {
                        "saved": False,
                        "scenario_name_error": "Scenario name is required.",
                    }
                )
            scenario = scenario_from_form_values(values, name)
            new_scenario_id = create_event_scenario(event_id, scenario)
            scenario_id = new_scenario_id
            active_name = name
            message = f'Scenario "{name}" saved.'
        elif mode == "overwrite":
            if request.form.get("overwrite_confirmed") != "true":
                return jsonify(
                    {
                        "saved": False,
                        "overwrite_error": (
                            "Confirm that you want to overwrite the "
                            "current scenario."
                        ),
                    }
                )
            scenario = scenario_from_form_values(
                values, stored.scenario_name
            )
            overwrite_event_scenario(scenario_id, scenario)
            active_name = stored.scenario_name
            message = f'Scenario "{active_name}" overwritten.'
        else:
            return jsonify(
                {"saved": False, "save_error": "Choose a save option."}
            )
    except ScenarioNameConflict as error:
        return jsonify(
            {
                "saved": False,
                "scenario_name_error": str(error),
            }
        )
    except (sqlite3.Error, ValueError):
        return jsonify(
            {
                "saved": False,
                "save_error": "The scenario could not be saved.",
            }
        )

    return jsonify(
        {
            "saved": True,
            "active_event_id": event_id,
            "active_scenario_id": scenario_id,
            "active_scenario_name": active_name,
            "result": calculation_result_data(result),
            "message": message,
        }
    )


@main.route("/defaults", methods=("GET", "POST"))
def defaults():
    """Display the Defaults screen."""
    errors = {}
    initial_setup = not business_defaults_setup_is_complete()
    persisted_defaults = load_business_defaults()
    if request.method == "POST":
        defaults_record, form_values, errors = validate_defaults_form(
            request.form
        )
        if defaults_record is not None:
            save_business_defaults(defaults_record)
            session.pop("onboarding_deferred", None)
            flash("Business defaults saved successfully.", "success")
            if (
                initial_setup
                and current_app.config.get("ENFORCE_SETUP", True)
            ):
                return redirect(url_for("main.dashboard"))
            return redirect(url_for("main.defaults"))
    else:
        form_values = defaults_to_form(persisted_defaults)

    return render_template(
        "defaults.html",
        active_page="defaults",
        form_values=form_values,
        errors=errors,
        initial_setup=initial_setup,
        active_step=request.form.get("wizard_step", "1"),
        snapshot_values=defaults_to_form(persisted_defaults),
    )


@main.post("/defaults/finish-later")
def finish_defaults_later():
    """Preserve browser-saved setup progress and return to Dashboard."""
    session["onboarding_deferred"] = True
    flash("Your setup progress is saved on this device.", "info")
    return redirect(url_for("main.dashboard"))


@main.get("/saved-events")
def saved_events():
    """Display saved Events grouped with their Scenarios."""
    return _render_saved_events()


@main.get("/events/<int:event_id>/scenarios/<int:scenario_id>")
def open_saved_scenario(event_id: int, scenario_id: int):
    """Open one persisted Scenario in the existing analysis workspace."""
    try:
        stored_event_id, identity, scenario = load_event_scenario(
            scenario_id
        )
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    form_values = event_scenario_to_form(identity, scenario)
    return render_template(
        "calculator.html",
        active_page="saved_events",
        form_values=form_values,
        errors={},
        protection_reductions=protection_reductions(form_values),
        show_event_protection=weather_allows_protection(form_values),
        workspace=True,
        event_identity=identity,
        analysis=calculation_result_data(
            calculate_event_scenario(scenario)
        ),
        active_event_id=event_id,
        active_scenario_id=scenario_id,
        active_scenario_name=scenario.scenario_name,
        workspace_scenarios=_workspace_scenario_summaries(event_id),
        save_error=None,
    )


@main.post("/events/<int:event_id>/scenarios/<int:scenario_id>/duplicate")
def duplicate_saved_scenario(event_id: int, scenario_id: int):
    """Create a distinct saved copy beside the active Scenario."""
    try:
        stored_event_id, _, scenario = load_event_scenario(scenario_id)
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    existing = {
        item["scenario_name"].casefold()
        for item in _workspace_scenario_summaries(event_id)
    }
    base = f"{scenario.scenario_name} Copy"
    name = base
    number = 2
    while name.casefold() in existing:
        name = f"{base} {number}"
        number += 1
    copied = replace(scenario, scenario_name=name)
    new_id = create_event_scenario(event_id, copied)
    flash(f'Scenario "{name}" duplicated.', "success")
    return redirect(
        url_for(
            "main.open_saved_scenario",
            event_id=event_id,
            scenario_id=new_id,
        )
    )


@main.post("/events/<int:event_id>/rename")
def rename_saved_event(event_id: int):
    name = request.form.get("event_name", "")
    if not name.strip():
        return _render_saved_events(
            event_errors={event_id: "Event name is required."},
            event_values={event_id: name},
        )
    if not rename_event(event_id, name):
        abort(404)
    flash("Event name updated.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/scenarios/<int:scenario_id>/rename")
def rename_saved_scenario(event_id: int, scenario_id: int):
    try:
        stored_event_id, _, _ = load_event_scenario(scenario_id)
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    name = request.form.get("scenario_name", "")
    if not name.strip():
        return _render_saved_events(
            scenario_errors={
                scenario_id: "Scenario name is required."
            },
            scenario_values={scenario_id: name},
        )
    try:
        renamed = rename_event_scenario(scenario_id, name)
    except ScenarioNameConflict as error:
        return _render_saved_events(
            scenario_errors={scenario_id: str(error)},
            scenario_values={scenario_id: name},
        )
    if not renamed:
        abort(404)
    flash("Scenario name updated.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/scenarios/<int:scenario_id>/delete")
def delete_saved_scenario(event_id: int, scenario_id: int):
    try:
        stored_event_id, _, scenario = load_event_scenario(scenario_id)
    except ValueError:
        abort(404)
    if stored_event_id != event_id:
        abort(404)
    if request.form.get("confirmed") != "yes":
        return _render_saved_events(
            scenario_errors={
                scenario_id: (
                    f'Confirm deletion of "{scenario.scenario_name}".'
                )
            }
        )
    try:
        deleted = delete_event_scenario(scenario_id)
    except FinalScenarioDeletionError as error:
        return _render_saved_events(
            scenario_errors={scenario_id: str(error)}
        )
    if not deleted:
        abort(404)
    flash("Scenario deleted.", "success")
    return redirect(url_for("main.saved_events"))


@main.post("/events/<int:event_id>/delete")
def delete_saved_event(event_id: int):
    events = list_saved_events()
    event = next((item for item in events if item["id"] == event_id), None)
    if event is None:
        abort(404)
    if request.form.get("confirmed") != "yes":
        return _render_saved_events(
            event_errors={
                event_id: (
                    f'Confirm deletion of "{event["event_name"]}" and '
                    f'all {event["scenario_count"]} saved scenarios.'
                )
            }
        )
    try:
        deleted = delete_event(event_id)
    except sqlite3.Error:
        return _render_saved_events(
            event_errors={
                event_id: "The event could not be deleted."
            }
        )
    if not deleted:
        abort(404)
    flash("Event and its saved scenarios deleted.", "success")
    return redirect(url_for("main.saved_events"))


@main.route("/comparison", methods=("GET", "POST"))
def comparison():
    """Validate selected Scenarios and render read-only comparison."""
    if request.method == "GET":
        return redirect(url_for("main.saved_events"))
    raw_ids = request.form.getlist("scenario_id")
    if len(raw_ids) < 2:
        return _render_saved_events(
            comparison_error="Select at least two Scenarios to compare.",
            selected_scenarios=raw_ids,
        )
    if len(raw_ids) > 4:
        return _render_saved_events(
            comparison_error="Select no more than four Scenarios.",
            selected_scenarios=raw_ids,
        )
    if len(set(raw_ids)) != len(raw_ids):
        return _render_saved_events(
            comparison_error=(
                "The same Scenario cannot be selected more than once."
            ),
            selected_scenarios=raw_ids,
        )
    try:
        scenario_ids = [int(value) for value in raw_ids]
        comparison_data = build_comparison(scenario_ids)
    except (ValueError, sqlite3.Error):
        return _render_saved_events(
            comparison_error=(
                "One or more selected Scenarios are no longer available."
            ),
            selected_scenarios=raw_ids,
        )
    event_id = comparison_data["columns"][0]["event_id"]
    event = next(
        item for item in list_saved_events() if item["id"] == event_id
    )
    return render_template(
        "comparison.html",
        active_page="saved_events",
        comparison=comparison_data,
        comparison_event=event,
    )


def _render_saved_events(
    *,
    event_errors: dict | None = None,
    event_values: dict | None = None,
    scenario_errors: dict | None = None,
    scenario_values: dict | None = None,
    comparison_error: str | None = None,
    selected_scenarios: list[str] | None = None,
):
    all_events = list_saved_events()
    for event in all_events:
        latest = event["scenarios"][0]
        _, _, scenario = load_event_scenario(latest["id"])
        result = calculate_event_scenario(scenario)
        evaluation = result.profit_target_evaluation
        if result.business_profit < 0:
            status, tone = "Not worth it", "danger"
        elif evaluation is not None and evaluation.is_met is False:
            status, tone = "Borderline", "warning"
        else:
            status, tone = "Worth it", "success"
        event.update(
            recommendation=status,
            recommendation_key=status.lower().replace(" ", "-"),
            recommendation_tone=tone,
            latest_scenario_id=latest["id"],
            latest_scenario_name=latest["scenario_name"],
        )
    status_counts = {
        key: sum(event["recommendation_key"] == key for event in all_events)
        for key in ("worth-it", "borderline", "not-worth-it")
    }
    search = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    sort = request.args.get("sort", "modified")
    filtered = all_events
    if search:
        folded = search.casefold()
        filtered = [
            event for event in filtered
            if folded in event["event_name"].casefold()
            or folded in event["location"].casefold()
            or any(folded in item["scenario_name"].casefold() for item in event["scenarios"])
        ]
    if status_filter in status_counts:
        filtered = [event for event in filtered if event["recommendation_key"] == status_filter]
    if sort == "name":
        filtered.sort(key=lambda item: (item["event_name"].casefold(), item["id"]))
    elif sort == "event-date":
        filtered.sort(key=lambda item: (item["event_date"], item["id"]), reverse=True)
    elif sort == "recommendation":
        order = {"worth-it": 0, "borderline": 1, "not-worth-it": 2}
        filtered.sort(key=lambda item: (order[item["recommendation_key"]], item["event_name"].casefold()))
    page_size = 25
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    page_count = max((len(filtered) + page_size - 1) // page_size, 1)
    page = min(page, page_count)
    start = (page - 1) * page_size
    events = filtered[start:start + page_size]
    recent_cutoff = (datetime.now().astimezone().date() - timedelta(days=6)).isoformat()
    recently_updated = sum(
        event["last_modified"][:10] >= recent_cutoff
        for event in all_events
    )
    return render_template(
        "saved_events.html",
        active_page="saved_events",
        events=events,
        has_events=bool(all_events),
        total_events=len(all_events),
        total_scenarios=sum(event["scenario_count"] for event in all_events),
        recently_updated=recently_updated,
        status_counts=status_counts,
        search=search,
        status_filter=status_filter,
        sort=sort,
        page=page,
        page_count=page_count,
        result_start=(start + 1 if filtered else 0),
        result_end=min(start + page_size, len(filtered)),
        result_count=len(filtered),
        event_errors=event_errors or {},
        event_values=event_values or {},
        scenario_errors=scenario_errors or {},
        scenario_values=scenario_values or {},
        comparison_error=comparison_error,
        selected_scenarios=set(selected_scenarios or []),
    )
    delete_event,
    delete_event_scenario,
    list_saved_events,
    rename_event,
    rename_event_scenario,
    business_defaults_setup_is_complete,
