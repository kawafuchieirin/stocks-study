terraform {
  backend "s3" {
    bucket = "terraform-state-412420079063-ap-northeast-1"
    key    = "stocks-study/terraform.tfstate"
    region = "ap-northeast-1"
  }
}
