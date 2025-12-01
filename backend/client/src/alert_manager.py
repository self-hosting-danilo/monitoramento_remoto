from .configs import logger
from .process import ProcessData
from .email_sender import EmailSender
import time
from typing import Dict, Any, Tuple, Optional


class AlertManager:
    """
    AlertManager - Gerenciador de Alertas
    
    Classe responsável por processar dados de monitoramento, verificar TODOS os parâmetros,
    e enviar um único alerta consolidado se algum estiver fora do padrão.
    
    O cooldown é controlado por hospital, evitando spam de alertas.
    
    Attributes:
        _last_alert_time (Dict[str, float]): Rastreamento do último alerta por hospital
        ALERT_COOLDOWN (int): Intervalo mínimo entre alertas para o mesmo hospital (1800s)
    
    Methods:
        process_data(data: Any) -> bool
            Processa TODOS os dados recebidos e decide se deve enviar alerta.
            Retorna True se alerta foi enviado, False caso contrário.
        
        _process_usina_data(data: dict) -> Tuple[Optional[str], Optional[str]]
            Verifica TODOS os parâmetros da usina e retorna título e corpo do alerta.
        
        _process_hospital_data(data: dict) -> Tuple[Optional[str], Optional[str]]
            Verifica TODOS os parâmetros do hospital e retorna título e corpo do alerta.
        
        _process_offline_data(data: str) -> Tuple[str, str]
            Processa alertas de dispositivo offline.
        
        _should_send_alert(hospital_name: str) -> bool
            Verifica se deve enviar alerta baseado no cooldown por hospital.
        
        _send_alert_if_needed(hospital_name: str, title: Optional[str], body: Optional[str]) -> bool
            Envia alerta se houver problemas e o cooldown permitir.
    """
    
    _last_alert_time: Dict[str, float] = {}
    ALERT_COOLDOWN = 1800  # 30 minutos entre alertas do mesmo hospital
    
    @classmethod
    def process_data(cls, data: Any) -> bool:
        """
        Processa TODOS os dados recebidos e verifica se algum está fora do padrão.
        
        Fluxo:
        1. Processa todos os parâmetros
        2. Identifica todos os problemas
        3. Se houver problemas E cooldown permitir -> envia alerta consolidado
        4. Atualiza timestamp do último alerta para aquele hospital
        
        Args:
            data: Pode ser um dicionário com dados de monitoramento ou
                  uma string indicando dispositivo offline.
        
        Returns:
            bool: True se alerta foi enviado com sucesso, False caso contrário.
        """
        if isinstance(data, dict):
            try:
                hospital_name = data.get("Hospital", "Unknown")
                logger.info(f"Processando dados para hospital: {hospital_name}")
                
                # Processa baseado no tipo e obtém resultado da verificação
                if data.get("tipo") == "usina":
                    title, body = cls._process_usina_data(data)
                else:
                    title, body = cls._process_hospital_data(data)
                
                # Envia alerta apenas se houver problemas E cooldown permitir
                return cls._send_alert_if_needed(hospital_name, title, body)
                    
            except Exception as e:
                logger.error(f"Erro ao processar dados de alerta: {e}")
                return False
        else:
            # Alerta de dispositivo offline
            title, body = cls._process_offline_data(str(data))
            hospital_name = "Sistema"  # Usa nome genérico para offline
            return cls._send_alert_if_needed(hospital_name, title, body)
    
    @classmethod
    def _process_usina_data(cls, data: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa e verifica TODOS os parâmetros da usina de oxigênio.
        
        Verifica todos os valores contra as regras definidas em ProcessData.USINA_RULES
        e ProcessData.FLAG_RULES. Se algum parâmetro estiver fora do padrão,
        retorna um alerta consolidado com todos os problemas encontrados.
        
        Args:
            data (dict): Dados da usina contendo parâmetros de monitoramento.
        
        Returns:
            Tuple[Optional[str], Optional[str]]: 
                - (title, body) se problemas forem detectados
                - (None, None) se tudo estiver normal
        """
        try:
            # ProcessData já verifica TODOS os parâmetros e retorna título e corpo
            title, body = ProcessData._handle_usina_email(data)
            
            # Verifica se é realmente um alerta (começa com "ALERT")
            if title and title.startswith("ALERT"):
                logger.info(f"Problemas detectados na usina: {data.get('Hospital')}")
                return title, body
            else:
                logger.info(f"Todos os parâmetros normais na usina: {data.get('Hospital')}")
                return None, None
            
        except Exception as e:
            logger.error(f"Erro ao processar dados de usina: {e}")
            return None, None
    
    @classmethod
    def _process_hospital_data(cls, data: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Processa e verifica TODOS os parâmetros do hospital.
        
        Verifica todos os valores contra as regras definidas em ProcessData.HOSPITAL_RULES
        e ProcessData.FLAG_RULES. Se algum parâmetro estiver fora do padrão,
        retorna um alerta consolidado com todos os problemas encontrados.
        
        Args:
            data (dict): Dados do hospital contendo parâmetros de monitoramento.
        
        Returns:
            Tuple[Optional[str], Optional[str]]: 
                - (title, body) se problemas forem detectados
                - (None, None) se tudo estiver normal
        """
        try:
            # ProcessData já verifica TODOS os parâmetros e retorna título e corpo
            title, body = ProcessData._handle_hospital_email(data)
            
            # Verifica se é realmente um alerta (começa com "ALERT")
            if title and title.startswith("ALERT"):
                logger.info(f"Problemas detectados no hospital: {data.get('Hospital')}")
                return title, body
            else:
                logger.info(f"Todos os parâmetros normais no hospital: {data.get('Hospital')}")
                return None, None
            
        except Exception as e:
            logger.error(f"Erro ao processar dados de hospital: {e}")
            return None, None
    
    @classmethod
    def _process_offline_data(cls, data: str) -> Tuple[str, str]:
        """
        Processa alerta de dispositivo offline.
        
        Args:
            data (str): Mensagem descrevendo o dispositivo offline.
        
        Returns:
            Tuple[str, str]: (title, body) do alerta.
        """
        title = 'ALERT: Device Connection!'
        body = f'Dispositivo desconectado:\n\n{data}'
        logger.info("Dispositivo offline detectado")
        return title, body
    
    @classmethod
    def _send_alert_if_needed(cls, hospital_name: str, title: Optional[str], body: Optional[str]) -> bool:
        """
        Envia alerta se houver problemas detectados E o cooldown permitir.
        
        Fluxo:
        1. Se não há título/corpo -> não há problemas -> retorna False
        2. Verifica cooldown para o hospital
        3. Se cooldown permite -> envia alerta e atualiza timestamp
        4. Se cooldown bloqueia -> apenas loga e retorna False
        
        Args:
            hospital_name (str): Nome do hospital.
            title (Optional[str]): Título do alerta (None se sem problemas).
            body (Optional[str]): Corpo do alerta (None se sem problemas).
        
        Returns:
            bool: True se alerta foi enviado, False caso contrário.
        """
        # Se não há título ou corpo, não há problemas
        if not title or not body:
            return False
        
        # Verifica cooldown
        if not cls._should_send_alert(hospital_name):
            logger.info(
                f"Problemas detectados em {hospital_name}, mas alerta bloqueado por cooldown"
            )
            return False
        
        # Envia o alerta
        logger.info(f"Enviando alerta para {hospital_name}: {title}")
        success = EmailSender.send(title, body)
        
        if success:
            # Atualiza timestamp do último alerta para este hospital
            cls._last_alert_time[hospital_name] = time.time()
            logger.info(f"Alerta enviado com sucesso para {hospital_name}")
        else:
            logger.error(f"Falha ao enviar alerta para {hospital_name}")
        
        return success
    
    @classmethod
    def _should_send_alert(cls, hospital_name: str) -> bool:
        """
        Verifica se deve enviar alerta baseado no período de cooldown POR HOSPITAL.
        
        Cada hospital tem seu próprio timer de cooldown. Isso significa que:
        - Hospital A pode receber alerta mesmo se Hospital B recebeu há 1 minuto
        - Mas Hospital A só receberá novo alerta após ALERT_COOLDOWN segundos do último alerta dele
        
        Args:
            hospital_name (str): Nome do hospital a verificar.
        
        Returns:
            bool: True se cooldown expirou e alerta pode ser enviado,
                  False se ainda está em cooldown.
        """
        current_time = time.time()
        last_time = cls._last_alert_time.get(hospital_name, 0)
        
        time_elapsed = current_time - last_time
        
        # Se passou tempo suficiente desde o último alerta DESTE hospital
        if time_elapsed > cls.ALERT_COOLDOWN:
            return True
        
        # Ainda em cooldown
        time_remaining = cls.ALERT_COOLDOWN - time_elapsed
        minutes_remaining = time_remaining / 60
        
        logger.info(
            f"Cooldown ativo para {hospital_name}: "
            f"faltam {minutes_remaining:.1f} minutos para próximo alerta"
        )
        return False
    
    @classmethod
    def reset_cooldown(cls, hospital_name: str) -> None:
        """
        Reseta o cooldown de um hospital específico (útil para testes ou admin).
        
        Args:
            hospital_name (str): Nome do hospital para resetar cooldown.
        """
        if hospital_name in cls._last_alert_time:
            del cls._last_alert_time[hospital_name]
            logger.info(f"Cooldown resetado para {hospital_name}")
    
    @classmethod
    def get_cooldown_status(cls, hospital_name: str) -> Dict[str, Any]:
        """
        Retorna o status do cooldown de um hospital.
        
        Args:
            hospital_name (str): Nome do hospital.
        
        Returns:
            Dict contendo:
                - in_cooldown (bool): Se está em cooldown
                - last_alert_time (float): Timestamp do último alerta
                - time_remaining (float): Segundos restantes de cooldown
                - can_send_alert (bool): Se pode enviar alerta agora
        """
        current_time = time.time()
        last_time = cls._last_alert_time.get(hospital_name, 0)
        time_elapsed = current_time - last_time
        time_remaining = max(0, cls.ALERT_COOLDOWN - time_elapsed)
        
        return {
            'hospital': hospital_name,
            'in_cooldown': time_remaining > 0,
            'last_alert_time': last_time,
            'time_elapsed': time_elapsed,
            'time_remaining': time_remaining,
            'minutes_remaining': time_remaining / 60,
            'can_send_alert': time_remaining == 0
        }