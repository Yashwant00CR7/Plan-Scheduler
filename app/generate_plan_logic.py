from datetime import datetime
from pymongo.collection import Collection
from bson import ObjectId
from bson.errors import InvalidId

def generate_user_plan(collection: Collection, user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise ValueError("Invalid userId format. Expected a valid MongoDB ObjectId.")

    today = datetime.today().date()
    user_subjects = collection.find({"userId": user_obj_id})

    full_plan = []

    for subject in user_subjects:
        exam_date = subject.get("examDate")
        difficulty = subject.get("examDifficulty", "MEDIUM").upper()
        topics = subject.get("topics", [])
        subject_name = subject.get("subjectName", "Unknown Subject")

        # Skip invalid records
        if not exam_date or not topics:
            continue

        exam_date = exam_date.date() if isinstance(exam_date, datetime) else exam_date
        days_left = (exam_date - today).days

        if days_left <= 0:
            continue  # skip if exam is today or past

        hours_per_day = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 2)
        study_time_per_topic = hours_per_day / len(topics)

        for day in range(1, days_left + 1):
            plan_for_day = f" Day {day}: Subject {subject_name} " + " ".join([
                f"{topic['name']} for {round(study_time_per_topic, 1)} hrs " for topic in topics 
            ])
            full_plan.append(plan_for_day)

    return full_plan
