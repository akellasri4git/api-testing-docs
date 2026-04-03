// External Groovy Script: Order Validation
// Purpose: Validate order response structure and business rules

import groovy.json.JsonSlurper

def responseContent = context.expand('${Create Order#Response}')
def jsonSlurper = new JsonSlurper()
def response = jsonSlurper.parseText(responseContent)

// Validate order structure
assert response.orderId != null, "Order ID must be present"
assert response.status == "PENDING", "New order status must be PENDING"
assert response.totalAmount > 0, "Order total amount must be positive"

// Validate items array
assert response.items != null && response.items.size() > 0, "Order must contain at least one item"

response.items.each { item ->
    assert item.productId != null, "Each item must have a product ID"
    assert item.quantity > 0, "Item quantity must be positive"
    assert item.price > 0, "Item price must be positive"
}

// Validate customer information
assert response.customerId != null, "Customer ID must be present"
assert response.shippingAddress != null, "Shipping address is required"

// Business rule: Total amount should match sum of (item.price * item.quantity)
def calculatedTotal = response.items.sum { it.price * it.quantity }
assert Math.abs(response.totalAmount - calculatedTotal) < 0.01,
    "Total amount mismatch: expected ${calculatedTotal}, got ${response.totalAmount}"

log.info("Order validation passed: Order ID ${response.orderId}")
return true
