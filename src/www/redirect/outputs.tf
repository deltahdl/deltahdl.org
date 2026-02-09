output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.redirect.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.redirect.domain_name
}

output "redirect_target" {
  value = local.redirect_target
}
