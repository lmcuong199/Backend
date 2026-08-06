# Global settings
terraform {
  required_version = ">= 1.6"

  required_providers {
    # Providers
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# Connect
provider "docker" {
  host = "npipe:////./pipe/dockerDesktopLinuxEngine"
}

# Resource type: "docker_image"
# Name: "server"
resource "docker_image" "server" {
  name = "todo-server:latest"

  build {
    context    = "${path.module}/server"
    dockerfile = "Dockerfile"
  }

  triggers = {
    dockerfile = filesha256("${path.module}/server/Dockerfile")
  }
}

resource "docker_volume" "server_storage" {
  name = "todo-server-docker-storage"
}

resource "docker_container" "server" {
  name       = "todo-server"
  hostname   = "todo-server"

  # This reference is what tells Terraformto build the image before the container
  image      = docker_image.server.image_id

  # without this, Docker can't run inside the server
  privileged = true
  restart    = "unless-stopped"

  ports {
    internal = 22
    external = var.ssh_port
  }

  ports {
    internal = 80
    external = var.app_port
  }

  # Without this, you get "invalid argument" mount errors 
  volumes {
    volume_name    = docker_volume.server_storage.name
    container_path = "/var/lib/docker"
  }

  # Without this, Ansible can't SSH in
  upload {
    content = file(pathexpand(var.ssh_public_key_path))
    file    = "/root/.ssh/authorized_keys"
  }
}
