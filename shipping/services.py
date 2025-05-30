import requests
import logging
from django.conf import settings
from typing import Dict, Optional, List
from decimal import Decimal

logger = logging.getLogger(__name__)

class ServientregaService:
    BASE_URL = "https://mobile.servientrega.com/ApiIngresoCLientes/api"
    
    def __init__(self):
        self.api_key = settings.SERVIENTREGA_API_KEY
        self.username = settings.SERVIENTREGA_USERNAME
        self.password = settings.SERVIENTREGA_PASSWORD
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """
        Realiza una petición a la API de Servientrega
        """
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a Servientrega: {str(e)}")
            raise

    def cotizar_envio(
        self,
        origen_codigo: str,
        destino_codigo: str,
        peso: Decimal,
        valor_declarado: Decimal,
        tipo_servicio: str = "NACIONAL"
    ) -> Dict:
        """
        Cotiza un envío usando la API de Servientrega
        """
        data = {
            "OrigenCodigo": origen_codigo,
            "DestinoCodigo": destino_codigo,
            "Peso": float(peso),
            "ValorDeclarado": float(valor_declarado),
            "TipoServicio": tipo_servicio
        }
        return self._make_request("CotizacionEnvio", method="POST", data=data)

    def generar_guia(
        self,
        remitente: Dict,
        destinatario: Dict,
        paquete: Dict,
        servicio: str = "NACIONAL"
    ) -> Dict:
        """
        Genera una guía de envío
        """
        data = {
            "Remitente": remitente,
            "Destinatario": destinatario,
            "Paquete": paquete,
            "Servicio": servicio
        }
        return self._make_request("GeneracionGuia", method="POST", data=data)

    def consultar_guia(self, numero_guia: str) -> Dict:
        """
        Consulta el estado de una guía
        """
        return self._make_request(f"ConsultaGuias/{numero_guia}")

    def validar_codigo_postal(self, codigo: str) -> bool:
        """
        Valida si un código postal es válido
        """
        try:
            self._make_request(f"ValidarCodigoPostal/{codigo}")
            return True
        except:
            return False 