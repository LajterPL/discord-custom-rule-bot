from datetime import datetime
from tinydb import TinyDB, where

def get_by_id(user_id):
    entries = User.db.search(where('id') == user_id)
    if len(entries) > 0:
        return from_entry(entries[0])
    return None

def from_entry(entry):
    return User(
        entry['id'],
        entry['points'],
        datetime.fromisoformat(entry['last_activity'])
    )

class User:
    db = TinyDB("users.json")

    def __init__(self, user_id: int, points: int = 0, last_activity: datetime = datetime.now()):
        self.id = user_id
        self.points = points
        self.last_activity = last_activity

    def save(self):
        User.db.upsert(
            {
                "id": self.id,
                "points": self.points,
                "last_activity": self.last_activity.isoformat()
            },
            where('id') == self.id
        )