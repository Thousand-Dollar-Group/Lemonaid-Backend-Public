import boto3

s3 = boto3.client(
    's3',
    region_name='us-west-1'
)

def get_presigned_url(method: str, bucket_name: str, key: str, expiration: int = 3600, ContentType=None) -> str:

    params={
        'Bucket': bucket_name,
        'Key': key,
    }

    if(method=='get_object'):
        params['ResponseContentType']=ContentType
    elif(method=='put_object'):
        params['ContentType']=ContentType

    else:
        raise HTTPException(status_code=500, detail="Content Type Error")
    
    url = s3.generate_presigned_url(
        method,
        Params=params,
        ExpiresIn=expiration
    )
    return url
    