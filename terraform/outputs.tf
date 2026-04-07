output "kong_url" {
  value = "http://${aws_instance.kong.public_ip}:8000"
}