import logging
import sys
import os

import csv
import io
import re

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import get_db, init_db
from datetime import datetime

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), 'testwatch.log')),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger('testwatch')

app = Flask(__name__)


@app.before_request
def log_request():
    logger.info("Request: %s %s", request.method, request.path)


# --- Pages ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stopwatch')
def stopwatch():
    return render_template('stopwatch.html')


@app.route('/statistics')
def statistics():
    return render_template('statistics.html')


@app.route('/preparation')
def preparation():
    return render_template('preparation.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


# --- API: Activity Types ---

@app.route('/api/activity-types', methods=['GET'])
def get_activity_types():
    db = get_db()
    rows = db.execute("SELECT * FROM activity_types ORDER BY sort_order").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/activity-types', methods=['POST'])
def create_activity_type():
    data = request.json
    db = get_db()
    try:
        max_order = db.execute("SELECT COALESCE(MAX(sort_order),0) FROM activity_types").fetchone()[0]
        db.execute("INSERT INTO activity_types (name, color, sort_order) VALUES (?, ?, ?)",
                   (data['name'], data['color'], max_order + 1))
        db.commit()
    finally:
        db.close()
    return jsonify({"ok": True}), 201


@app.route('/api/activity-types/<int:id>', methods=['PUT'])
def update_activity_type(id):
    data = request.json
    db = get_db()
    db.execute("UPDATE activity_types SET name=?, color=? WHERE id=?",
               (data['name'], data['color'], id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route('/api/activity-types/<int:id>', methods=['DELETE'])
def delete_activity_type(id):
    db = get_db()
    db.execute("DELETE FROM activity_types WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: Workstreams ---

@app.route('/api/workstreams', methods=['GET'])
def get_workstreams():
    db = get_db()
    rows = db.execute("SELECT * FROM workstreams ORDER BY name").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/workstreams', methods=['POST'])
def create_workstream():
    data = request.json
    db = get_db()
    try:
        db.execute("INSERT INTO workstreams (name) VALUES (?)", (data['name'],))
        db.commit()
    finally:
        db.close()
    return jsonify({"ok": True}), 201


@app.route('/api/workstreams/<int:id>', methods=['DELETE'])
def delete_workstream(id):
    db = get_db()
    db.execute("DELETE FROM workstreams WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: Scenarios ---

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    db = get_db()
    rows = db.execute("SELECT * FROM scenarios ORDER BY name").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/scenarios', methods=['POST'])
def create_scenario():
    data = request.json
    db = get_db()
    try:
        c = db.execute("INSERT INTO scenarios (name) VALUES (?)", (data['name'],))
        db.commit()
        scenario_id = c.lastrowid
    finally:
        db.close()
    return jsonify({"ok": True, "id": scenario_id}), 201


@app.route('/api/scenarios/<int:id>', methods=['PUT'])
def update_scenario(id):
    data = request.json
    db = get_db()
    db.execute("UPDATE scenarios SET name=? WHERE id=?", (data['name'], id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route('/api/scenarios/<int:id>', methods=['DELETE'])
def delete_scenario(id):
    db = get_db()
    db.execute("DELETE FROM scenarios WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: Ranks ---

@app.route('/api/scenarios/<int:scenario_id>/ranks', methods=['GET'])
def get_ranks(scenario_id):
    db = get_db()
    rows = db.execute("""
        SELECT r.*, w.name as workstream_name, r.jira_key
        FROM ranks r
        LEFT JOIN workstreams w ON r.workstream_id = w.id
        WHERE r.scenario_id = ?
        ORDER BY r.sort_order
    """, (scenario_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/scenarios/<int:scenario_id>/ranks', methods=['POST'])
def create_rank(scenario_id):
    data = request.json
    db = get_db()
    try:
        max_order = db.execute("SELECT COALESCE(MAX(sort_order),0) FROM ranks WHERE scenario_id=?",
                               (scenario_id,)).fetchone()[0]
        db.execute("""INSERT INTO ranks (scenario_id, rank_id, description, workstream_id, sort_order)
                      VALUES (?, ?, ?, ?, ?)""",
                   (scenario_id, data['rank_id'], data.get('description', ''),
                    data.get('workstream_id'), max_order + 1))
        db.commit()
    finally:
        db.close()
    return jsonify({"ok": True}), 201


@app.route('/api/ranks/<int:id>', methods=['PUT'])
def update_rank(id):
    data = request.json
    db = get_db()
    db.execute("""UPDATE ranks SET rank_id=?, description=?, workstream_id=?, sort_order=? WHERE id=?""",
               (data['rank_id'], data.get('description', ''),
                data.get('workstream_id'), data.get('sort_order', 0), id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route('/api/ranks/<int:id>', methods=['DELETE'])
def delete_rank(id):
    db = get_db()
    db.execute("DELETE FROM ranks WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: CSV Import ---

@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    # Derive scenario name from filename (without extension and suffix like -b)
    base_name = os.path.splitext(file.filename)[0]
    # Remove suffixes like -b, -c etc. to get the Jira key
    scenario_name = re.sub(r'-[a-zA-Z]$', '', base_name)

    try:
        raw = file.read().decode('utf-8-sig')
        reader = csv.reader(io.StringIO(raw), delimiter=';')
        header = next(reader)
        header = [h.strip() for h in header]
        logger.info("CSV import: file=%s, columns=%s", file.filename, header)

        # Find column indices
        col_map = {h.lower(): i for i, h in enumerate(header)}
        test_key_idx = col_map.get('test key')
        status_idx = col_map.get('status')
        executed_by_idx = col_map.get('executed by')
        assignee_idx = col_map.get('assignee')

        if test_key_idx is None:
            return jsonify({"error": "CSV must have a 'Test Key' column"}), 400

        rows = list(reader)
        logger.info("CSV import: %d rows found", len(rows))

        db = get_db()
        try:
            # Create scenario (or find existing)
            existing = db.execute("SELECT id FROM scenarios WHERE name=?", (scenario_name,)).fetchone()
            if existing:
                scenario_id = existing['id']
            else:
                c = db.execute("INSERT INTO scenarios (name) VALUES (?)", (scenario_name,))
                scenario_id = c.lastrowid

            # Workstream cache: prefix -> workstream_id
            ws_cache = {}
            for ws in db.execute("SELECT id, name FROM workstreams").fetchall():
                ws_cache[ws['name']] = ws['id']

            imported = 0
            for i, row in enumerate(rows):
                if len(row) <= test_key_idx:
                    continue
                test_key = row[test_key_idx].strip()
                if not test_key:
                    continue

                # Extract workstream prefix from Jira key (e.g. OFCON-6840 -> OFCON)
                prefix_match = re.match(r'^([A-Za-z]+)-', test_key)
                ws_name = prefix_match.group(1) if prefix_match else ''

                # Get or create workstream
                ws_id = None
                if ws_name:
                    if ws_name not in ws_cache:
                        c = db.execute("INSERT INTO workstreams (name) VALUES (?)", (ws_name,))
                        ws_cache[ws_name] = c.lastrowid
                    ws_id = ws_cache[ws_name]

                # Build description from status and executor
                desc_parts = []
                if status_idx is not None and len(row) > status_idx:
                    status = row[status_idx].strip()
                    if status:
                        desc_parts.append(status)
                if executed_by_idx is not None and len(row) > executed_by_idx:
                    executor = row[executed_by_idx].strip()
                    if executor:
                        desc_parts.append(executor)
                description = ' | '.join(desc_parts)

                db.execute("""INSERT INTO ranks (scenario_id, rank_id, description, workstream_id, sort_order, jira_key)
                              VALUES (?, ?, ?, ?, ?, ?)""",
                           (scenario_id, test_key, description, ws_id, i + 1, test_key))
                imported += 1

            db.commit()
            logger.info("CSV import: scenario=%s (id=%d), %d ranks imported", scenario_name, scenario_id, imported)
            return jsonify({
                "ok": True,
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "imported": imported
            }), 201

        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    except Exception as e:
        logger.exception("CSV import failed: %s", e)
        return jsonify({"error": str(e)}), 500


# --- API: Sessions ---

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    db = get_db()
    rows = db.execute("""
        SELECT s.*, sc.name as scenario_name
        FROM sessions s
        JOIN scenarios sc ON s.scenario_id = sc.id
        ORDER BY s.started_at DESC
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    db = get_db()
    try:
        now = datetime.utcnow().isoformat()
        c = db.execute("INSERT INTO sessions (scenario_id, name, started_at) VALUES (?, ?, ?)",
                       (data['scenario_id'], data.get('name', ''), now))
        db.commit()
        session_id = c.lastrowid
    finally:
        db.close()
    return jsonify({"ok": True, "id": session_id, "started_at": now}), 201


@app.route('/api/sessions/<int:id>/end', methods=['POST'])
def end_session(id):
    db = get_db()
    now = datetime.utcnow().isoformat()
    db.execute("UPDATE sessions SET ended_at=? WHERE id=?", (now, id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: Time Entries ---

@app.route('/api/sessions/<int:session_id>/entries', methods=['GET'])
def get_entries(session_id):
    db = get_db()
    rows = db.execute("""
        SELECT te.*, at.name as activity_name, at.color as activity_color,
               r.rank_id as rank_label, r.description as rank_description,
               w.name as workstream_name
        FROM time_entries te
        JOIN activity_types at ON te.activity_type_id = at.id
        JOIN ranks r ON te.rank_id = r.id
        LEFT JOIN workstreams w ON r.workstream_id = w.id
        WHERE te.session_id = ?
        ORDER BY te.seq_order
    """, (session_id,)).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/sessions/<int:session_id>/entries', methods=['POST'])
def create_entry(session_id):
    data = request.json
    db = get_db()
    try:
        max_seq = db.execute("SELECT COALESCE(MAX(seq_order),0) FROM time_entries WHERE session_id=?",
                             (session_id,)).fetchone()[0]
        now = datetime.utcnow().isoformat()
        c = db.execute("""INSERT INTO time_entries
                          (session_id, rank_id, activity_type_id, started_at, seq_order)
                          VALUES (?, ?, ?, ?, ?)""",
                       (session_id, data['rank_id'], data['activity_type_id'], now, max_seq + 1))
        db.commit()
        entry_id = c.lastrowid
    finally:
        db.close()
    return jsonify({"ok": True, "id": entry_id, "started_at": now}), 201


@app.route('/api/entries/<int:id>', methods=['PUT'])
def update_entry(id):
    data = request.json
    db = get_db()
    updates = []
    params = []
    if 'rank_id' in data:
        updates.append("rank_id=?")
        params.append(data['rank_id'])
    if 'activity_type_id' in data:
        updates.append("activity_type_id=?")
        params.append(data['activity_type_id'])
    if 'ended_at' in data:
        updates.append("ended_at=?")
        params.append(data['ended_at'])
    if 'duration_seconds' in data:
        updates.append("duration_seconds=?")
        params.append(data['duration_seconds'])
    if updates:
        params.append(id)
        db.execute(f"UPDATE time_entries SET {', '.join(updates)} WHERE id=?", params)
        db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route('/api/entries/<int:id>', methods=['DELETE'])
def delete_entry(id):
    db = get_db()
    db.execute("DELETE FROM time_entries WHERE id=?", (id,))
    db.commit()
    db.close()
    return jsonify({"ok": True})


# --- API: Statistics ---

@app.route('/api/statistics/session/<int:session_id>')
def session_statistics(session_id):
    db = get_db()

    # Time by activity type
    by_activity = db.execute("""
        SELECT at.name, at.color, SUM(te.duration_seconds) as total_seconds, COUNT(*) as count
        FROM time_entries te
        JOIN activity_types at ON te.activity_type_id = at.id
        WHERE te.session_id = ? AND te.duration_seconds > 0
        GROUP BY at.id
        ORDER BY total_seconds DESC
    """, (session_id,)).fetchall()

    # Time by workstream
    by_workstream = db.execute("""
        SELECT COALESCE(w.name, 'Unassigned') as name, SUM(te.duration_seconds) as total_seconds, COUNT(*) as count
        FROM time_entries te
        JOIN ranks r ON te.rank_id = r.id
        LEFT JOIN workstreams w ON r.workstream_id = w.id
        WHERE te.session_id = ? AND te.duration_seconds > 0
        GROUP BY w.id
        ORDER BY total_seconds DESC
    """, (session_id,)).fetchall()

    # Time by rank
    by_rank = db.execute("""
        SELECT r.rank_id, r.description, COALESCE(w.name, '') as workstream_name,
               SUM(te.duration_seconds) as total_seconds, COUNT(*) as count
        FROM time_entries te
        JOIN ranks r ON te.rank_id = r.id
        LEFT JOIN workstreams w ON r.workstream_id = w.id
        WHERE te.session_id = ? AND te.duration_seconds > 0
        GROUP BY r.id
        ORDER BY r.sort_order
    """, (session_id,)).fetchall()

    # Waste time (non-execution activities) by workstream
    waste_by_workstream = db.execute("""
        SELECT COALESCE(w.name, 'Unassigned') as name,
               at.name as activity_name, at.color,
               SUM(te.duration_seconds) as total_seconds
        FROM time_entries te
        JOIN activity_types at ON te.activity_type_id = at.id
        JOIN ranks r ON te.rank_id = r.id
        LEFT JOIN workstreams w ON r.workstream_id = w.id
        WHERE te.session_id = ? AND te.duration_seconds > 0
              AND at.name != 'Test execution'
        GROUP BY w.id, at.id
        ORDER BY w.name, total_seconds DESC
    """, (session_id,)).fetchall()

    db.close()
    return jsonify({
        "by_activity": [dict(r) for r in by_activity],
        "by_workstream": [dict(r) for r in by_workstream],
        "by_rank": [dict(r) for r in by_rank],
        "waste_by_workstream": [dict(r) for r in waste_by_workstream],
    })


@app.errorhandler(Exception)
def handle_error(e):
    logger.exception("Unhandled error: %s", e)
    return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Initializing database...")
    init_db()
    logger.info("Starting TestWatch on http://127.0.0.1:5050")
    app.run(debug=True, port=5050)
