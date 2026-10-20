terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Networking (default VPC, keep it simple) ---
data "aws_vpc" "default" {
  default = true
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# --- Security Group: locked to your home IP only ---
resource "aws_security_group" "homewatch" {
  name        = "homewatch-sg"
  description = "DNS resolver + dashboard, restricted to home IP"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.home_ip}/32"]
  }

  ingress {
    description = "DNS over TCP"
    from_port   = 53
    to_port     = 53
    protocol    = "tcp"
    cidr_blocks = ["${var.home_ip}/32"]
  }

  ingress {
    description = "DNS over UDP"
    from_port   = 53
    to_port     = 53
    protocol    = "udp"
    cidr_blocks = ["${var.home_ip}/32"]
  }

  ingress {
    description = "Dashboard HTTP and ACME"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "DNS over TLS (DoT for Mobile Private DNS)"
    from_port   = 853
    to_port     = 853
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Dashboard (HTTPS)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["${var.home_ip}/32"]
  }

  ingress {
    description = "Dashboard (Port 8000)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["${var.home_ip}/32"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "homewatch-sg" }
}

# --- SSH key pair (uses a key you already generated) ---
resource "aws_key_pair" "homewatch" {
  key_name   = "homewatch-key"
  public_key = file(var.ssh_public_key_path)
}

# --- EC2 instance ---
resource "aws_instance" "homewatch" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.homewatch.key_name
  vpc_security_group_ids = [aws_security_group.homewatch.id]
  user_data              = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = { Name = "homewatch-server" }
}

# --- Static public IP, so your router's DNS setting never breaks ---
resource "aws_eip" "homewatch" {
  instance = aws_instance.homewatch.id
  domain   = "vpc"
  tags     = { Name = "homewatch-eip" }
}
