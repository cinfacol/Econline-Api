from django.conf import settings
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from products.models import Product
from .serializers import UpdateProductReviewSerializer

from .models import Review

User = settings.AUTH_USER_MODEL


# todos los reviews de un producto
class GetProductReviewsView(APIView):
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

            if Review.objects.filter(product=product).exists():
                reviews = Review.objects.order_by("-created_at").filter(product=product)

                for review in reviews:
                    item = {}

                    item["id"] = review.id
                    item["rating"] = review.rating
                    item["comment"] = review.comment
                    item["created_at"] = review.created_at
                    item["rater"] = review.rater.username

                    results.append(item)

            return Response({"reviews": results}, status=status.HTTP_200_OK)

        except:
            return Response(
                {"error": "Something went wrong when retrieving reviews"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# una review (review) en particular de un producto
class GetProductReviewView(APIView):
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

            if Review.objects.filter(rater=user, product=product).exists():
                review = Review.objects.get(rater=user, product=product)

                result["id"] = review.id
                result["rating"] = review.rating
                result["comment"] = review.comment
                result["created_at"] = review.created_at
                result["rater"] = review.rater.username

            return Response({"review": result}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when retrieving review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateProductReviewView(APIView):
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
                {"error": "Must pass a comment when creating review"},
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

            if Review.objects.filter(rater=user, product=product).exists():
                return Response(
                    {"error": "Review for this product already created"},
                    status=status.HTTP_409_CONFLICT,
                )

            review = Review.objects.create(
                rater=user, product=product, rating=rating, comment=comment
            )

            if Review.objects.filter(rater=user, product=product).exists():
                result["id"] = review.id
                result["rating"] = review.rating
                result["comment"] = review.comment
                result["created_at"] = review.created_at
                result["rater"] = review.rater.username

                reviews = Review.objects.order_by("-created_at").filter(product=product)

                for review in reviews:
                    item = {}

                    item["id"] = review.id
                    item["rating"] = review.rating
                    item["comment"] = review.comment
                    item["created_at"] = review.created_at
                    item["rater"] = review.rater.username

                    results.append(item)

            return Response(
                {"review": result, "reviews": results}, status=status.HTTP_201_CREATED
            )
        except:
            return Response(
                {"error": "Something went wrong when creating review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UpdateProductReviewView(APIView):
    @extend_schema(responses=UpdateProductReviewSerializer)
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
            review = float(data["review"])
        except:
            return Response(
                {"error": "Review must be a decimal value"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            comment = str(data["comment"])
        except:
            return Response(
                {"error": "Must pass a comment when creating review"},
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

            if not Review.objects.filter(rater=user, product=product).exists():
                return Response(
                    {"error": "Review for this product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if Review.objects.filter(rater=user, product=product).exists():
                Review.objects.filter(rater=user, product=product).update(
                    review=review, comment=comment
                )

                review = Review.objects.get(rater=user, product=product)

                result["id"] = review.id
                result["rating"] = review.rating
                result["comment"] = review.comment
                result["created_at"] = review.created_at
                result["rater"] = review.rater.username

                reviews = Review.objects.order_by("-created_at").filter(product=product)

                for review in reviews:
                    item = {}

                    item["id"] = review.id
                    item["rating"] = review.rating
                    item["comment"] = review.comment
                    item["created_at"] = review.created_at
                    item["rater"] = review.rater.username

                    results.append(item)

            return Response(
                {"review": result, "reviews": results}, status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "Something went wrong when upating review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteProductReviewView(APIView):
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

            if Review.objects.filter(rater=user, product=product).exists():
                Review.objects.filter(rater=user, product=product).delete()

                reviews = Review.objects.order_by("-created_at").filter(product=product)

                for review in reviews:
                    item = {}

                    item["id"] = review.id
                    item["rating"] = review.rating
                    item["comment"] = review.comment
                    item["created_at"] = review.created_at
                    item["rater"] = review.rater.username

                    results.append(item)

                return Response({"reviews": results}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "Review for this product does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except:
            return Response(
                {"error": "Something went wrong when deleting product review"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FilterProductReviewsView(APIView):
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

        review = request.query_params.get("review")

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

            if Review.objects.filter(product=product).exists():
                if rating == 0.5:
                    reviews = Review.objects.order_by("-created_at").filter(
                        rating=rating, product=product
                    )
                else:
                    reviews = (
                        Review.objects.order_by("-created_at")
                        .filter(rating__lte=rating, product=product)
                        .filter(rating__gte=(rating - 0.5), product=product)
                    )

                for review in reviews:
                    item = {}

                    item["id"] = review.id
                    item["rating"] = review.rating
                    item["comment"] = review.comment
                    item["created_at"] = review.created_at
                    item["rater"] = review.rater.username

                    results.append(item)

            return Response({"reviews": results}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when filtering reviews for product"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
