from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kinesisfirehose as firehose
from aws_cdk import aws_s3 as s3
from aws_cdk import core

from common.parameters import string_parameter


class KinesisStack(core.Stack):

    def __init__(self,
                 scope: core.Construct,
                 id: str,
                 circleci_execution_role: iam.Role,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        identity_pool = cognito.CfnIdentityPool(
            self,
            'pinpoint_integ_test_android',
            allow_unauthenticated_identities=True)

        unauthenticated_role = iam.Role(
            self,
            'CognitoDefaultUnauthenticatedRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                {
                    'StringEquals': {
                        'cognito-identity.amazonaws.com:aud': identity_pool.ref
                    },
                    'ForAnyValue:StringLike': {
                        'cognito-identity.amazonaws.com:amr': 'unauthenticated'
                    },
                },
                'sts:AssumeRoleWithWebIdentity'
            )
        )
        unauthenticated_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'cognito-sync:*',
                'kinesis:*',
                'firehose:*'
            ],
            resources=['*']
        ))
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            'DefaultValid',
            identity_pool_id=identity_pool.ref,
            roles={
                'unauthenticated': unauthenticated_role.role_arn
            }
        )

        firehose_s3_role = iam.Role(
            self,
            'FirehoseS3Role',
            assumed_by=iam.ServicePrincipal(
                'firehose.amazonaws.com'))
        firehose_s3_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                's3:AbortMultipartUpload',
                's3:GetBucketLocation',
                's3:GetObject',
                's3:ListBucket',
                's3:ListBucketMultipartUploads',
                's3:PutObject'
            ],
            resources=['*']
        ))

        ingest_bucket = s3.Bucket(self, 'test-aws-android-sdk-firehose-bucket')
        s3_dest_config = firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
            bucket_arn=ingest_bucket.bucket_arn,
            buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                interval_in_seconds=60,
                size_in_m_bs=5),
            compression_format='UNCOMPRESSED',
            role_arn=firehose_s3_role.role_arn)

        firehose_test = firehose.CfnDeliveryStream(
            self,
            'kinesis_firehose_recorder_test',
            s3_destination_configuration=s3_dest_config)

        string_parameter(self, 'firehose_name', firehose_test.ref)
        string_parameter(self, 'identity_pool_id', identity_pool.ref)

        circleci_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["kinesis:*"], resources=["*"]))
