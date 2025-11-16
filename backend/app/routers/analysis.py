"""
Music analysis API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import shutil
import logging
from datetime import datetime

from app.models import MusicAnalysis
from app.services import AudioAnalyzer, GoogleDriveService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize services
audio_analyzer = AudioAnalyzer(openai_api_key=settings.openai_api_key)
gdrive_service = GoogleDriveService()


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    extract_lyrics: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    Upload an audio file and perform comprehensive analysis

    Args:
        file: Audio file to analyze
        extract_lyrics: Whether to extract lyrics using Whisper (default: True)

    Returns:
        Analysis results and MongoDB document ID
    """
    logger.info(f"Received upload request: {file.filename}")

    # Validate file type
    allowed_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma']
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Save uploaded file temporarily
    temp_path = os.path.join(settings.upload_dir, f"{datetime.utcnow().timestamp()}_{file.filename}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"File saved to: {temp_path}")

        # Perform analysis
        analysis = await audio_analyzer.analyze_audio(
            audio_path=temp_path,
            source="upload",
            extract_lyrics=extract_lyrics
        )

        # Save to MongoDB
        await analysis.insert()

        logger.info(f"Analysis saved to database with ID: {analysis.id}")

        # Schedule cleanup in background
        if background_tasks:
            background_tasks.add_task(cleanup_file, temp_path)

        return {
            "status": "success",
            "message": "Audio analysis completed successfully",
            "analysis_id": str(analysis.id),
            "filename": file.filename,
            "duration": analysis.duration,
            "processing_time": analysis.processing_time_total
        }

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        # Cleanup on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/google-drive")
async def analyze_from_google_drive(
    file_url: str = Form(...),
    extract_lyrics: bool = Form(True),
    background_tasks: BackgroundTasks = None
):
    """
    Analyze an audio file from Google Drive

    Args:
        file_url: Google Drive file URL or file ID
        extract_lyrics: Whether to extract lyrics using Whisper (default: True)

    Returns:
        Analysis results and MongoDB document ID
    """
    logger.info(f"Received Google Drive analysis request: {file_url}")

    # Extract file ID
    file_id = GoogleDriveService.extract_file_id_from_url(file_url)
    if not file_id:
        raise HTTPException(status_code=400, detail="Invalid Google Drive URL or file ID")

    # Check if file is audio
    if not gdrive_service.is_audio_file(file_id):
        raise HTTPException(status_code=400, detail="File is not an audio file")

    # Get file metadata
    metadata = gdrive_service.get_file_metadata(file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="File not found or inaccessible")

    filename = metadata.get('name', f"{file_id}.audio")

    # Create upload directory
    os.makedirs(settings.upload_dir, exist_ok=True)

    # Download file
    temp_path = os.path.join(settings.upload_dir, f"{datetime.utcnow().timestamp()}_{filename}")

    try:
        success = gdrive_service.download_file(file_id, temp_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to download file from Google Drive")

        # Perform analysis
        analysis = await audio_analyzer.analyze_audio(
            audio_path=temp_path,
            source="google_drive",
            source_path=file_url,
            extract_lyrics=extract_lyrics
        )

        # Save to MongoDB
        await analysis.insert()

        logger.info(f"Analysis saved to database with ID: {analysis.id}")

        # Schedule cleanup in background
        if background_tasks:
            background_tasks.add_task(cleanup_file, temp_path)

        return {
            "status": "success",
            "message": "Audio analysis from Google Drive completed successfully",
            "analysis_id": str(analysis.id),
            "filename": filename,
            "duration": analysis.duration,
            "processing_time": analysis.processing_time_total
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Google Drive analysis: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str):
    """
    Get analysis results by ID

    Args:
        analysis_id: MongoDB document ID

    Returns:
        Complete analysis results
    """
    try:
        analysis = await MusicAnalysis.get(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_analyses(
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at"
):
    """
    List all analyses with pagination

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        sort_by: Field to sort by (default: created_at)

    Returns:
        List of analyses
    """
    try:
        # Query with pagination and sorting
        query = MusicAnalysis.find_all()

        # Sort descending by default
        if sort_by == "created_at":
            query = query.sort(-MusicAnalysis.created_at)
        elif sort_by == "filename":
            query = query.sort(MusicAnalysis.filename)

        # Pagination
        analyses = await query.skip(skip).limit(limit).to_list()

        # Count total
        total = await MusicAnalysis.find_all().count()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "results": analyses
        }

    except Exception as e:
        logger.error(f"Error listing analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """
    Delete an analysis by ID

    Args:
        analysis_id: MongoDB document ID

    Returns:
        Success message
    """
    try:
        analysis = await MusicAnalysis.get(analysis_id)

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        await analysis.delete()

        return {
            "status": "success",
            "message": f"Analysis {analysis_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def cleanup_file(file_path: str):
    """Background task to cleanup temporary files"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {e}")
