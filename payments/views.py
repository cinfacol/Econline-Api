from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cart.models import Cart, CartItem
from coupons.models import FixedPriceCoupon, PercentageCoupon
from orders.models import Order, OrderItem
from inventory.models import Inventory
from shipping.models import Shipping
from django.core.mail import send_mail
import braintree

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=settings.BT_ENVIRONMENT,
        merchant_id=settings.BT_MERCHANT_ID,
        public_key=settings.BT_PUBLIC_KEY,
        private_key=settings.BT_PRIVATE_KEY,
    )
)


class GenerateTokenView(APIView):
    def get(self, request, format=None):
        try:
            token = gateway.client_token.generate()

            return Response({"braintree_token": token}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "Something went wrong when retrieving braintree token"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetPaymentTotalView(APIView):
    def get(self, request, format=None):
        user = self.request.user

        tax = str(request.query_params.get("taxe", ""))
        shipping_id = str(request.query_params.get("shipping_id", ""))
        coupon_name = str(request.query_params.get("coupon_name", ""))

        try:
            cart = Cart.objects.prefetch_related(
                "cartitem_set__inventory__inventory_stock"
            ).get(user=user)

            if not cart.cartitem_set.exists():
                return Response(
                    {"error": "Need to have items in cart"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            def calculate_totals(cart_items):
                total_amount = 0.0
                total_compare_amount = 0.0
                total_tax = 0.0

                for item in cart_items:
                    # Convertir valores a float
                    store_price = float(str(item.inventory.store_price))
                    retail_price = float(str(item.inventory.retail_price))
                    quantity = float(item.quantity)
                    tax_rate = float(str(item.inventory.taxe))

                    # Calcular subtotal por item
                    item_subtotal = store_price * quantity

                    # Calcular impuesto por item
                    item_tax = round(item_subtotal * tax_rate, 2)

                    total_amount += item_subtotal
                    total_compare_amount += retail_price * quantity
                    total_tax += item_tax

                return (
                    round(total_amount, 2),
                    round(total_compare_amount, 2),
                    round(total_tax, 2),
                )

            # Validar inventario
            for item in cart.cartitem_set.all():
                available_stock = int(item.inventory.inventory_stock.units) - int(
                    item.inventory.inventory_stock.units_sold
                )
                if int(item.quantity) > available_stock:
                    return Response(
                        {"error": f"Not enough stock for product {item.inventory.id}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            total_amount, total_compare_amount, estimated_tax = calculate_totals(
                cart.cartitem_set.all()
            )
            original_price = total_amount

            # Agregar impuestos al total
            total_amount += estimated_tax

            # Agregar shipping si está habilitado
            shipping_cost = 0.0

            if shipping_id:
                try:
                    shipping = Shipping.objects.get(id=shipping_id)
                    shipping_cost = float(str(shipping.price))
                    total_amount += shipping_cost
                except Shipping.DoesNotExist:
                    pass

            return Response(
                {
                    "original_price": f"{original_price:.2f}",
                    "total_amount": f"{total_amount:.2f}",
                    "total_compare_amount": f"{total_compare_amount:.2f}",
                    "estimated_tax": f"{estimated_tax:.2f}",
                    "shipping_cost": f"{shipping_cost:.2f}",
                },
                status=status.HTTP_200_OK,
            )

        except Cart.DoesNotExist:
            return Response(
                {"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error processing payment total: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProcessPaymentView(APIView):
    def post(self, request, format=None):
        user = self.request.user
        data = self.request.data
        # print("data =", data) # card data

        tax = 19 / 100

        nonce = data["nonce"]
        shipping_id = str(data["shipping_id"])
        coupon_name = str(data["coupon_name"])

        full_name = data["full_name"]
        address_line_1 = data["address_line_1"]
        address_line_2 = data["address_line_2"]
        city = data["city"]
        state_province_region = data["state_province_region"]
        postal_zip_code = data["postal_zip_code"]
        country_region = data["country_region"]
        telephone_number = data["telephone_number"]

        # revisar si datos de shipping son validos
        if not Shipping.objects.filter(id__iexact=shipping_id).exists():
            return Response(
                {"error": "Invalid shipping option"}, status=status.HTTP_404_NOT_FOUND
            )

        cart = Cart.objects.get(user=user)

        # revisar si usuario tiene items en carrito
        if not CartItem.objects.filter(cart=cart).exists():
            return Response(
                {"error": "Need to have items in cart"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart_items = CartItem.objects.filter(cart=cart)

        # revisar si hay stock
        for cart_item in cart_items:
            if not Inventory.objects.filter(id=cart_item.inventory.id).exists():
                return Response(
                    {"error": "Transaction failed, a proudct ID does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if int(cart_item.quantity) > int(
                cart_item.inventory.inventory_stock.units
                - cart_item.inventory.inventory_stock.units_sold
            ):
                return Response(
                    {"error": "Not enough items in stock"}, status=status.HTTP_200_OK
                )

        total_amount = 0.0

        for cart_item in cart_items:
            total_amount += float(cart_item.inventory.retail_price) * float(
                cart_item.quantity
            )

        # Cupones
        if coupon_name != "":
            if FixedPriceCoupon.objects.filter(name__iexact=coupon_name).exists():
                fixed_price_coupon = FixedPriceCoupon.objects.get(name=coupon_name)
                discount_amount = float(fixed_price_coupon.discount_price)

                if discount_amount < total_amount:
                    total_amount -= discount_amount

            elif PercentageCoupon.objects.filter(name__iexact=coupon_name).exists():
                percentage_coupon = PercentageCoupon.objects.get(name=coupon_name)
                discount_percentage = float(percentage_coupon.discount_percentage)

                if discount_percentage > 1 and discount_percentage < 100:
                    total_amount -= total_amount * (discount_percentage / 100)

        total_amount += total_amount * tax

        shipping = Shipping.objects.get(id=str(shipping_id))

        shipping_name = shipping.name
        shipping_time = shipping.time_to_delivery
        shipping_price = shipping.price

        total_amount += float(shipping_price)
        total_amount = round(total_amount, 2)

        try:
            # Crear transaccion con braintree
            newTransaction = gateway.transaction.sale(
                {
                    "amount": str(total_amount),
                    "payment_method_nonce": str(nonce["nonce"]),
                    "options": {"submit_for_settlement": True},
                }
            )
        except:
            return Response(
                {"error": "Error processing the transaction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if newTransaction.is_success or newTransaction.transaction:
            for cart_item in cart_items:
                update_product = Inventory.objects.get(id=cart_item.inventory.id)

                # encontrar cantidad despues de compra
                quantity = int(update_product.inventory_stock.units) - int(
                    cart_item.quantity
                )

                # obtener cantidad de producto por vender
                sold = int(update_product.inventory_stock.units_sold) + int(
                    cart_item.quantity
                )

                # actualizar el stock
                """ Inventory.objects.filter(id=cart_item.inventory.id).update(
                    units=update_product.inventory_stock.units,
                    unitsSold=update_product.inventory_stock.units_sold,
                    units=quantity,
                    unitsSold=sold,
                ) """
                inventario = Inventory.objects.filter(id=cart_item.inventory.id)
                inventario.inventory_stock.update(units=quantity, units_sold=sold)

            # crear orden
            try:
                order = Order.objects.create(
                    user=user,
                    transaction_id=newTransaction.transaction.id,
                    amount=total_amount,
                    full_name=full_name,
                    address_line_1=address_line_1,
                    address_line_2=address_line_2,
                    city=city,
                    state_province_region=state_province_region,
                    postal_zip_code=postal_zip_code,
                    country_region=country_region,
                    telephone_number=telephone_number,
                    shipping_name=shipping_name,
                    shipping_time=shipping_time,
                    shipping_price=float(shipping_price),
                )
            except:
                return Response(
                    {"error": "Transaction succeeded but failed to create the order"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            for cart_item in cart_items:
                try:
                    # agarrar el producto
                    inventory = Inventory.objects.get(id=cart_item.inventory.id)

                    OrderItem.objects.create(
                        inventory=inventory,
                        order=order,
                        name=inventory.product.name,
                        price=cart_item.inventory.retail_price,
                        count=cart_item.quantity,
                    )
                except:
                    return Response(
                        {
                            "error": "Transaction succeeded and order created, but failed to create an order item"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            try:
                send_mail(
                    "Your Order Details",
                    "Hey "
                    + full_name
                    + ","
                    + "\n\nWe recieved your order!"
                    + "\n\nGive us some time to process your order and ship it out to you."
                    + "\n\nYou can go on your user dashboard to check the status of your order."
                    + "\n\nSincerely,"
                    + "\nShop Time",
                    "mail@virtualeline.com",
                    [user.email],
                    fail_silently=False,
                )
            except:
                return Response(
                    {
                        "error": "Transaction succeeded and order created, but failed to send email"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                # Vaciar carrito de compras
                CartItem.objects.filter(cart=cart).delete()

                # Actualizar carrito
                Cart.objects.filter(user=user).update(total_items=0)
            except:
                return Response(
                    {
                        "error": "Transaction succeeded and order successful, but failed to clear cart"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"success": "Transaction successful and order was created"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"error": "Transaction failed"}, status=status.HTTP_400_BAD_REQUEST
            )
