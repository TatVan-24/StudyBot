resource"aws_s3_bucket" "frontend" {
    bucket = var.frontend_bucket_name
    lifecycle {
        prevent_destroy = true
    }
}

resource"aws_s3_bucket" "document" {
    bucket = var.document_bucket_name
    lifecycle {
        prevent_destroy = true
    }
}

resource"aws_s3_bucket_versioning" "frontend" {
    bucket = aws_s3_bucket.frontend.id
    versioning_configuration {
        status = var.enable_versioning ? "Enabled" : "Suspended"
    }
}

resource"aws_s3_bucket_versioning" "document" {
    bucket = aws_s3_bucket.document.id
    versioning_configuration {
        status = var.enable_versioning ? "Enabled" : "Suspended"
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
    bucket = aws_s3_bucket.frontend.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    bucket_key_enabled = true
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "document" {
    bucket = aws_s3_bucket.document.id
    rule {
        apply_server_side_encryption_by_default {
            sse_algorithm = "AES256"
        }
    bucket_key_enabled = true
    }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
    bucket = aws_s3_bucket.frontend.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "document" {
    bucket = aws_s3_bucket.document.id
    block_public_acls       = true
    block_public_policy     = true
    ignore_public_acls      = true
    restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "document" {
    bucket  =	aws_s3_bucket.document.id
    cors_rule {
        allowed_methods	= ["GET", "PUT", "POST", "HEAD"]
        allowed_origins	= var.cors_allowed_origins
        allowed_headers	= ["*"]
        expose_headers	= ["ETag"]
        max_age_seconds	= 3000
    }
} 

# resource "aws_s3_bucket_notification" "document" {
#   bucket = aws_s3_bucket.document.id
# 
#   lambda_function {
#     lambda_function_arn = "TODO: ARN of lambda function (M6)"
#     events              = ["s3:ObjectCreated:*"]
#   }
# }