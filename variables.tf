variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1" # Mumbai — lowest latency from Pune
}

variable "instance_type" {
  description = "EC2 instance size (t2.micro / t3.micro are free-tier eligible for 12 months)"
  type        = string
  default     = "t3.micro"
}

variable "home_ip" {
  description = "Your home's public IPv4 address (check whatsmyip.com). Everything is locked to just this IP."
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to your local SSH public key, e.g. ~/.ssh/id_ed25519.pub"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "telegram_bot_token" {
  description = "Telegram bot token for daily report alerts"
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_chat_id" {
  description = "Telegram chat ID to send alerts to"
  type        = string
  default     = ""
  sensitive   = true
}
