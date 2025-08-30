#!/usr/bin/env python3
import os
import aws_cdk as cdk
from nfse_stack import NfseStack

app = cdk.App()
NfseStack(app, "NfseStack",
          env=cdk.Environment(
            account=os.getenv("CDK_DEFAULT_ACCOUNT"),
            region=os.getenv("CDK_DEFAULT_REGION", "us-east-1")
          ))
app.synth()
