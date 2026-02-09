data "aws_route53_zone" "main" {
  zone_id = var.hosted_zone_id
}
