import os
import boto3
from common.response import success, error
from common.auth import get_user_id

dynamodb = boto3.resource("dynamodb")
TABLE_JOBS = os.environ.get("TABLE_JOBS", "")

def lambda_handler(event, context):
    try:
        # 1. Lấy user_id từ JWT Authorizer
        user_id = get_user_id(event)
        if not user_id:
            return error("Unauthorized: Missing user identity", 401)

        # 2. Lấy job_id từ Path Parameter (/jobs/{job_id})
        path_params = event.get("pathParameters") or {}
        job_id = path_params.get("job_id")

        if not job_id:
            return error("Missing job_id path parameter", 400)

        if not TABLE_JOBS:
            return error("TABLE_JOBS environment variable not configured", 500)

        # 3. Đọc dữ liệu Job từ DynamoDB
        table = dynamodb.Table(TABLE_JOBS)
        res = table.get_item(Key={"job_id": job_id})
        item = res.get("Item")

        if not item:
            return error(f"Job '{job_id}' not found", 404)

        # 4. Kiểm tra quyền sở hữu (Job thuộc về đúng user)
        if item.get("user_id") and item.get("user_id") != user_id:
            return error("Forbidden: You do not own this job", 403)

        # 5. Trả về thông tin Job
        return success({
            "job_id": item.get("job_id"),
            "job_type": item.get("job_type"),
            "status": item.get("status"),
            "user_id": item.get("user_id"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "error_message": item.get("error_message"),
            "result": item.get("result"),
        })

    except Exception as e:
        print(f"Error handling job request: {str(e)}")
        return error("Internal server error", 500, str(e))