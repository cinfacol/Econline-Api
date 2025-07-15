# Corrección del Límite de Descuento en Cupones de Porcentaje

## Problema Identificado

Los cupones de porcentaje con límite máximo de descuento (ej: 25% con máximo $35 USD) no respetaban el límite cuando se integraban con Stripe. El sistema enviaba el porcentaje completo a Stripe sin aplicar el límite máximo.

## Solución Implementada

### Cambios en `payments/views.py`

**Antes:**
```python
if coupon.percentage_coupon:
    stripe_coupon = stripe.Coupon.create(
        name=coupon.code,
        percent_off=float(coupon.percentage_coupon.discount_percentage),
        duration="once",
    )
```

**Después:**
```python
if coupon.percentage_coupon:
    # Calcular el subtotal real de los productos (sin envío)
    subtotal = Decimal('0')
    for item in order.orderitem_set.all():
        subtotal += Decimal(str(item.price)) * Decimal(str(item.count))
    
    # Calcular el descuento real aplicando el límite máximo
    percentage_discount = (subtotal * coupon.percentage_coupon.discount_percentage) / 100
    
    # Aplicar límite máximo de descuento si está configurado
    if coupon.max_discount_amount:
        actual_discount = min(percentage_discount, coupon.max_discount_amount)
        logger.info(f"Subtotal: {subtotal}, descuento calculado: {percentage_discount}, límite: {coupon.max_discount_amount}, descuento final: {actual_discount}")
    else:
        actual_discount = percentage_discount
        logger.info(f"Subtotal: {subtotal}, descuento calculado sin límite: {actual_discount}")
    
    # Crear cupón de monto fijo en Stripe con el descuento calculado
    stripe_coupon = stripe.Coupon.create(
        name=coupon.code,
        amount_off=int(float(actual_discount) * 100),  # Convertir a centavos
        currency=order.currency.lower(),
        duration="once",
    )
```

## Mejoras Implementadas

1. **Cálculo correcto del subtotal**: Se calcula el subtotal real de los productos sin incluir el envío
2. **Aplicación del límite máximo**: Se aplica el límite `max_discount_amount` antes de crear el cupón de Stripe
3. **Cupón de monto fijo**: En lugar de usar `percent_off`, se usa `amount_off` con el descuento calculado
4. **Logging mejorado**: Se registra información detallada del cálculo para debugging

## Casos de Prueba

### Caso 1: Subtotal alto ($1000) con 25% y límite $35
- Descuento sin límite: $250
- Descuento aplicado: $35 ✅
- Límite respetado: ✅

### Caso 2: Subtotal bajo ($100) con 25% y límite $35
- Descuento sin límite: $25
- Descuento aplicado: $25 ✅
- Descuento completo aplicado: ✅

### Caso 3: Subtotal medio ($200) con 25% y límite $35
- Descuento sin límite: $50
- Descuento aplicado: $35 ✅
- Límite respetado: ✅

## Comandos de Prueba

```bash
# Prueba con valores por defecto
docker compose exec api python manage.py test_coupon_limit

# Prueba con subtotal bajo
docker compose exec api python manage.py test_coupon_limit --subtotal 100 --percentage 25 --max-discount 35

# Prueba con subtotal alto
docker compose exec api python manage.py test_coupon_limit --subtotal 1000 --percentage 25 --max-discount 35
```

## Resultado

✅ **Problema resuelto**: Los cupones de porcentaje ahora respetan correctamente el límite máximo de descuento cuando se integran con Stripe.

✅ **Compatibilidad mantenida**: Los cupones de monto fijo siguen funcionando igual.

✅ **Logging mejorado**: Se registra información detallada para facilitar el debugging.

## Archivos Modificados

- `payments/views.py`: Lógica principal de corrección
- `payments/management/commands/test_coupon_limit.py`: Comando de prueba
- `payments/test_coupon_limit.py`: Script de prueba independiente

## Notas Importantes

1. **Cupones existentes**: Los cupones ya creados en Stripe seguirán funcionando, pero los nuevos respetarán el límite.
2. **Moneda**: El código asume USD, pero es configurable a través de `order.currency`.
3. **Precisión**: Se usa `Decimal` para evitar problemas de precisión en cálculos monetarios. 