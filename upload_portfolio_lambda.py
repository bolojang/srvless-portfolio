import io
import zipfile
import mimetypes
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config


def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-1:886198463915:deployPortfolioTopic')

    location = {
        "bucketName": 'portfoliobuild.francorezabek.info',
        "objectKey": 'portfoliobuild.zip'
    }
    try:
        job = event.get("CodePipeline.job")

        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]
        print("Building portfolio from " + str(location))

        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.francorezabek.info')
        build_bucket = s3.Bucket(location["bucketName"])

        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print("Job Done!")
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio Deployed Successfully.")
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])

    except ClientError as error_message:
        topic.publish(Subject="Portfolio Deploy Failed", Message="{}".format(error_message))
        raise

    return 'Hello from Lambda'
    
