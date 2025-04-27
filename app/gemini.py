from datetime import datetime
from pymongo.collection import Collection
from bson import ObjectId
from bson.errors import InvalidId
from collections import defaultdict
import google.genai as genai

# Function to convert time range (e.g. "08:00 - 10:00") to hours as a float (e.g. 2 hours)
def time_range_to_hours(time_range: str) -> float:
    start_str, end_str = time_range.split(" - ")
    start = datetime.strptime(start_str, "%H:%M")
    end = datetime.strptime(end_str, "%H:%M")
    duration = (end - start).seconds / 3600
    return round(duration, 2)

# Function to generate a study plan for a user
def generate_user_plan_with_gemini(users_collection: Collection, subjects_collection: Collection, user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise ValueError("Invalid userId format. Expected a valid MongoDB ObjectId.")

    # Fetch user document and daily learning slots
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

    # Fetch user subjects and exam details
    today = datetime.today().date()
    user_subjects = list(subjects_collection.find({"userId": user_obj_id}))

    # Sort subjects by exam date
    user_subjects = sorted(
        user_subjects,
        key=lambda x: (x.get("examDate") or datetime.max)
    )

    full_plan = []  # List to store the final study plan
    day = 1  # Day counter for scheduling
    day_plan = defaultdict(list)  # Dictionary to store topics scheduled for each day

    urgent_subjects = []  # Subjects with exams tomorrow
    normal_subjects = []  # Subjects with exams in the future

    subject_status = {}

    total_available_hours = sum(slot["duration"] for slot in learning_slots)
    total_required_hours = 0  # Total hours required to study all subjects

    for subject in user_subjects:
        exam_date = subject.get("examDate")
        difficulty = subject.get("examDifficulty", "MEDIUM").upper()
        topics = subject.get("topics", [])
        subject_name = subject.get("subjectName", "Unknown Subject")

        if not topics:
            full_plan.append(f"⚠️ Warning: Subject '{subject_name}' has no topics added.")
            continue

        if not exam_date:
            continue

        exam_date = exam_date.date() if isinstance(exam_date, datetime) else exam_date
        days_left = (exam_date - today).days - 1

        if days_left <= 0:
            continue

        if days_left == 1:
            urgent_subjects.append({
                "name": subject_name,
                "topics": topics,
                "difficulty": difficulty
            })
        else:
            normal_subjects.append({
                "name": subject_name,
                "topics": topics,
                "difficulty": difficulty,
                "days_left": days_left
            })

        subject_status[subject_name] = {
            "total_topics": len(topics),
            "scheduled_topics": 0
        }

        total_hours = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 2)
        total_required_hours += total_hours * len(topics)

    if total_available_hours < total_required_hours:
        full_plan.append(f"⚠️ Warning: Your available time ({total_available_hours} hrs) is less than the required time ({total_required_hours} hrs). Please adjust your learning plan.")

    # Handle urgent subjects (exams tomorrow)
    if urgent_subjects:
        total_available_hours = sum(slot["duration"] for slot in learning_slots)
        total_topics = sum(len(sub["topics"]) for sub in urgent_subjects)

        if total_topics == 0 or total_available_hours == 0:
            full_plan.append("No time available or no topics to schedule.")
        else:
            time_per_topic = round(total_available_hours / total_topics, 2)

            full_plan.append("Day 1 Plan (URGENT! Exam Tomorrow) 📢")

            slot_index = 0
            for subject in urgent_subjects:
                for topic in subject["topics"]:
                    remaining_time_needed = time_per_topic

                    while remaining_time_needed > 0 and slot_index < len(learning_slots):
                        slot = learning_slots[slot_index]

                        if slot["duration"] <= 0:
                            slot_index += 1
                            continue

                        allocated_time = min(slot["duration"], remaining_time_needed)
                        day_plan[day].append(
                            f"- {slot['time']}: {subject['name']} → {topic} ({allocated_time} hrs)"
                        )

                        subject_status[subject["name"]]["scheduled_topics"] += (1 if remaining_time_needed == time_per_topic else 0)

                        slot["duration"] -= allocated_time
                        remaining_time_needed -= allocated_time

                        if slot["duration"] <= 0:
                            slot_index += 1

                    if remaining_time_needed > 0:
                        full_plan.append(f"⚠️ Could not fully allocate time for topic '{topic}' in '{subject['name']}'.")

            day += 1

    # Handle normal subjects
    for subject in normal_subjects:
        difficulty = subject["difficulty"]
        total_hours = {"EASY": 1, "MEDIUM": 2, "HARD": 3}.get(difficulty, 2)
        study_time_per_topic = total_hours / len(subject["topics"])

        for topic in subject["topics"]:
            scheduled = False
            for _ in range(subject["days_left"]):
                remaining_time_needed = study_time_per_topic

                for slot in learning_slots:
                    if remaining_time_needed <= 0:
                        break

                    if slot["duration"] <= 0:
                        continue

                    allocated_time = min(slot["duration"], remaining_time_needed)

                    day_plan[day].append(
                        f"- {slot['time']}: {subject['name']} → {topic} ({allocated_time} hrs)"
                    )

                    if remaining_time_needed == study_time_per_topic:
                        subject_status[subject["name"]]["scheduled_topics"] += 1

                    slot["duration"] -= allocated_time
                    remaining_time_needed -= allocated_time

                if remaining_time_needed <= 0:
                    scheduled = True
                    break

            if scheduled:
                day += 1
            else:
                full_plan.append(
                    f"⚠️ Could not fit topic '{topic}' from '{subject['name']}' in available slots."
                )

    # Final formatting of the full plan
    formatted_plan = {
        "user_id": user_id,
        "learning_times": raw_learning_slots,
        "study_plan": []
    }

    # Add warnings and day plans to the study_plan list
    if total_available_hours < total_required_hours:
        formatted_plan["study_plan"].append(
            f"⚠️ Warning: Your available time ({total_available_hours} hrs) is less than the required time ({total_required_hours} hrs). Please adjust your learning plan."
        )

    formatted_plan["study_plan"].append("Day 1 Plan (URGENT! Exam Tomorrow) 📢")
    
    # Add day plan tasks
    for d in sorted(day_plan.keys()):
        formatted_plan["study_plan"].append(f"\n📅 Day {d} Plan:")
        formatted_plan["study_plan"].extend(day_plan[d])

    formatted_plan["study_plan"].append("\n📋 Subject Completion Summary:")
    for subject, stats in subject_status.items():
        total = stats["total_topics"]
        scheduled = stats["scheduled_topics"]
        percentage = (scheduled / total) * 100 if total > 0 else 0

        if percentage == 100:
            status = "✅ 100% completed"
        elif percentage >= 70:
            status = f"⚠️ {int(percentage)}% completed"
        else:
            status = f"❌ {int(percentage)}% completed - needs urgent focus!"

        formatted_plan["study_plan"].append(f"- {subject}: {status}")

    # Use Gemini API to summarize the study plan (optional)
    client = genai.Client(api_key="AIzaSyB9lYHay2GdDhSbSGVk776PMlO9khj5_wk")
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents="\n".join(formatted_plan["study_plan"]),
    )

    print("Gemini Response:", response.text)
    return formatted_plan
