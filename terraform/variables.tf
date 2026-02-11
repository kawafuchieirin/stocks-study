variable "aws_region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "プロジェクト名"
  type        = string
  default     = "stocks-study"
}

variable "environment" {
  description = "環境名"
  type        = string
  default     = "dev"
}

variable "jquants_api_key" {
  description = "J-Quants API v2 リフレッシュトークン"
  type        = string
  sensitive   = true
}

variable "schedule_expression" {
  description = "EventBridge Schedulerのスケジュール式"
  type        = string
  default     = "cron(0 18 ? * SUN *)" # 毎週日曜 03:00 JST = 18:00 UTC (土曜)
}

variable "glue_max_capacity" {
  description = "Glue Python Shell ジョブの最大DPU"
  type        = number
  default     = 0.0625
}
