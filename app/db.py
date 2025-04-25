from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb+srv://bharath:bharathsivanesh262005@cluste.5phjp.mongodb.net/study_planner?retryWrites=true&w=majority&appName=Cluste")
    return client["study_planner"]
