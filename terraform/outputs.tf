output "kong_url" {
  value = "http://${aws_instance.kong.public_ip}:8000"
}
output "alb_dns" {
  value = aws_lb.app_lb.dns_name
}
