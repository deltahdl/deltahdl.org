output "hosted_zone_id" {
  value = data.aws_route53_zone.main.zone_id
}

output "hosted_zone_name" {
  value = data.aws_route53_zone.main.name
}

output "name_servers" {
  value = data.aws_route53_zone.main.name_servers
}
