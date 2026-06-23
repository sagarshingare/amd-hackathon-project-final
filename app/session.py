import pickle
import uuid
import os
import time

SESSION_TTL_SECONDS = 3600  # 1 hour

SESSION_DIR = "temp_sessions"

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def _get_session_path(session_id):
    return os.path.join(SESSION_DIR, f"{session_id}.pkl")

def create_session():
    """Creates a new session and returns its ID."""
    return str(uuid.uuid4())

def save_state(session_id, state):
    """Saves state to a session file."""
    with open(_get_session_path(session_id), "wb") as f:
        pickle.dump(state, f)

def load_state(session_id):
    """Loads state from a session file, returning None if not found or expired."""
    filepath = _get_session_path(session_id)
    if not os.path.exists(filepath) or time.time() - os.path.getmtime(filepath) > SESSION_TTL_SECONDS:
        if os.path.exists(filepath): os.remove(filepath)
        return None
    with open(filepath, "rb") as f:
        return pickle.load(f)