resource "aws_lambda_layer_version" "main_layer" {
  layer_name               = "ss-keepalive-support"
  filename                 = "${path.module}/aws/resources/main-layer.zip"
  source_code_hash         = filebase64sha256("${path.module}/aws/resources/main-layer.zip")
  compatible_runtimes      = [ "python3.11" ]
  compatible_architectures = [ "x86_64" ]
}
