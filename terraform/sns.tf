resource "aws_sns_topic" "keepalive_error" {
  name         = "ss-keepalive-error"
  display_name = "Topic for errors encountered by the keepalive service."

}
