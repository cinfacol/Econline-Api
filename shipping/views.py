from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from .models import Shipping
from .serializers import ShippingSerializer, ShippingCalculationSerializer
from .services import ServientregaService
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
import logging
from decimal import Decimal
from django.db.models import Q

logger = logging.getLogger(__name__)

class ShippingViewSet(ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ShippingSerializer
    queryset = Shipping.objects.filter(is_active=True)

    def get_queryset(self):
        """
        Retorna solo los métodos de envío activos
        """
        return Shipping.objects.filter(is_active=True)

    @extend_schema(
        responses=ShippingSerializer,
        description="Lista todas las opciones de envío activas",
        examples=[
            OpenApiExample(
                'Respuesta exitosa',
                value={
                    "shipping_options": [
                        {
                            "id": "uuid",
                            "name": "Envío Estándar",
                            "service_type": "NACIONAL",
                            "transport_type": "TERRESTRE",
                            "standard_shipping_cost": "3.00",
                            "free_shipping_threshold": "15.00",
                            "is_active": True,
                            "time_to_delivery": "3-5 días",
                            "is_free_shipping": False,
                            "estimated_delivery_days": "3-5 días"
                        }
                    ],
                    "message": "Opciones de envío activas obtenidas exitosamente"
                }
            )
        ]
    )
    def list(self, request):
        """
        Lista todas las opciones de envío activas
        """
        try:
            queryset = self.get_queryset()
            order_total = Decimal(request.query_params.get('order_total', '0'))
            
            serializer = self.get_serializer(
                queryset, 
                many=True,
                context={'order_total': order_total}
            )
            
            return Response(
                {
                    "shipping_options": serializer.data,
                    "message": _("Opciones de envío activas obtenidas exitosamente")
                }, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error al obtener opciones de envío: {str(e)}")
            return Response(
                {"error": _("Error al obtener opciones de envío")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        responses=ShippingSerializer,
        description="Obtiene los detalles de una opción de envío específica",
        parameters=[
            OpenApiParameter(
                name='order_total',
                type=float,
                description='Total de la orden para calcular si el envío es gratuito'
            )
        ]
    )
    def retrieve(self, request, pk=None):
        """
        Obtiene los detalles de una opción de envío específica
        """
        try:
            shipping = Shipping.objects.get(id=pk, is_active=True)
            order_total = Decimal(request.query_params.get('order_total', '0'))
            
            serializer = ShippingSerializer(
                shipping,
                context={'order_total': order_total}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Shipping.DoesNotExist:
            return Response(
                {"error": _("Opción de envío no encontrada")},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error al obtener opción de envío: {str(e)}")
            return Response(
                {"error": _("Error al obtener opción de envío")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        request=ShippingCalculationSerializer,
        responses=ShippingSerializer,
        description="Calcula el costo de envío basado en el total de la orden",
        examples=[
            OpenApiExample(
                'Solicitud',
                value={
                    "order_total": "100.00",
                    "shipping_id": "uuid",
                    "weight": "1.0",
                    "origin_code": "11001"
                }
            )
        ]
    )
    @action(detail=False, methods=['post'])
    def calculate_shipping(self, request):
        """
        Calcula el costo de envío basado en el total de la orden
        """
        try:
            # Validar datos de entrada
            logger.info(f"Datos de entrada: {request.data}")
            serializer = ShippingCalculationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            logger.info(f"Datos validados: {data}")

            # Obtener método de envío
            if data.get('shipping_id'):
                try:
                    shipping_id = str(data['shipping_id'])
                    logger.info(f"Buscando envío con ID: {shipping_id}")
                    
                    # Verificar si el envío existe sin el filtro de is_active
                    shipping = Shipping.objects.get(id=shipping_id)
                    logger.info(f"Envió encontrado (sin filtro): {shipping.name} (ID: {shipping.id}, Activo: {shipping.is_active})")
                    
                    # Verificar si está activo
                    if not shipping.is_active:
                        logger.error(f"Envió encontrado pero no está activo: {shipping.name}")
                        return Response(
                            {"error": _("La opción de envío seleccionada no está disponible")},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                except Shipping.DoesNotExist:
                    logger.error(f"Envió no encontrado con ID: {shipping_id}")
                    return Response(
                        {"error": _("Opción de envío no encontrada")},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                shipping = Shipping.objects.filter(is_active=True).order_by('standard_shipping_cost').first()
                if not shipping:
                    return Response(
                        {"error": _("No hay opciones de envío disponibles")},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Calcular costo de envío
            shipping_cost = shipping.calculate_shipping_cost(data['order_total'])
            logger.info(f"Costo de envío calculado: {shipping_cost}")
            
            response_data = {
                "shipping_method": ShippingSerializer(
                    shipping,
                    context={'order_total': data['order_total']}
                ).data,
                "order_total": data['order_total'],
                "shipping_cost": shipping_cost,
                "is_free_shipping": shipping_cost == 0,
                "total_with_shipping": data['order_total'] + shipping_cost
            }

            # Obtener cotización de Servientrega si es posible
            if request.user.is_authenticated:
                user_address = request.user.address_set.filter(is_default=True).first()
                if user_address and data.get('origin_code'):
                    try:
                        servientrega_service = ServientregaService()
                        servientrega_quote = servientrega_service.cotizar_envio(
                            origen_codigo=data['origin_code'],
                            destino_codigo=user_address.postal_zip_code,
                            peso=data.get('weight', Decimal('1.0')),
                            valor_declarado=float(data['order_total']),
                            tipo_servicio=shipping.service_type
                        )
                        response_data['servientrega_quote'] = servientrega_quote
                    except Exception as e:
                        logger.error(f"Error al obtener cotización de Servientrega: {str(e)}")
                        # Continuamos sin la cotización de Servientrega

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al calcular envío: {str(e)}")
            return Response(
                {"error": _("Error al calcular el costo de envío")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
