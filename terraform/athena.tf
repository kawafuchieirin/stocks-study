# ====================
# Athena ワークグループ
# ====================

resource "aws_athena_workgroup" "main" {
  name = "${local.prefix}-workgroup"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.datalake.id}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }

    bytes_scanned_cutoff_per_query = 1073741824 # 1GB
  }
}
