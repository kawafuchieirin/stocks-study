# ====================
# CloudWatch ロググループ
# ====================

resource "aws_cloudwatch_log_group" "lambda_ingest" {
  name              = "/aws/lambda/${local.prefix}-ingest"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "step_functions" {
  name              = "/aws/states/${local.prefix}-pipeline"
  retention_in_days = 14
}
