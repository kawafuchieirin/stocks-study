# ====================
# Lambda Ingest 関数
# ====================

data "archive_file" "lambda_ingest" {
  type        = "zip"
  source_dir  = "${path.module}/../data-platform/lambda/ingest"
  output_path = "${path.module}/.build/lambda_ingest.zip"
  excludes    = ["__pycache__", "*.pyc"]
}

resource "aws_lambda_function" "ingest" {
  function_name    = "${local.prefix}-ingest"
  role             = aws_iam_role.lambda_ingest.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  architectures    = ["arm64"]
  memory_size      = 256
  timeout          = 300
  filename         = data.archive_file.lambda_ingest.output_path
  source_code_hash = data.archive_file.lambda_ingest.output_base64sha256

  layers = [aws_lambda_layer_version.ingest_deps.arn]

  environment {
    variables = {
      DATALAKE_BUCKET = aws_s3_bucket.datalake.id
      JQUANTS_API_KEY = var.jquants_api_key
    }
  }

  logging_config {
    log_group  = aws_cloudwatch_log_group.lambda_ingest.name
    log_format = "Text"
  }

  depends_on = [
    aws_iam_role_policy.lambda_ingest,
    aws_cloudwatch_log_group.lambda_ingest,
  ]
}

# ====================
# Lambda Layer（依存ライブラリ）
# ====================

resource "aws_lambda_layer_version" "ingest_deps" {
  layer_name               = "${local.prefix}-ingest-deps"
  filename                 = "${path.module}/.build/lambda_layer.zip"
  compatible_runtimes      = ["python3.12"]
  compatible_architectures = ["arm64"]
  description              = "jquants-api-client, tenacity, pandas の依存ライブラリ"

  lifecycle {
    # レイヤーZIPはMakefileのpackage-lambdaで事前ビルド
    ignore_changes = [filename]
  }
}
