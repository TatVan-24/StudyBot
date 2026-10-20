terraform {
  backend "s3" {
    bucket         = "studybot-tfstate-001"
    key            = "dev/terraform.tfstate"
    region         = "ap-southeast-2"
    dynamodb_table = "studybot-tflock"
    encrypt        = true
  }
}
