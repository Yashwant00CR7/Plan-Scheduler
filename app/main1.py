from fastapi import FastAPI, HTTPException, Query
from app.db import get_db
from app.generate_plan_logic import generate_user_plan

app = FastAPI()

@app.get("/generate-user-plan")
def generate_plan(userId: str = Query(...)):
    collection = get_db()["subjects"]

    try:
        study_plan = generate_user_plan(collection, userId)
        if not study_plan:
            return {"message": "No upcoming exams found or no topics available."}
        return {"user_id": userId, "study_plan": study_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
