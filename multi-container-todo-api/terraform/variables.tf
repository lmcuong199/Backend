variable "ssh_public_key_path" {
  description = "Path to your SSH public key"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "ssh_port" {
  description = "Host port forwarded to the server's SSH"
  type        = number
  default     = 2222
}

variable "app_port" {
  description = "Host port forwarded to the deployed API"
  type        = number
  default     = 8080
}
