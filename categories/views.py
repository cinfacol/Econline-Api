from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Category, MeasureUnit
from .serializers import CategorySerializer, MeasureUnitSerializer


class ListCategoriesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        if Category.objects.all().exists():
            categories = Category.objects.all()

            result = []

            for category in categories:
                if not category.parent:
                    item = {}
                    item["id"] = category.id
                    item["name"] = category.name
                    item["slug"] = category.slug

                    item["sub_categories"] = []
                    for cat in categories:
                        sub_item = {}
                        if cat.parent and cat.parent.id == category.id:
                            sub_item["id"] = cat.id
                            sub_item["name"] = cat.name
                            sub_item["slug"] = cat.slug
                            sub_item["sub_categories"] = []

                            item["sub_categories"].append(sub_item)
                    result.append(item)
            return Response({"categories": result}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "No categories found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateCategoryView(APIView):
    permission_classes = (
        permissions.IsAdminUser,
    )  # Cambiar según tus necesidades de autorización

    def post(self, request, format=None):
        try:
            data = request.data
            name = data.get("name")
            parent_id = data.get("parent")
            measure_unit_id = data.get("measure_unit")
            is_active = data.get("is_active", True)

            # Validaciones básicas
            if not name:
                return Response(
                    {"error": "El nombre de la categoría es requerido"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not measure_unit_id:
                return Response(
                    {"error": "La unidad de medida es requerida"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verificar que la unidad de medida existe
            try:
                measure_unit = MeasureUnit.objects.get(id=measure_unit_id)
            except MeasureUnit.DoesNotExist:
                return Response(
                    {"error": "La unidad de medida especificada no existe"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verificar que la categoría padre existe (si se proporciona)
            parent = None
            if parent_id:
                try:
                    parent = Category.objects.get(id=parent_id)
                except Category.DoesNotExist:
                    return Response(
                        {"error": "La categoría padre especificada no existe"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Verificar que no existe una categoría con el mismo nombre
            if Category.objects.filter(name=name).exists():
                return Response(
                    {"error": f"Ya existe una categoría con el nombre '{name}'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Crear la categoría
            category_data = {
                "name": name,
                "parent": parent,
                "measure_unit": measure_unit,
                "is_active": is_active,
            }

            category = Category.objects.create(**category_data)

            # Serializar la respuesta
            serializer = CategorySerializer(category)

            return Response(
                {
                    "message": "Categoría creada exitosamente",
                    "category": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ListMeasureUnitsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        try:
            measure_units = MeasureUnit.objects.all()
            serializer = MeasureUnitSerializer(measure_units, many=True)

            return Response(
                {"measure_units": serializer.data},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Error al obtener las unidades de medida: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateMeasureUnitView(APIView):
    permission_classes = (
        permissions.AllowAny,
    )  # Cambiar según tus necesidades de autorización

    def post(self, request, format=None):
        try:
            data = request.data
            description = data.get("description", "").strip()

            # Validaciones básicas
            if not description:
                return Response(
                    {"error": "La descripción de la unidad de medida es requerida"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verificar que no existe una unidad de medida con la misma descripción
            if MeasureUnit.objects.filter(description=description).exists():
                return Response(
                    {
                        "error": f"Ya existe una unidad de medida con la descripción '{description}'"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar longitud mínima y máxima
            if len(description) < 2:
                return Response(
                    {"error": "La descripción debe tener al menos 2 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(description) > 100:
                return Response(
                    {"error": "La descripción no puede exceder 100 caracteres"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verificar si es una unidad predefinida o personalizada
            valid_choices = [choice[0] for choice in MeasureUnit.MeasureType.choices]
            is_custom = description not in valid_choices

            # Crear la unidad de medida
            measure_unit = MeasureUnit.objects.create(
                description=description, is_custom=is_custom
            )

            # Serializar la respuesta
            serializer = MeasureUnitSerializer(measure_unit)

            return Response(
                {
                    "message": "Unidad de medida creada exitosamente",
                    "measure_unit": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Error interno del servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
