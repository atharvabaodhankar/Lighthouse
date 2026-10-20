output "server_public_ip" {
  description = "Set this as your router's DNS server"
  value       = aws_eip.homewatch.public_ip
}

output "ssh_command" {
  value = "ssh ubuntu@${aws_eip.homewatch.public_ip}"
}

output "dashboard_url" {
  description = "Lighthouse Dashboard Web Interface (restricted to your home IP)"
  value       = "http://${aws_eip.homewatch.public_ip}"
}
