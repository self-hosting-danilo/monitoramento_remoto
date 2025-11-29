from .configs import EmailConfig, ConfigManager, logger
from .process import ProcessData

import time
import threading
import smtplib
from threading import Lock
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class HandleMail:
    """
    HandleMail - Alert Email Manager
    Class responsible for managing the sending of alert emails based on received data.
    Implements rate control (cooldown), automatic retry, and synchronous sending with timeout.
    Attributes:
        _email_lock (Lock): Lock for thread synchronization in email sending
        _last_email_time (Dict[str, float]): Dictionary tracking last send time per hospital
        EMAIL_COOLDOWN (int): Minimum interval between emails for the same hospital (300s)
        MAX_RETRIES (int): Maximum number of send attempts (3)
        RETRY_DELAY (int): Interval between retry attempts (5s)
        _settings (Optional[EmailConfig]): Loaded email configuration
    Methods:
        initialize(settings: Optional[EmailConfig]) -> None
            Initializes the class with email configuration. If not provided, loads from file.
        get_settings() -> EmailConfig
            Returns the current configuration, initializing if necessary.
        send(data: Any) -> bool
            Sends alert email based on received data.
            Handles two types of data: dictionaries (hospital/power plant) and strings (offline).
            Returns True if sent successfully, False otherwise.
        _send_offline_mail(data: str) -> bool
            Sends alert email for offline device.
        __send_email_smtp(title: str, body: str) -> bool
            Sends email using SMTP protocol with loaded configurations.
            Supports TLS and authentication.
        __send_email_sync(title: str, body: str) -> bool
            Helper for synchronous sending with automatic retry mechanism.
            Performs up to MAX_RETRIES attempts with RETRY_DELAY between them.
        __send_email(title: str, body: str, timeout: int = 30) -> bool
            Sends email with timeout using threading.
            Executes sending in a separate thread with synchronization via lock.
            Returns False if the specified timeout is exceeded.
        _should_send_email(hospital_name: str) -> bool
            Checks if email should be sent based on cooldown per hospital.
            Prevents spam by limiting sends for the same hospital every EMAIL_COOLDOWN seconds.
    """

    _email_lock = Lock()
    _last_email_time: Dict[str, float] = {}
    EMAIL_COOLDOWN = 300  # 5 minutes
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds between attempts
    
    _settings: Optional[EmailConfig] = None

    @classmethod
    def initialize(cls, settings: Optional[EmailConfig] = None):
        """
        Initialize the email handler class with configuration settings.
        This class method sets up the HandleMail class with email configuration parameters.
        If no settings are provided, it attempts to load configuration from a file using ConfigManager.
        Once initialized, the class logs the successful setup.
        Args:
            settings (Optional[EmailConfig]): Email configuration object. If None, configuration
                will be loaded from file using ConfigManager.load_from_file().
        Returns:
            None
        Raises:
            Logs an info message upon successful initialization.
        Note:
            This is a class method that sets the cls._settings attribute used by other
            methods in the HandleMail class.
        """
        if settings:
            cls._settings = settings
        else:
            cls._settings = ConfigManager.load_from_file()
        
        logger.info("HandleMail initialized with email configurations")

    @classmethod
    def get_settings(cls) -> EmailConfig:
        """
        Retrieves the current email configuration settings.
        
        Initializes the configuration if it has not been previously set.
        This method ensures that the EmailConfig object is always available
        by performing lazy initialization on first access.
        
        Returns:
            EmailConfig: The current email configuration object containing
                         all necessary settings for email operations.
        
        Note:
            The returned value is type-ignored to suppress type checking warnings
            related to the optional _settings class variable.
        """
        if cls._settings is None:
            cls.initialize()
        return cls._settings #type:ignore

    @classmethod
    def send(cls, data: Any) -> bool:
        """
        Send email notification based on data type and hospital configuration.
        Args:
            data (Any): The data to process and send via email. Can be a dictionary with hospital
                        and type information, or a string for offline mail handling.
        Returns:
            bool: True if email was sent successfully, False otherwise.
        Raises:
            Catches all exceptions and logs them, returning False on error.
        Notes:
            - For dictionary input: Processes hospital name and checks if email should be sent
            - For "usina" type: Handles power plant email processing
            - For other types: Handles hospital email processing
            - For non-dict input: Sends offline mail with string representation of data
            - Logs hospital name and any errors during processing
        """
    
        if isinstance(data, dict):
            try:
                hospital_name = data.get("Hospital", "Unknown")
                logger.info(f"Processing data for hospital: {hospital_name}")
                
                if not cls._should_send_email(hospital_name):
                    return False
                
                if data.get("tipo") == "usina":
                    mail_status_usina = cls.__send_email(*ProcessData._handle_usina_email(data))
                    return mail_status_usina
                else:
                    mail_status_central = cls.__send_email(*ProcessData._handle_hospital_email(data))
                    return mail_status_central
        
            except Exception as e:
                logger.error(f"General error in HandleMail.send: {e}")
                return False
        else:
            return cls._send_offline_mail(str(data))

    
    @classmethod
    def _send_offline_mail(cls, data: str) -> bool:
        """
        Send an alert email indicating that a device has gone offline.
        Parameters
        ----------
        data : str
            The message body or payload describing the offline event. Expected to contain
            details such as device identifier, timestamp, and any relevant context.
        Returns
        -------
        bool
            True if the email was successfully sent, False otherwise.
        Notes
        -----
        This is an internal helper that constructs an email with a preset alert title
        and delegates the actual sending to the class-level email-sending routine
        (__send_email_sync). Exceptions from the underlying send routine may be raised
        or handled by that routine.
        """
       
        title = 'ALERT: Device Connection!'
        return cls.__send_email_sync(title, data)

    @classmethod
    def __send_email_smtp(cls, title: str, body: str) -> bool:
        """
        Send an email via SMTP protocol.
        This method sends an email using the configured SMTP settings. It retrieves
        email credentials and server configuration, establishes an SMTP connection,
        and sends the email with the provided title and body.
        Args:
            cls: The class reference (for class method).
            title (str): The subject line of the email.
            body (str): The body content of the email in plain text format.
        Returns:
            bool: True if the email was sent successfully, False otherwise.
        Raises:
            No exceptions are raised; errors are caught and logged.
        Notes:
            - Email credentials (username and password) must be configured in settings.
            - The method supports optional TLS encryption based on settings.
            - The 'From' field defaults to the configured from_email or username.
            - The 'To' field is populated from the configured to_emails list.
            - Connection timeout is set to 15 seconds.
            - All exceptions are logged with error details.
        """
        
        try:
            settings = cls.get_settings()
            
            if not settings.username or not settings.password:
                logger.error("Email credentials not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = settings.from_email or settings.username
            msg['To'] = ', '.join(settings.to_emails)
            msg['Subject'] = title
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(settings.host, settings.port, timeout=15)
            
            if settings.use_tls:
                server.starttls()
            
            server.login(settings.username, settings.password)
            text = msg.as_string()
            server.sendmail(settings.from_email or settings.username, settings.to_emails, text)
            server.quit()
            
            logger.info(f"Email sent successfully: {title}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False

    @classmethod
    def __send_email_sync(cls, title: str, body: str) -> bool:
        """
        Attempt to send an email synchronously, retrying on failure.
        This class method obtains email configuration from cls.get_settings() and attempts
        to send an email using the helper cls.__send_email_smtp(title, body). It performs
        up to cls.MAX_RETRIES attempts and waits cls.RETRY_DELAY seconds between retries
        when an attempt fails. All exceptions raised during an attempt are caught and
        logged; this method does not propagate exceptions.
        Parameters:
            cls: The class on which this method is called. Expected to define:
                 - get_settings() -> object with attributes `username` and `host`
                 - MAX_RETRIES (int)
                 - RETRY_DELAY (int or float)
                 - __send_email_smtp(title: str, body: str) -> bool
            title (str): Subject or title of the email.
            body (str): Body/content of the email.
        Returns:
            bool: True if the email was sent successfully (i.e., cls.__send_email_smtp returned True
            on any attempt). False if required settings are missing or all retry attempts failed.
        Side effects:
            - Logs informational, warning and error messages.
            - Performs blocking network I/O via the SMTP helper.
            - Sleeps (blocks) between retry attempts using time.sleep().
            - Does not guarantee thread-safety.
        Notes:
            - If settings.username or settings.host are missing, the method logs a warning and
              returns False immediately.
            - The method name is private (double-underscore); it is intended for internal use.
        """
        
        
        settings = cls.get_settings()
        
        if not settings.username or not settings.host:
            logger.warning("Email settings not found")
            return False

        for attempt in range(cls.MAX_RETRIES):
            try:
                logger.info(f"Attempt {attempt + 1} to send email: {title}")
                
                if cls.__send_email_smtp(title, body):
                    return True
                
                if attempt < cls.MAX_RETRIES - 1:
                    logger.info(f"Waiting {cls.RETRY_DELAY}s before next attempt...")
                    time.sleep(cls.RETRY_DELAY)
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                if attempt < cls.MAX_RETRIES - 1:
                    time.sleep(cls.RETRY_DELAY)
        
        logger.error(f"Failed in all {cls.MAX_RETRIES} send attempts")
        return False

    @classmethod
    def __send_email(cls, title: str, body: str, timeout: int = 30) -> bool:
        """
        Send an email asynchronously with a timeout mechanism.
        This method sends an email in a separate thread to prevent blocking operations.
        It uses a lock to ensure thread-safe access to the email sending functionality
        and implements a timeout to prevent indefinite waiting.
        Args:
            title (str): The subject line of the email.
            body (str): The body content of the email.
            timeout (int, optional): Maximum time in seconds to wait for the email to be sent.
                                    Defaults to 30 seconds.
        Returns:
            bool: True if the email was sent successfully within the timeout period,
                  False if a timeout occurred, an exception was raised, or the send operation failed.
        Raises:
            None (exceptions are caught and logged internally).
        Note:
            - The email is sent in a daemon thread to avoid blocking the main thread.
            - If the thread exceeds the timeout, it will be abandoned and False is returned.
            - All exceptions during sending are caught, logged, and result in a False return value.
            - Thread safety is ensured through the use of cls._email_lock.
        """
        
        result: List[bool] = [False]
        exception_info: List[Optional[str]] = [None]
        
        def email_worker():
            try:
                with cls._email_lock:
                    result[0] = cls.__send_email_sync(title, body)
            except Exception as e:
                exception_info[0] = str(e)
                logger.error(f"Error in email worker: {e}")
        
        email_thread = threading.Thread(target=email_worker, daemon=True)
        email_thread.start()
        
        email_thread.join(timeout=timeout)
        
        if email_thread.is_alive():
            logger.error(f"Timeout sending email '{title}' after {timeout}s")
            return False
        
        if exception_info[0]:
            logger.error(f"Error sending email: {exception_info[0]}")
            return False
            
        return result[0]

    @classmethod
    def _should_send_email(cls, hospital_name: str) -> bool:
        """
        Determines whether an email should be sent based on cooldown period.
        This method checks if enough time has elapsed since the last email was sent
        for a given hospital. It implements a cooldown mechanism to prevent email flooding.
        Args:
            hospital_name (str): The name of the hospital to check cooldown status for.
        Returns:
            bool: True if the cooldown period has elapsed and email should be sent,
                  False if the email is blocked due to active cooldown.
        Side Effects:
            - Updates the `_last_email_time` dictionary with current timestamp if cooldown
              has elapsed.
            - Logs an info message if email is blocked due to cooldown, including the
              time remaining until the next email can be sent.
        """
        """Checks if email should be sent based on cooldown"""
        current_time = time.time()
        last_time = cls._last_email_time.get(hospital_name, 0)
        
        if current_time - last_time > cls.EMAIL_COOLDOWN:
            cls._last_email_time[hospital_name] = current_time
            return True
        
        logger.info(f"Email blocked by cooldown for {hospital_name} (last {(current_time - last_time):.0f}s)")
        return False

