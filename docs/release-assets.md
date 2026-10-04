# Archived asset release

Large images, generated audit reports, and the retail prototype model binaries were removed from the current source tree. They are not loaded by the default API or frontend. The manual workflow [Publish archived binary assets](../.github/workflows/release-legacy-assets.yml) extracts them from the pre-cleanup repository snapshot, creates a compressed GitHub Release bundle, and publishes a SHA-256 manifest.

After merging, run the workflow on `main` with the default tag `legacy-assets-v1.0.0` and verify the release download and checksum. The original blobs remain in Git history for traceability; a shallow checkout of the cleaned tree no longer downloads them. The empty audit PDF is excluded.
