# AI Empire — Google Cloud Infrastructure (100% Open Source)
# ===========================================================
# Deploys to: mauricepfeiferai@gmail.com / ai-empire-486415
#
# Resources:
#   - Cloud Run (serverless container for API)
#   - Compute Engine (GPU VM for Ollama + heavy AI)
#   - Cloud Storage (data + models)
#   - Artifact Registry (container images)
#   - Cloud Build (CI/CD)
#
# Usage:
#   cd cloud/terraform
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# ─── Variables ────────────────────────────────────────────────

variable "project_id" {
  default     = "ai-empire-486415"
  description = "Google Cloud Project ID"
}

variable "region" {
  default     = "europe-west4"
  description = "Google Cloud Region (Netherlands, close to DE)"
}

variable "zone" {
  default     = "europe-west4-a"
  description = "Google Cloud Zone"
}

# ─── Provider ─────────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Enable APIs ──────────────────────────────────────────────

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "compute.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# ─── Artifact Registry (Container Images) ────────────────────

resource "google_artifact_registry_repository" "empire" {
  location      = var.region
  repository_id = "empire"
  format        = "DOCKER"
  description   = "AI Empire container images"

  depends_on = [google_project_service.apis]
}

# ─── Cloud Storage (Data + Models) ───────────────────────────

resource "google_storage_bucket" "empire_data" {
  name     = "${var.project_id}-empire-data"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

# ─── Cloud Run (API Server — Serverless) ─────────────────────

resource "google_cloud_run_v2_service" "empire_api" {
  name     = "empire-api"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/empire/api:latest"

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "OLLAMA_BASE_URL"
        value = "http://localhost:11434"
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  depends_on = [google_project_service.apis]
}

# Public access for API
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.empire_api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─── Compute Engine (GPU VM for Ollama) ──────────────────────
# Optional: Only needed if you want full Ollama in the cloud
# Uncomment to deploy a GPU VM

# resource "google_compute_instance" "empire_gpu" {
#   name         = "empire-ai-server"
#   machine_type = "g2-standard-4"  # 4 vCPU, 16GB RAM, L4 GPU
#   zone         = var.zone
#
#   boot_disk {
#     initialize_params {
#       image = "projects/ml-images/global/images/c0-deeplearning-common-gpu-v20240128-debian-11-py310"
#       size  = 100
#     }
#   }
#
#   guest_accelerator {
#     type  = "nvidia-l4"
#     count = 1
#   }
#
#   scheduling {
#     on_host_maintenance = "TERMINATE"
#     preemptible         = true  # 60-91% cheaper!
#   }
#
#   network_interface {
#     network = "default"
#     access_config {}
#   }
#
#   metadata_startup_script = <<-EOF
#     #!/bin/bash
#     curl -fsSL https://ollama.com/install.sh | sh
#     ollama serve &
#     sleep 5
#     ollama pull qwen2.5-coder:7b
#     ollama pull qwen2.5-coder:14b
#   EOF
#
#   tags = ["empire-ai", "http-server"]
# }

# ─── Outputs ──────────────────────────────────────────────────

output "api_url" {
  value       = google_cloud_run_v2_service.empire_api.uri
  description = "Cloud Run API URL"
}

output "registry" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/empire"
  description = "Artifact Registry URL"
}

output "bucket" {
  value       = google_storage_bucket.empire_data.name
  description = "Data bucket name"
}
