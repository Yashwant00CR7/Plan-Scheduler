

# **User Learning Plan Generator**

## **Description**
This project is a learning plan generator designed to help users efficiently allocate their study time based on their daily routine and upcoming exam schedules. The system fetches user details and their learning slots from a MongoDB database, calculates the total time available for studying, and then assigns topics for each subject based on the available study hours and the time needed for each topic.

The system also helps identify if there is not enough available time to cover all the required study material, warning users if their study time is insufficient.

## **Features**
- Fetches the user's daily learning slots from the database.
- Automatically calculates available study hours and compares them to the required study time.
- Generates a study plan that prioritizes urgent subjects (subjects with exams the next day).
- Schedules topics based on their difficulty and the time required.
- Warns users if there is insufficient study time or if any topics cannot be covered.
- Outputs a complete study plan with day-wise breakdowns and completion percentages for each subject.

## **Technologies Used**
- **Python 3.x**
- **MongoDB** (for storing user data and subject information)
- **Datetime** (for calculating time and deadlines)
- **BSON** (for handling MongoDB ObjectId)

## **Functionality**

### `time_range_to_hours(time_range: str) -> float`
This helper function converts a time range (e.g., "08:00 - 10:00") into the total number of hours available for study.

### `generate_user_plan(users_collection: Collection, subjects_collection: Collection, user_id: str) -> dict`
Main function that generates a personalized study plan for a user. It:
- Fetches the user and subject data from MongoDB collections.
- Sorts subjects based on exam dates and allocates time for each topic.
- Creates an actionable plan with clear breakdowns.
- Warns if the available time is less than the required time.

### **Study Plan Example**
- **Urgent subjects:** Exam tomorrow. Allocate study time immediately.
- **Normal subjects:** Allocate study time based on exam date.
- **Completion summary:** Tracks how much of the study material has been completed.

---

## **Usage**

### **1. Set up MongoDB**
Ensure that you have a MongoDB database set up with collections for users and subjects. The collections should follow the structure:

- **Users Collection**:
    - `_id`: MongoDB ObjectId
    - `dailyRoutine`: List of daily routines, each containing a time range (e.g., `{"action": "learning", "time": "08:00 - 10:00"}`)
  
- **Subjects Collection**:
    - `userId`: MongoDB ObjectId (references the user)
    - `subjectName`: Name of the subject
    - `examDate`: Date of the exam
    - `examDifficulty`: Difficulty level (e.g., `EASY`, `MEDIUM`, `HARD`)
    - `topics`: List of topics to be studied

### **2. Running the Script**
You can run the Python script after setting up the MongoDB collections and passing the necessary parameters:

```python
from datetime import datetime
from pymongo import MongoClient
from project import generate_user_plan  # Import the function from your project

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['learning_db']
users_collection = db['users']
subjects_collection = db['subjects']

user_id = 'user_mongo_object_id_here'  # Replace with the actual user ID
plan = generate_user_plan(users_collection, subjects_collection, user_id)

# Print the study plan
print(plan)
```

### **3. Example Output**
```json
{
    "learning_times": [
        "08:00 - 10:00",
        "14:00 - 16:00"
    ],
    "study_plan": [
        "Day 1 Plan (URGENT! Exam Tomorrow) 📢",
        "- 08:00 - 10:00: Subject A → Topic 1 (2.0 hrs)",
        "- 14:00 - 16:00: Subject A → Topic 2 (1.0 hrs)",
        "⚠️ Warning: Your available time is less than required study time. Please adjust your learning plan."
    ]
}
```

### **4. Adjustments & Warnings**
The system will output warnings if:
- There is not enough available time to study all topics.
- A subject has no topics listed.
- A topic could not be scheduled within the available time slots.

---

## **Future Enhancements**
- Implement a feature to allow users to specify more detailed preferences (e.g., study hours per day, preferred subjects).
- Integrate the Scoring System with LLM and other Models for a Precised Output
- Introduce additional exam preparation strategies (e.g., practice tests, revision).
- Integrate with external calendars to sync study schedules with other events.

## **Contributing**
If you'd like to contribute to this project, feel free to fork the repository and submit pull requests. Contributions such as bug fixes, new features, or improvements are always welcome!

---

## **License**
This project is licensed under the MIT License.

---

Let me know if you need any adjustments to this README or if you'd like additional details included.
