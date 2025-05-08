import sqlite3
import json
import datetime
import os

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect("LLM_analyzer_hs.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repository_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            structure TEXT NOT NULL,
            profile TEXT NOT NULL,
            sources_used TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS change_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            changes TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_url ON repository_analyses(repo_url)")
    conn.commit()
    return conn

def store_analysis(conn, results):
    """Store analysis results"""
    cursor = conn.cursor()
    sources_used = results["profile"].get("sources_used", {"llm": 0, "static": 0})
    cursor.execute("""
        INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        results["repository_url"],
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        results["commit_hash"],
        json.dumps(results["structure"]),
        json.dumps(results["profile"]),
        json.dumps(sources_used),
    ))
    conn.commit()

def compare_and_log_changes(conn, results):
    """Compare with previous analysis and log changes"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT structure, profile, commit_hash
        FROM repository_analyses
        WHERE repo_url = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (results["repository_url"],))
    previous = cursor.fetchone()
    if not previous:
        return {"changes": [], "message": "No previous analysis found."}
    
    prev_structure, prev_profile, prev_commit_hash = json.loads(previous[0]), json.loads(previous[1]), previous[2]
    curr_structure, curr_profile, curr_commit_hash = results["structure"], results["profile"], results["commit_hash"]
    
    changes = []
    if prev_commit_hash != curr_commit_hash:
        changes.append(f"New commit: {curr_commit_hash[:7]} (prev: {prev_commit_hash[:7]})")
    
    prev_files = set(os.path.join(dir_path, f) for dir_path, files in prev_structure.items() for f in files)
    curr_files = set(os.path.join(dir_path, f) for dir_path, files in curr_structure.items() for f in files)
    if new_files := curr_files - prev_files:
        changes.append(f"New files: {', '.join(new_files)}")
    if deleted_files := prev_files - curr_files:
        changes.append(f"Removed files: {', '.join(deleted_files)}")
    
    threshold = 0.1
    prev_memory = float(prev_profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", ""))
    curr_memory = float(curr_profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", ""))
    if prev_memory > 0 and abs(curr_memory - prev_memory) / prev_memory > threshold:
        changes.append(f"Memory: {curr_memory}MB (prev: {prev_memory}MB)")
    
    prev_cores = prev_profile["recommendations"]["cpu"]["recommended_cores"]
    curr_cores = curr_profile["recommendations"]["cpu"]["recommended_cores"]
    if curr_cores != prev_cores:
        changes.append(f"CPU cores: {curr_cores} (prev: {prev_cores})")
    
    prev_bandwidth = float(prev_profile["recommendations"]["bandwidth"]["peak_requirement"].replace("Mbps", ""))
    curr_bandwidth = float(curr_profile["recommendations"]["bandwidth"]["peak_requirement"].replace("Mbps", ""))
    if prev_bandwidth > 0 and abs(curr_bandwidth - prev_bandwidth) / prev_bandwidth > threshold:
        changes.append(f"Bandwidth: {curr_bandwidth}Mbps (prev: {prev_bandwidth}Mbps)")
    
    prev_sources = prev_profile.get("sources_used", {"llm": 0, "static": 0})
    curr_sources = curr_profile.get("sources_used", {"llm": 0, "static": 0})
    for source in ["llm", "static"]:
        if curr_sources[source] != prev_sources[source]:
            changes.append(f"{source.capitalize()} analysis: {curr_sources[source]} (prev: {prev_sources[source]})")
    
    if changes:
        cursor.execute("""
            INSERT INTO change_logs (repo_url, timestamp, changes)
            VALUES (?, ?, ?)
        """, (
            results["repository_url"],
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            json.dumps(changes),
        ))
        conn.commit()
    
    return {"changes": changes, "message": "Changes detected." if changes else "No changes."}