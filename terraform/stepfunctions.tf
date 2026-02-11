# ====================
# Step Functions ステートマシン
# ====================

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${local.prefix}-pipeline"
  role_arn = aws_iam_role.step_functions.arn

  definition = templatefile("${path.module}/../data-platform/stepfunctions/pipeline.asl.json", {
    lambda_ingest_arn       = aws_lambda_function.ingest.arn
    glue_transform_job_name = aws_glue_job.transform.name
    glue_enrich_job_name    = aws_glue_job.enrich.name
    glue_crawler_name       = aws_glue_crawler.main.name
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.step_functions.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  depends_on = [aws_iam_role_policy.step_functions]
}
