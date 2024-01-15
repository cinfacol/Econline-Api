from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from products.models import Product

from .models import Rating

User = settings.AUTH_USER_MODEL


# todos los reviews de un producto
class GetProductRatingsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, productId, format=None):
        try:
            product_id = str(productId)
        except:
            return Response(
                {"error": "Product ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not Product.objects.filter(id=product_id).exists():
                return Response(
                    {"error": "This product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product = Product.objects.get(id=product_id)

            results = []

            if Rating.objects.filter(product=product).exists():
                ratings = Rating.objects.order_by("-created_at").filter(product=product)

                for rating in ratings:
                    item = {}

                    item["id"] = rating.id
                    item["rating"] = rating.rating
                    item["comment"] = rating.comment
                    item["created_at"] = rating.created_at
                    item["rater"] = rating.rater.username

                    results.append(item)

            return Response({"ratings": results}, status=status.HTTP_200_OK)

        except:
            return Response(
                {"error": "Something went wrong when retrieving ratings"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# una review (rating) en particular de un producto
class GetProductRatingView(APIView):
    def get(self, request, productId, format=None):
        user = self.request.user

        try:
            product_id = str(productId)
        except:
            return Response(
                {"error": "Product ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not Product.objects.filter(id=product_id).exists():
                return Response(
                    {"error": "This product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product = Product.objects.get(id=product_id)
            result = {}

            if Rating.objects.filter(rater=user, product=product).exists():
                rating = Rating.objects.get(rater=user, product=product)

                result["id"] = rating.id
                result["rating"] = rating.rating
                result["comment"] = rating.comment
                result["created_at"] = rating.created_at
                result["rater"] = rating.rater.username

            return Response({"rating": result}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when retrieving rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateProductRatingView(APIView):
    def post(self, request, productId, format=None):
        user = self.request.user
        data = self.request.data

        try:
            rating = float(data["rating"])
        except:
            return Response(
                {"error": "Rating must be a decimal value"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            comment = str(data["comment"])
        except:
            return Response(
                {"error": "Must pass a comment when creating rating"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if not Product.objects.filter(id=productId).exists():
                return Response(
                    {"error": "This Product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product = Product.objects.get(id=productId)

            result = {}
            results = []

            if Rating.objects.filter(rater=user, product=product).exists():
                return Response(
                    {"error": "Rating for this product already created"},
                    status=status.HTTP_409_CONFLICT,
                )

            rating = Rating.objects.create(
                rater=user, product=product, rating=rating, comment=comment
            )

            if Rating.objects.filter(rater=user, product=product).exists():
                result["id"] = rating.id
                result["rating"] = rating.rating
                result["comment"] = rating.comment
                result["created_at"] = rating.created_at
                result["rater"] = rating.rater.username

                ratings = Rating.objects.order_by("-created_at").filter(product=product)

                for rating in ratings:
                    item = {}

                    item["id"] = rating.id
                    item["rating"] = rating.rating
                    item["comment"] = rating.comment
                    item["created_at"] = rating.created_at
                    item["rater"] = rating.rater.username

                    results.append(item)

            return Response(
                {"rating": result, "ratings": results}, status=status.HTTP_201_CREATED
            )
        except:
            return Response(
                {"error": "Something went wrong when creating rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateProductRatingView(APIView):
    def put(self, request, productId, format=None):
        user = self.request.user
        data = self.request.data

        try:
            product_id = str(productId)
        except:
            return Response(
                {"error": "Product ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            rating = float(data["rating"])
        except:
            return Response(
                {"error": "Rating must be a decimal value"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            comment = str(data["comment"])
        except:
            return Response(
                {"error": "Must pass a comment when creating rating"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if not Product.objects.filter(id=product_id).exists():
                return Response(
                    {"error": "This product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product = Product.objects.get(id=product_id)

            result = {}
            results = []

            if not Rating.objects.filter(rater=user, product=product).exists():
                return Response(
                    {"error": "Rating for this product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if Rating.objects.filter(rater=user, product=product).exists():
                Rating.objects.filter(rater=user, product=product).update(
                    rating=rating, comment=comment
                )

                rating = Rating.objects.get(rater=user, product=product)

                result["id"] = rating.id
                result["rating"] = rating.rating
                result["comment"] = rating.comment
                result["created_at"] = rating.created_at
                result["rater"] = rating.rater.username

                ratings = Rating.objects.order_by("-created_at").filter(product=product)

                for rating in ratings:
                    item = {}

                    item["id"] = rating.id
                    item["rating"] = rating.rating
                    item["comment"] = rating.comment
                    item["created_at"] = rating.created_at
                    item["rater"] = rating.rater.username

                    results.append(item)

            return Response(
                {"rating": result, "ratings": results}, status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "Something went wrong when updating rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteProductRatingView(APIView):
    def delete(self, request, productId, format=None):
        user = self.request.user

        try:
            product_id = str(productId)
        except:
            return Response(
                {"error": "Product ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            if not Product.objects.filter(id=product_id).exists():
                return Response(
                    {"error": "This product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            product = Product.objects.get(id=product_id)

            results = []

            if Rating.objects.filter(rater=user, product=product).exists():
                Rating.objects.filter(rater=user, product=product).delete()

                ratings = Rating.objects.order_by("-created_at").filter(product=product)

                for rating in ratings:
                    item = {}

                    item["id"] = rating.id
                    item["rating"] = rating.rating
                    item["comment"] = rating.comment
                    item["created_at"] = rating.created_at
                    item["rater"] = rating.rater.username

                    results.append(item)

                return Response({"ratings": results}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Rating for this product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except:
            return Response(
                {"error": "Something went wrong when deleting product rating"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FilterProductRatingsView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, productId, format=None):
        try:
            product_id = str(productId)
        except:
            return Response(
                {"error": "Product ID must be an string"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not Product.objects.filter(id=product_id).exists():
            return Response(
                {"error": "This product does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        product = Product.objects.get(id=product_id)

        rating = request.query_params.get("rating")

        try:
            rating = float(rating)
        except:
            return Response(
                {"error": "Rating must be a decimal value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if not rating:
                rating = 5.0
            elif rating > 5.0:
                rating = 5.0
            elif rating < 0.5:
                rating = 0.5

            results = []

            if Rating.objects.filter(product=product).exists():
                if rating == 0.5:
                    ratings = Rating.objects.order_by("-created_at").filter(
                        rating=rating, product=product
                    )
                else:
                    ratings = (
                        Rating.objects.order_by("-created_at")
                        .filter(rating__lte=rating, product=product)
                        .filter(rating__gte=(rating - 0.5), product=product)
                    )

                for rating in ratings:
                    item = {}

                    item["id"] = rating.id
                    item["rating"] = rating.rating
                    item["comment"] = rating.comment
                    item["created_at"] = rating.created_at
                    item["rater"] = rating.rater.username

                    results.append(item)

            return Response({"ratings": results}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when filtering ratings for product"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
