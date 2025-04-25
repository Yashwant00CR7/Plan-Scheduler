# from datetime import datetime
# from pymongo.collection import Collection
# from bson import ObjectId
# from bson.errors import InvalidId

# def generate_user_plan(users_collection: Collection, subjects_collection: Collection, user_id: str):
#     try:
#         user_obj_id = ObjectId(user_id)
#     except InvalidId:
#         raise ValueError("Invalid userId format. Expected a valid MongoDB ObjectId.")

#     # Fetch learning times from users collection
#     user_doc = users_collection.find_one({"_id": user_obj_id})
#     if not user_doc:
#         raise ValueError("User not found.")

#     learning_slots = []
#     for routine in user_doc.get("dailyRoutine", []):
#         if routine.get("action") == "learning":
#             time_range = routine.get("time")
#             if time_range:
#                 learning_slots.append(time_range)

#     # Fetch subject plans from subjects collection
#     today = datetime.today().date()
#     user_subjects = subjects_collection.find({"userId": user_obj_id})

#     full_plan = []

#     for subject in user_subjects:
#         exam_date = subject.get("examDate")
#         difficulty = subject.get("examDifficulty", "MEDIUM").upper()
#         topics = subject.get("topics", [])
#         subject_name = subject.get("subjectName", "Unknown Subject")

#         if not exam_date or not topics:
#             continue

#         exam_date = exam_date.date() if isinstance(exam_date, datetime) else exam_date
#         days_left = (exam_date - today).days

#         if days_left <= 0:
#             continue

#         hours_per_day = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 2)
#         study_time_per_topic = hours_per_day / len(topics)

#         for day in range(1, days_left + 1):
#             plan_for_day = f"Day {day}: Subject {subject_name} " + " ".join([
#                 f"{topic['name']} for {round(study_time_per_topic, 1)} hrs" for topic in topics
#             ])
#             full_plan.append(plan_for_day)

#     return {
#         "learning_times": learning_slots,
#         "study_plan": full_plan
#     }
from datetime import datetime
from pymongo.collection import Collection
from bson import ObjectId
from bson.errors import InvalidId

def time_range_to_hours(time_range: str) -> float:
    """Converts 'HH:MM - HH:MM' to float hours"""
    start_str, end_str = time_range.split(" - ")
    start = datetime.strptime(start_str, "%H:%M")
    end = datetime.strptime(end_str, "%H:%M")
    duration = (end - start).seconds / 3600
    return round(duration, 2)

def generate_user_plan(users_collection: Collection, subjects_collection: Collection, user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise ValueError("Invalid userId format. Expected a valid MongoDB ObjectId.")

    # --- Fetch user document and learning slots ---
    user_doc = users_collection.find_one({"_id": user_obj_id})
    if not user_doc:
        raise ValueError("User not found.")

    raw_learning_slots = []
    for routine in user_doc.get("dailyRoutine", []):
        if routine.get("action") == "learning":
            time_range = routine.get("time")
            if time_range:
                raw_learning_slots.append(time_range)

    if not raw_learning_slots:
        return {"message": "No learning slots found for the user."}

    learning_slots = [
        {"time": slot, "duration": time_range_to_hours(slot)}
        for slot in raw_learning_slots
    ]

    # --- Fetch user's subjects ---
    today = datetime.today().date()
    user_subjects = list(subjects_collection.find({"userId": user_obj_id}))

    full_plan = []
    day = 1
    slot_index = 0  # rotate through learning slots

    for subject in user_subjects:
        exam_date = subject.get("examDate")
        difficulty = subject.get("examDifficulty", "MEDIUM").upper()
        topics = subject.get("topics", [])
        subject_name = subject.get("subjectName", "Unknown Subject")

        if not exam_date or not topics:
            continue

        exam_date = exam_date.date() if isinstance(exam_date, datetime) else exam_date
        days_left = (exam_date - today).days

        if days_left <= 0:
            continue

        # Calculate study time needed per topic
        total_hours = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 2)
        study_time_per_topic = total_hours / len(topics)

        if all(study_time_per_topic > slot["duration"] for slot in learning_slots):
            full_plan.append(
                f"Cannot schedule '{subject_name}' (each topic needs {round(study_time_per_topic,1)} hrs) "
                f"as it exceeds all available learning slots. Please increase learning time."
            )
            continue

        for topic in topics:
            # Rotate through days and slots
            scheduled = False
            for _ in range(days_left):
                for slot in learning_slots:
                    if study_time_per_topic <= slot["duration"]:
                        # Use full or part of the slot time for the topic
                        allocated_time = min(study_time_per_topic, slot["duration"])
                        remaining_time = slot["duration"] - allocated_time

                        # Add the topic to the plan
                        full_plan.append(
                            f"Day {day}: Subject {subject_name} - {topic['name']} in {slot['time']}, "
                            f"allocated {allocated_time} hrs"
                        )

                        # If there is remaining time, consider for other subjects in the same slot
                        if remaining_time > 0:
                            next_topic = next((t for t in topics if t != topic), None)
                            if next_topic:
                                full_plan.append(
                                    f"Day {day}: Subject {subject_name} - {next_topic['name']} in {slot['time']}, "
                                    f"allocated {remaining_time} hrs"
                                )

                        # Warn if allocated time is not enough for the whole topic
                        if allocated_time < study_time_per_topic:
                            full_plan.append(
                                f"Day {day}: WARNING: '{topic['name']}' could not be fully learned in {slot['time']}. "
                                f"Only {allocated_time} hrs allocated, but it needs {study_time_per_topic} hrs to complete."
                            )

                        day += 1
                        scheduled = True
                        break
                if scheduled:
                    break
            if not scheduled:
                full_plan.append(
                    f"Could not fit topic '{topic['name']}' from '{subject_name}' in any available slot."
                )

    return {
        "learning_times": [s["time"] for s in learning_slots],
        "study_plan": full_plan
    }
