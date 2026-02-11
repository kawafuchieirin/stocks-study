# ====================
# EventBridge Scheduler
# ====================

resource "aws_scheduler_schedule" "pipeline" {
  name       = "${local.prefix}-weekly-pipeline"
  group_name = "default"

  schedule_expression          = var.schedule_expression
  schedule_expression_timezone = "Asia/Tokyo"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sfn_state_machine.pipeline.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({})
  }

  state = "ENABLED"
}
