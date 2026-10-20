# ============================================================
# BACKEND — KHÔNG dùng remote backend trong bootstrap
# ============================================================
#
# Bootstrap chạy TRƯỚC khi có state bucket, nên không thể
# trỏ vào chính bucket mà nó sắp tạo (chicken-and-egg problem).
#
# Vì vậy bootstrap dùng LOCAL state:
#   - File terraform.tfstate nằm cùng thư mục bootstrap/
#   - KHÔNG commit file này lên Git
#   - Sau khi bootstrap xong, các module KHÁC sẽ dùng remote
#     backend trỏ vào bucket vừa tạo.
#
# Ví dụ backend block cho các module khác (KHÔNG dùng ở đây):
#
# terraform {
#   backend "s3" {
#     bucket         = "studybot-tfstate-<account-id>"
#     key            = "env/dev/terraform.tfstate"
#     region         = "ap-southeast-1"
#     dynamodb_table = "studybot-tflock"
#     encrypt        = true
#   }
# }