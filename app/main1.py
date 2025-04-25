from fastapi import FastAPI, HTTPException, Query
from app.db import get_db
from app.generate_plan_logic import generate_user_plan

app = FastAPI()

@app.get("/generate-user-plan")
def generate_plan(userId: str = Query(...)):
    db = get_db()
    users_collection = db["users"]
    subjects_collection = db["subjects"]

    try:
        result = generate_user_plan(users_collection, subjects_collection, userId)
        if not result["study_plan"]:
            return {"message": "No upcoming exams found or no topics available."}
        return {
            "user_id": userId,
            "learning_times": result["learning_times"],
            "study_plan": result["study_plan"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
