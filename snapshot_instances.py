import ec2_enumerate
import json
import boto3
from datetime import datetime

def retrieve_volumes(instance):
    pass

def read_region_from_json(region):
    with open("ec2.json") as ec2_json:
        full_region_dict = json.load(ec2_json)
    #return full_region_dict
    for list_region in full_region_dict:
        if list_region['Region'] == region:
            return (list_region['Instances'], list_region['Region'])


def get_instances_from_region(regiondict):
    vol_list = []
    for instance in regiondict['Instances']:
        if instance == 'NID':
            return False
        else:
            vol_list.append((instance['Name'], instance['ID'], instance['Volumes']))
    return vol_list

def make_snapshots(ec2, instance):
    timestamp = datetime.now()
    for volume in list(instance['Volumes']):
        created_data = "Instance: {} ID: {} Vol: {}".format(instance['Name'], instance['ID'], volume)
        description = "Transition Snapshot"
        created_time = "{}".format(timestamp)
        snap_tags = [{
                        'Key'   : 'Name',
                        'Value' : created_data
                    },
                    {
                        'Key'   : 'CreatedAt',
                        'Value' : created_time
                    },
                    ]
        snapshot = ec2.create_snapshot(VolumeId=volume, Description=description)
        snapshot.create_tags(Resources=[snapshot.id], Tags=snap_tags)
        print "Snapshot {} for instance {} created {}".format(snapshot.id, instance['Name'], timestamp)
        

def create_ami_from_snapshots(ec2,snapshot_id,instance):
    pass

if __name__ == "__main__":
# TEST CODE
    #get an ec2 object
    ec2 = ec2_enumerate.init_ec2('eu-west-1')
    instances, region = read_region_from_json('eu-west-1')
    if instances:
        for instance in instances:
            make_snapshots(ec2, instance)


