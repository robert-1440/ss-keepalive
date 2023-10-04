resource "aws_dynamodb_table" "s_s_keepalive_session" {
  name         = "SSKeepaliveSession"
  hash_key     = "sessionId"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "sessionId"
    type = "S"
  }

  ttl {
    attribute_name = "expireTime"
    enabled        = true
  }

}
