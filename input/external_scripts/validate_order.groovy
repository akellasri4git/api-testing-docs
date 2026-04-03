def json = new groovy.json.JsonSlurper().parseText(context.response)
assert json.orderId != null
