# These get printed after apply so you don't have to hunt for connection details

output "ssh_command" {
  description = "How to SSH into the server"
  value       = "ssh -p ${var.ssh_port} root@localhost"
}

output "app_url" {
  description = "Where the deployed API will be reachable"
  value       = "http://localhost:${var.app_port}"
}

output "ansible_host" {
  description = "Inventory line for Step 9"
  value       = "todo-server ansible_host=localhost ansible_port=${var.ssh_port} ansible_user=root"
}
