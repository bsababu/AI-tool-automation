import time
import sqlite3
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

class ResourceFeedbackSystem:
    def __init__(self, db_path='resource_feedback.db'):
        self.db_path = db_path
        self._init_db()
        self.prediction_models = {
            'memory': None,
            'cpu': None,
            'bandwidth': None
        }
        self._train_models()
    
    def _init_db(self):
        """Initialize the feedback database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT UNIQUE,
            last_analyzed TIMESTAMP,
            profile TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actual_resource_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER,
            timestamp TIMESTAMP,
            memory_mb REAL,
            cpu_cores REAL,
            bandwidth_kbps REAL,
            FOREIGN KEY (repo_id) REFERENCES repositories(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_analysis(self, repo_url, profile):
        """Store repository analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store or update repository profile
        cursor.execute('''
        INSERT INTO repositories (repo_url, last_analyzed, profile)
        VALUES (?, ?, ?)
        ON CONFLICT(repo_url) DO UPDATE
                       ''')