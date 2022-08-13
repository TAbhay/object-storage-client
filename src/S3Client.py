#!/bin/python
#
#   AWS S3 Client
#   API Reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html
#

import boto3

from .ObjectStorageClient import *

class S3Client(ObjectStorageClient):
    
    def __init__(self, location):
        self.client = boto3.client('s3')
        self.location = location
    
    # Container related actions
    
    def container_create(self, container_name: str) -> bool:
        """
        Create a new container. This request might take few seconds to complete.

        @param `container_name` The new container name
        @return True on success, False on failure (ex: already exists)
        """
        try:
            res = self.client.create_bucket(Bucket=container_name, CreateBucketConfiguration={ "LocationConstraint": self.location })
            print(res)
            return True
        except:
            return False

    def container_list(self, prefix: str = None) -> list[ContainerInfo]:
        buckets = self.client.list_buckets().get('Buckets', [])
        return [ ContainerInfo(b['Name'], None, None) for b in buckets ]

    def container_delete(self, container_name: str, force: bool = False) -> bool:
        """
        Delete a container. It will not delete a container that contain objects unless `force`
        is set to True.

        @param `force` Set to True to delete a container even if it is not empty.
        @return True if the container was deleted or does not exist
        """
        try:
            res = self.client.delete_bucket(Bucket=container_name)
            return True
        except:
            return False

    def container_info(self, container_name: str) -> ContainerInfo:
        """
        Fetch container information

        @return ContainerInfo or None if the container does not exist
        """
        result = self.client.head_bucket(Bucket=container_name)

        if result.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            return ContainerInfo(container_name, None, None)
        
        return None

    # Object related actions

    def object_info(self, object_name: str) -> ObjectInfo:
        res = self.client.head_object(Bucket=self.container_name, Key=object_name)
        if res.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            return ObjectInfo(
                name=object_name,
                bytes=res.get('ContentLength'),
                content_type=res.get('ContentType'),
                hash=res.get('ETag').replace('"',''),
                metadata=res.get('Metadata')
            )
        else:
            return None

    def object_replace_metadata(self, object_name: str, meta: dict={}) -> bool:
        res = self.client.copy_object(
            Bucket=self.container_name,
            Key=object_name,
            CopySource={'Bucket':self.container_name, 'Key': object_name},
            Metadata=meta,
            MetadataDirective='REPLACE'
        )

        return res.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200


    def object_set_metadata(self, object_name: str, key: str, value: str) -> bool:
        """Sets a single metadata key-value pair on the specified object"""
        raise NotImplementedError

    def object_delete_metadata(self, object_name: str, key: str) -> dict:
        """Delete a single metadata key-value for the specified object"""
        raise NotImplementedError

    def object_upload(self, stream, object_name: str, meta: dict={}) -> bool:
        """Upload a stream, optionally specifying some metadata to apply to the object"""
        raise NotImplementedError

    def object_download(self, object_name: str, stream) -> bool:
        """ 
        Download an object and write to the output stream
        """
        raise NotImplementedError

    def object_list(self,
        fetch_metadata: bool = False,
        prefix: str = None,
        delimiter: str = None,
        container_name: str = None,
    ) -> list[ObjectInfo|SubdirInfo]:
        
        if container_name is None:
            container_name = self.container_name

        args = {"Bucket": container_name}
        if prefix: args['Prefix'] = prefix
        if delimiter: args['Delimiter'] = delimiter

        res = self.client.list_objects_v2(**args)

        if res.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            objects =  [ObjectInfo(o['Key'], o['Size'], o['ETag'], None, None) for o in res.get('Contents', [])]
            subdirs =  [SubdirInfo(o['Prefix']) for o in res.get('CommonPrefixes', [])]
            if fetch_metadata:
                for i in range(0, len(objects)):
                    objects[i] = self.object_info(objects[i].name)
            objects.extend(subdirs)
            return objects
        else:
            return []

    def object_delete(self, object_name: str, container_name: str = None) -> bool:
        """Delete the specified object"""
        raise NotImplementedError


    

if __name__ == "__main__":

    client = S3Client('us-west-2')

    client.use_container("firmware-autonom")
    print(client.object_list(delimiter='6', fetch_metadata=True))
    # client.object_info("test.txt")

    # client.container_create('universal-object-storage-client-test-container-1231321321312')
    # client.container_delete('universal-object-storage-client-test-container-1231321321312')
