from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/media", tags=["Media & Downloads"])

ARTIFACTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../..", "artifacts"))

@router.get("/reports/{filename}")
async def download_report(filename: str):
    """Download a generated PDF report."""
    file_path = os.path.join(ARTIFACTS_DIR, "reports", filename)
    if not os.path.exists(file_path):
        # Fallback to root artifacts if not found in reports subdir (legacy support)
        file_path = os.path.join(ARTIFACTS_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

@router.get("/videos/{filename}")
async def download_video(filename: str):
    """Download a generated simulation video."""
    file_path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")
    # Determine media type based on extension
    media_type = "video/mp4"
    if filename.endswith(".gif"):
        media_type = "image/gif"
    return FileResponse(file_path, media_type=media_type, filename=filename)

@router.get("/maps/{filename}")
async def download_map(filename: str):
    """Download a generated map image."""
    file_path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Map not found")
    return FileResponse(file_path, media_type="image/png", filename=filename)
