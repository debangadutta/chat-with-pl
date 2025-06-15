import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class Config:
    """
    Unified configuration management for both local development and Streamlit Cloud deployment.

    This class automatically detects the environment and loads configuration accordingly:
    - Streamlit Cloud: Uses st.secrets
    - Local Development: Uses .env file
    """

    def __init__(self):
        self.environment = self._detect_environment()
        self.openai_api_key = self._get_openai_api_key()

        # Log successful configuration (without exposing sensitive data)
        logger.info(f"Configuration loaded for environment: {self.environment}")

    def _detect_environment(self) -> str:
        """
        Detect if we're running on Streamlit Cloud or locally.

        Returns:
            str: Either 'streamlit_cloud' or 'local'
        """
        try:
            # Try importing streamlit and accessing secrets
            import streamlit as st

            # If we can access st.secrets, we're likely on Streamlit Cloud
            _ = st.secrets
            return "streamlit_cloud"
        except (ImportError, AttributeError, FileNotFoundError):
            # Either streamlit not available or secrets not configured
            return "local"

    def _get_openai_api_key(self) -> str:
        """
        Get OpenAI API key from appropriate source based on environment.

        Returns:
            str: The OpenAI API key

        Raises:
            ValueError: If API key is not found in any source
        """
        api_key = None

        if self.environment == "streamlit_cloud":
            api_key = self._get_from_streamlit_secrets()

        # Always try .env as fallback (useful for local testing of deployed apps)
        if not api_key:
            api_key = self._get_from_env_file()

        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in either:\n"
                "- Streamlit secrets (for deployment)\n"
                "- .env file (for local development)\n"
                "- Environment variables"
            )

        return api_key.strip()

    def _get_from_streamlit_secrets(self) -> Optional[str]:
        """
        Try to get API key from Streamlit secrets.

        Returns:
            Optional[str]: API key if found, None otherwise
        """
        try:
            import streamlit as st

            return st.secrets.get("OPENAI_API_KEY")
        except Exception as e:
            logger.debug(f"Could not load from Streamlit secrets: {e}")
            return None

    def _get_from_env_file(self) -> Optional[str]:
        """
        Try to get API key from .env file or environment variables.

        Returns:
            Optional[str]: API key if found, None otherwise
        """
        try:
            # Try to load .env file if it exists
            try:
                from dotenv import load_dotenv

                load_dotenv()
                logger.debug("Loaded .env file")
            except ImportError:
                logger.debug("python-dotenv not installed, trying environment variables only")

            return os.getenv("OPENAI_API_KEY")
        except Exception as e:
            logger.debug(f"Could not load from environment: {e}")
            return None

    def __repr__(self) -> str:
        """
        String representation of config (without exposing sensitive data).
        """
        return f"Config(environment='{self.environment}', api_key_configured={bool(self.openai_api_key)})"


# Global config instance - initialized once when module is imported
config = Config()
