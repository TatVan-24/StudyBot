import json
import os

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "placeholder",
            "function": "studybot-flashcard",
            "table_jobs": os.environ.get("TABLE_JOBS", "N/A"),
        }),
    }