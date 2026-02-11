# ====================
# Glue Data Catalog データベース
# ====================

resource "aws_glue_catalog_database" "main" {
  name = "${local.prefix}-db"
}

# ====================
# Glue スクリプトの S3 アップロード
# ====================

resource "aws_s3_object" "transform_script" {
  bucket = aws_s3_bucket.glue_scripts.id
  key    = "scripts/transform.py"
  source = "${path.module}/../data-platform/glue/transform.py"
  etag   = filemd5("${path.module}/../data-platform/glue/transform.py")
}

resource "aws_s3_object" "enrich_script" {
  bucket = aws_s3_bucket.glue_scripts.id
  key    = "scripts/enrich.py"
  source = "${path.module}/../data-platform/glue/enrich.py"
  etag   = filemd5("${path.module}/../data-platform/glue/enrich.py")
}

# ====================
# Glue Python Shell ジョブ: Transform
# ====================

resource "aws_glue_job" "transform" {
  name     = "${local.prefix}-transform"
  role_arn = aws_iam_role.glue_job.arn

  command {
    name            = "pythonshell"
    script_location = "s3://${aws_s3_bucket.glue_scripts.id}/scripts/transform.py"
    python_version  = "3.9"
  }

  max_capacity = var.glue_max_capacity
  timeout      = 30 # 分

  default_arguments = {
    "--DATALAKE_BUCKET"           = aws_s3_bucket.datalake.id
    "--additional-python-modules" = "pyarrow==15.0.0"
    "--job-language"              = "python"
    "--TempDir"                   = "s3://${aws_s3_bucket.glue_scripts.id}/temp/"
    "--enable-metrics"            = "true"
  }

  depends_on = [aws_s3_object.transform_script]
}

# ====================
# Glue Python Shell ジョブ: Enrich
# ====================

resource "aws_glue_job" "enrich" {
  name     = "${local.prefix}-enrich"
  role_arn = aws_iam_role.glue_job.arn

  command {
    name            = "pythonshell"
    script_location = "s3://${aws_s3_bucket.glue_scripts.id}/scripts/enrich.py"
    python_version  = "3.9"
  }

  max_capacity = var.glue_max_capacity
  timeout      = 30 # 分

  default_arguments = {
    "--DATALAKE_BUCKET"           = aws_s3_bucket.datalake.id
    "--additional-python-modules" = "pyarrow==15.0.0,ta==0.11.0"
    "--job-language"              = "python"
    "--TempDir"                   = "s3://${aws_s3_bucket.glue_scripts.id}/temp/"
    "--enable-metrics"            = "true"
  }

  depends_on = [aws_s3_object.enrich_script]
}

# ====================
# Glue Crawler
# ====================

resource "aws_glue_crawler" "main" {
  name          = "${local.prefix}-crawler"
  role          = aws_iam_role.glue_crawler.arn
  database_name = aws_glue_catalog_database.main.name

  s3_target {
    path = "s3://${aws_s3_bucket.datalake.id}/processed/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.datalake.id}/analytics/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "LOG"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })
}
