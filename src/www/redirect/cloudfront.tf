module "redirect_bucket" {
  source = "../../../lib/opentofu/s3_bucket"

  bucket_name         = "deltahdl-redirect-origin"
  force_destroy       = true
  versioning_enabled  = false
  central_logs_bucket = local.name_for_central_logs
  log_prefix          = "s3-access/redirect-origin/"
}

resource "aws_cloudfront_function" "redirect" {
  name    = "${local.resource_prefix}Function"
  runtime = "cloudfront-js-2.0"
  code    = file("${path.module}/cloudfront_function.js")
}

resource "aws_cloudfront_distribution" "redirect" {
  enabled         = true
  is_ipv6_enabled = false
  aliases         = [local.www_fqdn, local.apex_fqdn]

  logging_config {
    include_cookies = false
    bucket          = "${local.name_for_central_logs}.s3.amazonaws.com"
    prefix          = "cloudfront-logs/redirect/"
  }

  origin {
    domain_name              = module.redirect_bucket.bucket_regional_domain_name
    origin_id                = "s3-redirect"
    origin_access_control_id = aws_cloudfront_origin_access_control.redirect.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-redirect"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = false

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.redirect.arn
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.redirect.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  depends_on = [aws_acm_certificate_validation.redirect]
}

resource "aws_cloudfront_origin_access_control" "redirect" {
  name                              = "${local.apex_fqdn}-redirect-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
