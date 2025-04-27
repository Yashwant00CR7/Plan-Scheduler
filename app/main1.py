# Import necessary modules from FastAPI
from fastapi import FastAPI, HTTPException, Query
# Import database functions and the function to generate the study plan
from app.db import get_db
from app.generate_plan_logic import generate_user_plan

# Create a FastAPI instance to define the API
app = FastAPI()

# Define an endpoint that generates a study plan for a user
@app.get("/generate-user-plan")
def generate_plan(userId: str = Query(...)):  # Takes userId as a query parameter
    # Connect to the database
    db = get_db()
    # Get the collections for users and subjects from the database
    users_collection = db["users"]
    subjects_collection = db["subjects"]

    try:
        # Call the function to generate the study plan
        result = generate_user_plan(users_collection, subjects_collection, userId)
        
        # If no study plan is generated, return a message
        if not result["study_plan"]:
            return {"message": "No upcoming exams found or no topics available."}
        
        # Return the generated study plan along with learning times
        return {
            "user_id": userId,  # The user ID for the plan
            "learning_times": result["learning_times"],  # Times when the user will study
            "study_plan": result["study_plan"]  # The actual study plan
        }
    
    except Exception as e:
        # If there’s any error, raise an HTTP exception with the error message
        raise HTTPException(status_code=500, detail=str(e))
