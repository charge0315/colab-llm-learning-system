"""
Google Drive integration service
Allows downloading audio files directly from Google Drive
"""
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from typing import Optional
import io
import os
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleDriveService:
    """Service to interact with Google Drive API"""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Drive service

        Args:
            credentials_path: Path to Google service account credentials JSON
        """
        self.credentials_path = credentials_path or settings.google_credentials_path
        self.service = None

        if self.credentials_path and os.path.exists(self.credentials_path):
            try:
                self._initialize_service()
            except Exception as e:
                logger.error(f"Failed to initialize Google Drive service: {e}")
        else:
            logger.warning("Google Drive credentials not found. Drive access will not be available.")

    def _initialize_service(self):
        """Initialize Google Drive API service"""
        try:
            # Use service account credentials
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )

            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Google Drive service initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
            raise

    def download_file(self, file_id: str, destination_path: str) -> bool:
        """
        Download a file from Google Drive

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file

        Returns:
            True if download successful, False otherwise
        """
        if not self.service:
            logger.error("Google Drive service not initialized")
            return False

        try:
            logger.info(f"Downloading file from Google Drive: {file_id}")

            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            logger.info(f"File name: {file_metadata.get('name')}, Size: {file_metadata.get('size')} bytes")

            # Download file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"File downloaded successfully to: {destination_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file from Google Drive: {e}")
            return False

    def get_file_metadata(self, file_id: str) -> Optional[dict]:
        """
        Get metadata for a Google Drive file

        Args:
            file_id: Google Drive file ID

        Returns:
            Dictionary with file metadata, or None if error
        """
        if not self.service:
            logger.error("Google Drive service not initialized")
            return None

        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime'
            ).execute()

            return file_metadata

        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return None

    @staticmethod
    def extract_file_id_from_url(url: str) -> Optional[str]:
        """
        Extract file ID from Google Drive URL

        Supports formats:
        - https://drive.google.com/file/d/FILE_ID/view
        - https://drive.google.com/open?id=FILE_ID
        - Direct file ID

        Args:
            url: Google Drive URL or file ID

        Returns:
            File ID if extracted, None otherwise
        """
        if not url:
            return None

        # If it's already a file ID (no slashes or special chars)
        if '/' not in url and '?' not in url and len(url) < 50:
            return url

        # Extract from /file/d/FILE_ID/ format
        if '/file/d/' in url:
            try:
                file_id = url.split('/file/d/')[1].split('/')[0]
                return file_id
            except IndexError:
                pass

        # Extract from ?id=FILE_ID format
        if 'id=' in url:
            try:
                file_id = url.split('id=')[1].split('&')[0]
                return file_id
            except IndexError:
                pass

        logger.warning(f"Could not extract file ID from URL: {url}")
        return None

    def is_audio_file(self, file_id: str) -> bool:
        """
        Check if a Google Drive file is an audio file

        Args:
            file_id: Google Drive file ID

        Returns:
            True if file is audio, False otherwise
        """
        metadata = self.get_file_metadata(file_id)
        if not metadata:
            return False

        mime_type = metadata.get('mimeType', '')
        name = metadata.get('name', '').lower()

        # Check MIME type
        if mime_type.startswith('audio/'):
            return True

        # Check file extension
        audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma']
        return any(name.endswith(ext) for ext in audio_extensions)
