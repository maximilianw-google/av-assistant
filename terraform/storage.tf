resource "google_storage_bucket" "bucket" {
 name          = var.bucket_name
 location      = "US"
 storage_class = "STANDARD"
 force_destroy = true
 lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }

 uniform_bucket_level_access = true
}