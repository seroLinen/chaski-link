import json
import os
from datetime import datetime

LOG_FILE = 'study_pulse.json'

def log_session():
    print("--- Chaski-Link: Study Pulse ---")
    chapter = input("Chapter worked on: ")
    pages = input("Pages covered: ")
    
    # Scale of 1-10 (1 = Energized, 10 = Fried)
    burnout = input("Burnout Level (1-10): ") 
    notes = input("Quick note for your future self: ")

    new_entry = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "chapter": chapter,
        "pages": pages,
        "burnout_score": burnout,
        "notes": notes
    }

    # Load existing data or start a new list
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(new_entry)

    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    print("\n[Pulse Logged] Data doesn't lie, John. Progress is progress.")

if __name__ == "__main__":
    log_session()