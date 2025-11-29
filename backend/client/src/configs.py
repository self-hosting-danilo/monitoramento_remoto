from dataclasses import dataclass
from pathlib import Path
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """
    Email configuration settings for SMTP server.
    Attributes:
        host (str): SMTP server hostname. Defaults to 'smtp.gmail.com'.
        port (int): SMTP server port. Defaults to 587.
        username (str): Username for SMTP authentication.
        password (str): Password for SMTP authentication.
        use_tls (bool): Whether to use TLS for the connection. Defaults to True.
        from_email (str): Sender email address. Defaults to username if not set.
        to_emails (List[str]): List of recipient email addresses. Defaults to ['danilocrautomacao@gmail.com'] if not set.
    Methods:
        __post_init__(): Initializes default values for 'to_emails' and 'from_email' if they are not provided.
    """

    host: str = 'smtp.gmail.com'
    port: int = 587
    username: str = ''
    password: str = ''
    use_tls: bool = True
    from_email: str = ''
    to_emails: list[str] = None #type:ignore
    
    def __post_init__(self):
        if self.to_emails is None:
            self.to_emails = ['danilocrautomacao@gmail.com']
        
        if not self.from_email:
            self.from_email = self.username

class ConfigManager:
    """
    Manages loading of email configuration for the system.
    Static Methods
    --------------
    load_from_env() -> EmailConfig
        Loads email configuration from system environment variables.
        Uses default values if variables are not set.
    load_from_file(settings_path: str = 'email_config.json') -> EmailConfig
        Loads email configuration from a specified JSON file.
        If the file does not exist or an error occurs, falls back to environment variable configuration.
    """
    
    
    @staticmethod
    def load_from_env() -> EmailConfig:
        """
        Loads email configuration from environment variables.
        Returns:
            EmailConfig: An instance of EmailConfig populated with values from environment variables.
                - host (str): SMTP server hostname (default: 'smtp.gmail.com').
                - port (int): SMTP server port (default: 587).
                - username (str): SMTP username (default: '').
                - password (str): SMTP password (default: '').
                - use_tls (bool): Whether to use TLS (default: True if 'SMTP_USE_TLS' is 'true').
                - from_email (str): Sender email address (default: '').
                - to_emails (List[str]): List of recipient email addresses (default: ['danilocrautomacao@gmail.com']).
        Environment Variables:
            SMTP_SERVER: SMTP server hostname.
            SMTP_PORT: SMTP server port.
            SMTP_USERNAME: SMTP username.
            SMTP_PASSWORD: SMTP password.
            SMTP_USE_TLS: Use TLS ('true' or 'false').
            EMAIL_FROM: Sender email address.
            EMAIL_TO: Comma-separated recipient email addresses.
        """
        
        return EmailConfig(
            host=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            port=int(os.getenv('SMTP_PORT', '587')),
            username=os.getenv('SMTP_USERNAME', ''),
            password=os.getenv('SMTP_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            from_email=os.getenv('EMAIL_FROM', ''),
            to_emails=os.getenv('EMAIL_TO', 'danilocrautomacao@gmail.com').split(',')
        )
    
    @staticmethod
    def load_from_file(settings_path: str = 'email_config.json') -> EmailConfig:
        """
        Loads email configuration from a JSON file.
        Attempts to read the configuration from the specified JSON file path.
        If the file exists and is valid, returns an EmailConfig instance populated with the file's data.
        If the file does not exist or an error occurs during loading, logs a warning and falls back to loading configuration from environment variables.
        Args:
            settings_path (str): Path to the JSON configuration file. Defaults to 'email_config.json'.
        Returns:
            EmailConfig: An instance of EmailConfig populated with configuration data.
        """
        
        try:
            settings_file = Path(settings_path)
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return EmailConfig(**data)
        except Exception as e:
            logger.warning(f"Error loading config from file: {e}")
        
        return ConfigManager.load_from_env()