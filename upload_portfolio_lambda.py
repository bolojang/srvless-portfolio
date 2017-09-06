import io
import zipfile
import mimetypes
import boto3
from botocore.exceptions import ClientError
from botocore.client import Config


def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:eu-west-1:886198463915:deployPortfolioTopic')

    try:
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.francorezabek.info')
        build_bucket = s3.Bucket('portfoliobuild.francorezabek.info')

        portfolio_zip = io.BytesIO()
        build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)

        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        print("Job Done!")
        topic.publish(Subject="Portfolio Deployed", Message="Portfolio Deployed Successfully.")

    except ClientError as error_message:
        topic.publish(Subject="Portfolio Deploy Failed", Message="{}".format(error_message))
        raise

    return 'Hello from Lambda'
