from typing import Any
from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_cognito as cognito,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
)
from constructs import Construct
import os


class NfseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- S3 for Admin Site (static) ---
        admin_bucket = s3.Bucket(
            self,
            "AdminSiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        oai = cloudfront.OriginAccessIdentity(self, "OAI")
        admin_bucket.grant_read(oai)

        distribution = cloudfront.Distribution(
            self,
            "AdminSiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(admin_bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            default_root_object="index.html",
        )

        # --- Docs bucket (XML/PDF) ---
        docs_bucket = s3.Bucket(
            self,
            "DocsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --- Cognito User Pool for API auth ---
        user_pool = cognito.UserPool(
            self,
            "Users",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=False,
                require_digits=True,
                require_symbols=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        user_pool_client = cognito.UserPoolClient(
            self, "UsersClient", user_pool=user_pool, generate_secret=False
        )

        # --- DynamoDB tables ---
        invoices = dynamodb.Table(
            self,
            "InvoicesTable",
            partition_key=dynamodb.Attribute(
                name="invoiceId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        requests = dynamodb.Table(
            self,
            "RequestsTable",
            partition_key=dynamodb.Attribute(
                name="requestId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --- Lambda functions (Python 3.12) ---
        runtime = _lambda.Runtime.PYTHON_3_12
        common_env = {
            "TABLE_INVOICES": invoices.table_name,
            "TABLE_REQUESTS": requests.table_name,
            "BUCKET_DOCS": docs_bucket.bucket_name,
        }

        emit_fn = _lambda.Function(
            self,
            "EmitFn",
            runtime=runtime,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "lambdas/emit")
            ),
            environment=common_env,
            timeout=Duration.seconds(10),
        )
        get_fn = _lambda.Function(
            self,
            "GetFn",
            runtime=runtime,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "lambdas/consult")
            ),
            environment=common_env,
            timeout=Duration.seconds(10),
        )
        cancel_fn = _lambda.Function(
            self,
            "CancelFn",
            runtime=runtime,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "lambdas/cancel")
            ),
            environment=common_env,
            timeout=Duration.seconds(10),
        )
        ping_fn = _lambda.Function(
            self,
            "PingFn",
            runtime=runtime,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(os.path.dirname(__file__), "lambdas/ping")
            ),
            timeout=Duration.seconds(5),
        )

        invoices.grant_read_write_data(emit_fn)
        invoices.grant_read_data(get_fn)
        invoices.grant_read_write_data(cancel_fn)
        requests.grant_read_write_data(emit_fn)
        docs_bucket.grant_read_write(emit_fn)

        # --- API Gateway (REST) ---
        api = apigateway.RestApi(
            self,
            "NfseApi",
            rest_api_name="nfse-api",
            deploy_options=apigateway.StageOptions(stage_name="dev"),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Requested-With",
                    "X-Idempotency-Key",
                ],
            ),
        )

        # Cognito authorizer (protect business routes)
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self, "CognitoAuthorizer", cognito_user_pools=[user_pool]
        )

        # /public/ping (no auth)
        public_res = api.root.add_resource("public")
        ping_res = public_res.add_resource("ping")
        ping_res.add_method("GET", apigateway.LambdaIntegration(ping_fn))

        # /invoices (protected)
        invoices_res = api.root.add_resource("invoices")
        invoices_res.add_method(
            "POST",
            apigateway.LambdaIntegration(emit_fn),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # /invoices/{id} GET (protected)
        invoice_id_res = invoices_res.add_resource("{id}")
        invoice_id_res.add_method(
            "GET",
            apigateway.LambdaIntegration(get_fn),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # /invoices/{id}/cancel POST (protected)
        cancel_res = invoice_id_res.add_resource("cancel")
        cancel_res.add_method(
            "POST",
            apigateway.LambdaIntegration(cancel_fn),
            authorizer=authorizer,
            authorization_type=apigateway.AuthorizationType.COGNITO,
        )

        # Outputs
        CfnOutput(self, "AdminBucketName", value=admin_bucket.bucket_name)
        CfnOutput(
            self, "AdminDistributionDomain", value=distribution.distribution_domain_name
        )
        CfnOutput(self, "DocsBucketName", value=docs_bucket.bucket_name)
        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
