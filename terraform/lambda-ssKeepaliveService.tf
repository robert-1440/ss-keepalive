data "aws_iam_policy_document" "ss_keepalive_service" {
  statement {
    effect    = "Allow"
    resources = [ "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/ssKeepaliveService:*" ]
    actions   = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
  }

  statement {
    effect    = "Allow"
    resources = [ aws_sns_topic.keepalive_error.arn ]
    actions   = [ "sns:Publish" ]
  }

  statement {
    effect    = "Allow"
    resources = [ aws_dynamodb_table.s_s_keepalive_session.arn ]
    actions   = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem"
    ]
  }

  statement {
    effect    = "Allow"
    resources = [ "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:ss-keepalive/*" ]
    actions   = [ "secretsmanager:GetSecretValue" ]
  }
}

resource "aws_iam_policy" "ss_keepalive_service" {
  policy = data.aws_iam_policy_document.ss_keepalive_service.json
}

resource "aws_iam_role" "ss_keepalive_service" {
  name = "lambda-ssKeepaliveService"

  assume_role_policy = jsonencode({
   "Version": "2012-10-17",
   "Statement": [
    {
     "Effect": "Allow",
     "Principal": {
      "Service": "lambda.amazonaws.com"
     },
     "Action": "sts:AssumeRole"
    }
   ]
  })
}

resource "aws_iam_role_policy_attachment" "ss_keepalive_service" {
  policy_arn = aws_iam_policy.ss_keepalive_service.arn
  role       = aws_iam_role.ss_keepalive_service.name
}

resource "aws_lambda_function" "ss_keepalive_service" {
  function_name    = "ssKeepaliveService"
  description      = "Social Studio Keepalive Service"
  handler          = "app.handler"
  timeout          = 90
  memory_size      = var.lambda_memory_size
  filename         = "${path.module}/aws/resources/ssKeepaliveService.zip"
  source_code_hash = filebase64sha256("${path.module}/aws/resources/ssKeepaliveService.zip")
  layers           = [ aws_lambda_layer_version.main_layer.arn ]
  runtime          = "python3.11"
  role             = aws_iam_role.ss_keepalive_service.arn

  environment {
    variables = {
      SS_KEEPALIVE_SCHEDULE_GROUP          = "NotificationGroup"
      SS_KEEPALIVE_SCHEDULE_GROUP_ROLE_ARN = "${aws_iam_role.notification_group.arn}"
      SS_KEEPALIVE_ERROR_TOPIC_ARN         = "${aws_sns_topic.keepalive_error.arn}"
    }
  }
  depends_on = [ aws_iam_role_policy_attachment.ss_keepalive_service ]
}

resource "aws_cloudwatch_log_group" "ss_keepalive_service" {
  name              = "/aws/lambda/${aws_lambda_function.ss_keepalive_service.function_name}"
  retention_in_days = 30
}
