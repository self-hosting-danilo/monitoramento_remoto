from .configs import EmailConfig, ConfigManager, logger
import time
import threading
import smtplib
from threading import Lock
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSender:
    """
    EmailSender - Gerenciador de Envio de Emails
    
    Classe responsável exclusivamente pelo envio de emails via SMTP.
    Implementa retry automático e envio síncrono com timeout.
    
    Attributes:
        _email_lock (Lock): Lock para sincronização de threads no envio
        MAX_RETRIES (int): Número máximo de tentativas de envio (3)
        RETRY_DELAY (int): Intervalo entre tentativas (5s)
        _settings (Optional[EmailConfig]): Configuração de email carregada
    
    Methods:
        initialize(settings: Optional[EmailConfig]) -> None
            Inicializa a classe com configurações de email.
        
        get_settings() -> EmailConfig
            Retorna a configuração atual, inicializando se necessário.
        
        send(title: str, body: str, timeout: int = 30) -> bool
            Envia email com título e corpo especificados.
            Retorna True se enviado com sucesso, False caso contrário.
        
        _send_sync(title: str, body: str) -> bool
            Envia email de forma síncrona com retry automático.
        
        _send_smtp(title: str, body: str) -> bool
            Envia email usando protocolo SMTP.
    """
    
    _email_lock = Lock()
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # segundos entre tentativas
    
    _settings: Optional[EmailConfig] = None
    
    @classmethod
    def initialize(cls, settings: Optional[EmailConfig] = None):
        """
        Inicializa o gerenciador de email com configurações.
        
        Args:
            settings (Optional[EmailConfig]): Objeto de configuração de email.
                Se None, carrega configuração de arquivo.
        """
        if settings:
            cls._settings = settings
        else:
            cls._settings = ConfigManager.load_from_file()
        
        logger.info("EmailSender inicializado com configurações de email")
    
    @classmethod
    def get_settings(cls) -> EmailConfig:
        """
        Retorna as configurações de email atuais.
        
        Inicializa a configuração se ainda não foi feita.
        
        Returns:
            EmailConfig: Objeto de configuração de email.
        """
        if cls._settings is None:
            cls.initialize()
        return cls._settings  # type: ignore
    
    @classmethod
    def send(cls, title: str, body: str, timeout: int = 30) -> bool:
        """
        Envia email de forma assíncrona com mecanismo de timeout.
        
        Envia o email em uma thread separada para evitar bloqueio.
        Usa lock para garantir acesso thread-safe e implementa timeout.
        
        Args:
            title (str): Assunto do email.
            body (str): Corpo do email.
            timeout (int): Tempo máximo em segundos para enviar (padrão: 30s).
        
        Returns:
            bool: True se enviado com sucesso dentro do timeout,
                  False se timeout, exceção ou falha no envio.
        """
        result: List[bool] = [False]
        exception_info: List[Optional[str]] = [None]
        
        def email_worker():
            try:
                with cls._email_lock:
                    result[0] = cls._send_sync(title, body)
            except Exception as e:
                exception_info[0] = str(e)
                logger.error(f"Erro no worker de email: {e}")
        
        email_thread = threading.Thread(target=email_worker, daemon=True)
        email_thread.start()
        
        email_thread.join(timeout=timeout)
        
        if email_thread.is_alive():
            logger.error(f"Timeout ao enviar email '{title}' após {timeout}s")
            return False
        
        if exception_info[0]:
            logger.error(f"Erro ao enviar email: {exception_info[0]}")
            return False
        
        return result[0]
    
    @classmethod
    def _send_sync(cls, title: str, body: str) -> bool:
        """
        Envia email de forma síncrona com retry automático.
        
        Tenta enviar o email até MAX_RETRIES vezes, aguardando
        RETRY_DELAY segundos entre tentativas em caso de falha.
        
        Args:
            title (str): Assunto do email.
            body (str): Corpo do email.
        
        Returns:
            bool: True se enviado com sucesso em alguma tentativa,
                  False se todas as tentativas falharem.
        """
        settings = cls.get_settings()
        
        if not settings.username or not settings.host:
            logger.warning("Configurações de email não encontradas")
            return False
        
        for attempt in range(cls.MAX_RETRIES):
            try:
                logger.info(f"Tentativa {attempt + 1} de enviar email: {title}")
                
                if cls._send_smtp(title, body):
                    return True
                
                if attempt < cls.MAX_RETRIES - 1:
                    logger.info(f"Aguardando {cls.RETRY_DELAY}s antes da próxima tentativa...")
                    time.sleep(cls.RETRY_DELAY)
                    
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt < cls.MAX_RETRIES - 1:
                    time.sleep(cls.RETRY_DELAY)
        
        logger.error(f"Falha em todas as {cls.MAX_RETRIES} tentativas de envio")
        return False
    
    @classmethod
    def _send_smtp(cls, title: str, body: str) -> bool:
        """
        Envia email via protocolo SMTP.
        
        Usa as configurações carregadas para estabelecer conexão SMTP,
        autentica e envia o email.
        
        Args:
            title (str): Assunto do email.
            body (str): Corpo do email em texto plano.
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário.
        """
        try:
            settings = cls.get_settings()
            
            if not settings.username or not settings.password:
                logger.error("Credenciais de email não configuradas")
                return False
            
            # Monta a mensagem
            msg = MIMEMultipart()
            msg['From'] = settings.from_email or settings.username
            msg['To'] = ', '.join(settings.to_emails)
            msg['Subject'] = title
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Conecta ao servidor SMTP
            server = smtplib.SMTP(settings.host, settings.port, timeout=15)
            
            if settings.use_tls:
                server.starttls()
            
            # Autentica e envia
            server.login(settings.username, settings.password)
            text = msg.as_string()
            server.sendmail(
                settings.from_email or settings.username,
                settings.to_emails,
                text
            )
            server.quit()
            
            logger.info(f"Email enviado com sucesso: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Erro no envio SMTP: {e}")
            return False