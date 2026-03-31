variable "instance_count" {
  description = "Número de instancias EC2"
  default     = 4
}

variable "instance_type" {
  default = "t2.micro"
}

variable "key_name" {
  description = "Clave SSH"
}