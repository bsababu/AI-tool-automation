import sqlite3
import json
import datetime
import os

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect("analysis_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repository_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            commit_hash TEXT NOT NULL,
            structure TEXT NOT NULL,
            profile TEXT NOT NULL,
            sources_used TEXT NOT NULL,
            static_metrics TEXT NOT NULL DEFAULT '{}',
            cloud_configs TEXT NOT NULL DEFAULT '{}'
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cloud_config_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            platform TEXT NOT NULL,
            config_path TEXT NOT NULL,
            feedback_score INTEGER,
            feedback_notes TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_url ON repository_analyses(repo_url)")
    try:
        cursor.execute("ALTER TABLE repository_analyses ADD COLUMN static_metrics TEXT NOT NULL DEFAULT '{}'")
        cursor.execute("ALTER TABLE repository_analyses ADD COLUMN cloud_configs TEXT NOT NULL DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    return conn

def save_to_jsonl(results):
    """Save analysis results to a JSONL file"""
    results_dir = "./Results/"
    os.makedirs(results_dir, exist_ok=True)
    jsonl_path = os.path.join(results_dir, "analyses.jsonl")
    
    # Prepare JSON object for JSONL
    analysis_record = {
        "repo_url": results["repository_url"],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "commit_hash": results["commit_hash"],
        "structure": results["structure"],
        "profile": results["profile"],
        "sources_used": results["profile"].get("sources_used", {"llm": 0, "static": 0}),
        "static_metrics": results["profile"].get("static_metrics", {}),
        "cloud_configs": results.get("cloud_configs", {})
    }
    
    with open(jsonl_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(analysis_record, ensure_ascii=False) + '\n')
    
    return jsonl_path

def store_analysis(conn, results):
    """Store analysis results in SQLite and JSONL"""
    cursor = conn.cursor()
    sources_used = results["profile"].get("sources_used", {"llm": 0, "static": 0})
    static_metrics = results["profile"].get("static_metrics", {})
    cloud_configs = results.get("cloud_configs", {})
    
    cursor.execute("""
        INSERT INTO repository_analyses 
        (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics, cloud_configs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        results["repository_url"],
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        results["commit_hash"],
        json.dumps(results["structure"]),
        json.dumps(results["profile"]),
        json.dumps(sources_used),
        json.dumps(static_metrics),
        json.dumps(cloud_configs),
    ))
    conn.commit()
    
    # Save to JSONL
    jsonl_path = save_to_jsonl(results)
    print(f"Saved analysis to JSONL at {jsonl_path}")

def store_cloud_config_feedback(conn, repo_url, platform, config_path, feedback_score, feedback_notes=""):
    """Store feedback about generated cloud configurations"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cloud_config_feedback 
        (repo_url, timestamp, platform, config_path, feedback_score, feedback_notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        repo_url,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        platform,
        config_path,
        feedback_score,
        feedback_notes
    ))
    conn.commit()

def get_cloud_config_feedback(repo_url, platform=None):
    """Retrieve feedback for cloud configurations"""
    conn = sqlite3.connect("analysis_history.db")
    try:
        cursor = conn.cursor()
        if platform:
            cursor.execute("""
                SELECT platform, config_path, feedback_score, feedback_notes, timestamp
                FROM cloud_config_feedback
                WHERE repo_url = ? AND platform = ?
                ORDER BY timestamp DESC
            """, (repo_url, platform))
        else:
            cursor.execute("""
                SELECT platform, config_path, feedback_score, feedback_notes, timestamp
                FROM cloud_config_feedback
                WHERE repo_url = ?
                ORDER BY timestamp DESC
            """, (repo_url,))
        results = cursor.fetchall()
        return [{
            "platform": r[0],
            "config_path": r[1],
            "feedback_score": r[2],
            "feedback_notes": r[3],
            "timestamp": r[4]
        } for r in results]
    finally:
        conn.close()

def compare_and_log_changes(conn, results):
    """Compare with previous analysis and log changes"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT structure, profile, commit_hash, static_metrics, cloud_configs
        FROM repository_analyses
        WHERE repo_url = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (results["repository_url"],))
    previous = cursor.fetchone()
    if not previous:
        return {"changes": [], "message": "No previous analysis found."}
    
    prev_structure = json.loads(previous[0])
    prev_profile = json.loads(previous[1])
    prev_commit_hash = previous[2]
    prev_metrics = json.loads(previous[3] or '{}')
    prev_configs = json.loads(previous[4] or '{}')
    
    curr_structure = results["structure"]
    curr_profile = results["profile"]
    curr_commit_hash = results["commit_hash"]
    curr_metrics = results["profile"].get("static_metrics", {})
    curr_configs = results.get("cloud_configs", {})
    
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
    
    # Add cloud configuration changes
    if prev_configs != curr_configs:
        changes.append("Cloud configurations have been updated")
        for platform in set(prev_configs.keys()) | set(curr_configs.keys()):
            if platform not in prev_configs:
                changes.append(f"Added {platform} configuration")
            elif platform not in curr_configs:
                changes.append(f"Removed {platform} configuration")
            elif prev_configs[platform] != curr_configs[platform]:
                changes.append(f"Updated {platform} configuration")
    
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

def get_latest_analysis(repo_url):
    """Retrieve the latest analysis for a given repository URL"""
    conn = sqlite3.connect("analysis_history.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT profile, timestamp, commit_hash, sources_used, static_metrics
            FROM repository_analyses
            WHERE repo_url = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (repo_url,))
        result = cursor.fetchone()
        if result:
            return {
                "profile": json.loads(result[0]),
                "timestamp": result[1],
                "commit_hash": result[2],
                "sources_used": json.loads(result[3]),
                "static_metrics": json.loads(result[4] or '{}'),
            }
        return None
    finally:
        conn.close()

def get_change_logs(repo_url):
    """Retrieve changed logs"""
    conn = sqlite3.connect("analysis_history.db")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, changes
            FROM change_logs
            WHERE repo_url = ?
            ORDER BY timestamp DESC
        """, (repo_url,))
        results = cursor.fetchall()
        return [{"timestamp": r[0], "changes": json.loads(r[1])} for r in results]
    finally:
        conn.close()

def summarize_analysis(repo_url):
    """Summarize the latest analysis for display"""
    try:
        analysis = get_latest_analysis(repo_url)
        if not analysis:
            return f"No analysis found for {repo_url}."
        
        profile = analysis["profile"]
        recommendations = profile.get("recommendations", {})
        memory = recommendations.get("memory", {}).get("recommended_allocation", "0.0MB")
        cpu = recommendations.get("cpu", {}).get("recommended_cores", 0)
        bandwidth = recommendations.get("bandwidth", {}).get("peak_requirement", "0.0Mbps")
        sources = analysis["sources_used"]
        
        return (
            f"Analysis Summary for {repo_url} (timestamp: {analysis['timestamp']}, commit: {analysis['commit_hash'][:7]}):\n"
            f"- Memory: {memory}\n"
            f"- CPU Cores: {cpu}\n"
            f"- Bandwidth: {bandwidth}\n"
        )
    except Exception as e:
        return f"Error retrieving analysis: {str(e)}"