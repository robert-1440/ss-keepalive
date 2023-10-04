resource "aws_scheduler_schedule_group" "notification_group" {
  name = "NotificationGroup"
}

data "aws_iam_policy_document" "notification_group" {
  statement {
    effect    = "Allow"
    resources = [ "${aws_lambda_function.ss_keepalive_service.arn}" ]
    actions   = [
      "lambda:InvokeFunction",
      "lambda:InvokeAsync"
    ]
  }
}

resource "aws_iam_policy" "notification_group" {
  policy = data.aws_iam_policy_document.notification_group.json
}

resource "aws_iam_role" "notification_group" {

  assume_role_policy = jsonencode({
   "Version": "2012-10-17",
   "Statement": [
    {
     "Effect": "Allow",
     "Principal": {
      "Service": "scheduler.amazonaws.com"
     },
     "Action": "sts:AssumeRole"
    }
   ]
  })
}

resource "aws_iam_role_policy_attachment" "notification_group" {
  policy_arn = aws_iam_policy.notification_group.arn
  role       = aws_iam_role.notification_group.name
}
