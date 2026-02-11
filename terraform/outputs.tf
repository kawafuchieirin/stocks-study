output "datalake_bucket_name" {
  description = "データレイク S3 バケット名"
  value       = aws_s3_bucket.datalake.id
}

output "glue_scripts_bucket_name" {
  description = "Glue スクリプト S3 バケット名"
  value       = aws_s3_bucket.glue_scripts.id
}

output "lambda_ingest_function_name" {
  description = "Lambda Ingest 関数名"
  value       = aws_lambda_function.ingest.function_name
}

output "step_functions_arn" {
  description = "Step Functions ステートマシン ARN"
  value       = aws_sfn_state_machine.pipeline.arn
}

output "glue_database_name" {
  description = "Glue Data Catalog データベース名"
  value       = aws_glue_catalog_database.main.name
}

output "athena_workgroup_name" {
  description = "Athena ワークグループ名"
  value       = aws_athena_workgroup.main.name
}

output "glue_transform_job_name" {
  description = "Glue Transform ジョブ名"
  value       = aws_glue_job.transform.name
}

output "glue_enrich_job_name" {
  description = "Glue Enrich ジョブ名"
  value       = aws_glue_job.enrich.name
}

output "glue_crawler_name" {
  description = "Glue Crawler 名"
  value       = aws_glue_crawler.main.name
}
