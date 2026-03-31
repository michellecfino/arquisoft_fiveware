resource "aws_instance" "reportes" {
  count         = var.instance_count
  ami           = "ami-0c55b159cbfafe1f0" # Ubuntu
  instance_type = var.instance_type

  key_name = var.key_name

  vpc_security_group_ids = [aws_security_group.sg.id]

  user_data = file("user_data.sh")

  tags = {
    Name = "reportes-${count.index}"
  }
}