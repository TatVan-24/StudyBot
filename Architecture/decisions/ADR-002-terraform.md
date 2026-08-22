# ADR-002: Terraform for AWS Infrastructure

- Status: Accepted
- Date: 2026-08-21

## Context

The confirmed inventory contains CloudFront/S3 frontend delivery, Cognito/API Gateway, six Lambda functions, seven DynamoDB tables, two SQS queues plus DLQs, document storage, IAM boundaries and observability resources. The project also aims to demonstrate an additional IaC/DevOps skill.

## Decision

Use Terraform to define and deploy StudyBot AWS infrastructure.

Required practices:

- Remote encrypted state with locking for deployed environments.
- Provider constraints and committed `.terraform.lock.hcl`.
- No state files or secrets in Git.
- Plan review before apply.
- Logical modules and explicit environment composition.
- Least-privilege policies generated from known resource ARNs.
- Repeatable teardown for temporary environments while preserving bootstrap/state.

## Consequences

Positive:

- Clear dependency graph and readable change plan.
- Reusable modules and multi-environment support.
- Broad AWS and potential non-AWS provider coverage.
- Strong portfolio value for IaC/DevOps work.

Negative:

- Terraform state becomes an additional protected operational asset.
- Lambda packaging/deployment requires explicit integration rather than SAM-specific shortcuts.
- Provider upgrades and lock files require maintenance.

## Alternatives considered

- AWS SAM: concise for Lambda/API and convenient local serverless testing, but the wider inventory still requires substantial CloudFormation syntax.
- AWS CDK Python: strong AWS integration and reusable code without separate state, but Terraform was selected to expand IaC skill coverage and retain provider flexibility.
