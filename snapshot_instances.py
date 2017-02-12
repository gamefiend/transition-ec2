import ec2_enumerate
import json
import boto3
import os
import argparse
from datetime import datetime

def record_complete(region, resource, resource_type):
    fname = "{}-{}.txt".format(region, resource_type)
    with open (fname, 'a+') as f:
        msg = "{}\n".format(resource)
        f.write(msg)

def is_complete(region,search,resource_type):
    fname = "{}-{}.txt".format(region, resource_type)
    if os.path.exists(fname):
        if search in open(fname, 'r').read():
            return True
        else:
            return False
    else:
        return False

def retrieve_volumes(instance):
    pass

def read_region_from_json(region):
    with open("ec2.json") as ec2_json:
        full_region_dict = json.load(ec2_json)
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

def get_instance_snapshot_from_ami(ec2, ami_id):
    ami_filter = ec2.describe_images(ImageIds=[ami_id])
    ami_instance_name = ami_filter['Images'][0]['Name'].split('  SNAPSHOT')[0].split('TRANSFER-')[1]
    ami_snapshot_id = ami_filter['Images'][0]['Name'].split('SNAPSHOT-')[1]
    return (ami_instance_name, ami_snapshot_id)

def get_snapshot_instance_name(ec2, snapshot_id):
    snapshot_filter = ec2.describe_snapshots(SnapshotIds=[snapshot_id])
    for snap in snapshot_filter['Snapshots']:
        for t in snap['Tags']:
            if t['Key'] == 'Name':
                first_split = t['Value'].split('ID')
                return str(first_split[0].split(': ')[1])

def get_ami_id_from_snapshot(ec2, snapshot_id):
    search_snapshot = "*SNAPSHOT-{}*".format(snapshot_id)
    ami_filter =  ec2.describe_images(Owners=[old_acct],Filters=[{'Name': 'name', 'Values': [search_snapshot]}])
    return ami_filter['Images'][0]['ImageId']
   

def make_snapshots(ec2, instances, region):
    timestamp = datetime.now()
    create_snapshot_file = "snapshots"
    snapshot_list = []
    for instance in instances:
        if not is_complete(region,instance['ID'],create_snapshot_file): 
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
                record_complete(region,instance['ID'],create_snapshot_file)
                print "Snapshot {} for instance {} created {}".format(snapshot.id, instance['Name'], timestamp)
                snapshot_list.append(snapshot.id)
        else:
            print "Snapshot already created for instance {}".format(instance['Name']) 
    return snapshot_list

def fetch_finished_snapshots(region): 
    ec2 = boto3.client('ec2', region_name=region)
    snapshot_filter = ec2.describe_snapshots(OwnerIds=[old_acct],Filters=[{'Name':'progress', 'Values':['100%']}])
    return [snap['SnapshotId'] for snap in snapshot_filter['Snapshots']]


def fetch_available_amis(region):
    ec2 = boto3.client('ec2', region_name=region)
    ami_filter = ec2.describe_images(Owners=[old_acct],Filters=[{'Name':'state', 'Values': ['available']}])
    return [ami['ImageId'] for ami in ami_filter['Images']]

def run_only_started_snapshots(ec2, snapshot_lists, region):
    snapshots_remaining = snapshot_lists
    ami_lists = []
    while snapshots_remaining:
        print "Looking for completed snapshots" 
        # check for snapshots with started status
        for waiting in snapshots_remaining:
            if waiting in fetch_finished_snapshots(region):
                instance_name = get_snapshot_instance_name(ec2,waiting)
                print "Snapshot {} for instance ({}) completed! Attempting to make an ami ({} of {} snapshots remain)".format(waiting, 
                                   instance_name, len(snapshots_remaining), len(snapshot_lists))
                response = create_ami_from_snapshots(ec2, waiting,
                                                instance_name, region)
                ami_name = ''
                if response['ImageId']:
                    ami_name = response['ImageId']
                else:
                    ami_name = get_ami_id_from_snapshot(ec2, waiting)
                ami_lists.append(ami_name)

                snapshots_remaining.remove(waiting)
    return ami_lists
        
def share_only_available_amis(ec2, ami_list, region):                
    amis_remaining = ami_list
    while amis_remaining:
        print "Looking for available amis in {} to share with account {}".format(region, new_acct)
        for waiting in amis_remaining:
            if waiting in fetch_available_amis(region):
               print "Sharing ami {} ({}/{} remaining)".format(waiting,len(amis_remaining),len(ami_list))
               instance_name, snapshot_id = get_instance_snapshot_from_ami(ec2, waiting)
               print share_ami_with_acct(region, waiting, instance_name, new_acct)
               amis_remaining.remove(waiting)
    

def create_ami_from_snapshots(ec2,snapshot_id,instance_name,region):
    timestamp = datetime.now()
    ami_name = "AMI TRANSFER-{} SNAPSHOT-{}".format(instance_name, snapshot_id)
    ami_desc = "created at {}".format(timestamp)
    create_ami_file = "create-ami"
    if not is_complete(region, snapshot_id, create_ami_file):
        response = ec2.register_image(
            Name=ami_name,
            Description=ami_desc,
            Architecture='x86_64',
            RootDeviceName='/dev/sda1',
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda',
                    'Ebs': {
                        'SnapshotId': snapshot_id,
                        'DeleteOnTermination': False,
                    }
                },
            ],
        )   
        record_complete(region, snapshot_id, create_ami_file)
        return response
    else:
        print "Snapshot {} already created!".format(snapshot_id)
        return False
        

def share_ami_with_acct(region, ami, instance_name, acct):
    timestamp = datetime.now()
    ec2 = boto3.client('ec2', region_name=region)
    ami_snapshot_file = "share-ami"
    if not is_complete(region, ami, ami_snapshot_file):
        response = ec2.modify_image_attribute(
            ImageId=ami,
            LaunchPermission={
                'Add': [
                    {
                        'UserId': acct
                    }
                ]
            },
        )
        record_complete(region, ami, 'share-ami')
        print "Sharing {} with acct {} on {}".format(ami,acct,timestamp)
    else:
        print "AMI {} already shared with acct {}".format(ami,acct)

def launch():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", help="provide the region to perform operations in.", required=True) 
    parser.add_argument("--source", help="Amazon UserID for the account transfer", required=True)
    parser.add_argument("--target", help="Amazon UserID for the account you will share AMIs with")
    return parser.parse_args()


if __name__ == "__main__":
    app = launch()   
    regions = []
    new_acct = app.source
    old_acct = app.target
    if app.region == 'all':
        regions = ec2_enumerate.init_regions()
    else:
        regions.append(app.region)
    for region in regions:
        ec2_enumerate.header_pound('   Initiating Transfer Process in {}   '.format(region))
        ec2_resource = ec2_enumerate.init_ec2(region)
        ec2_client = boto3.client('ec2', region_name=region)
        instances, region_list = read_region_from_json(region)
        if 'NID' not in instances:
            ec2_enumerate.header_star('   Making Snapshots   ')
            snapshot_list = make_snapshots(ec2_resource, instances, region)
            if snapshot_list:
                ec2_enumerate.header_star('   Making Amis   ')
                ami_list = run_only_started_snapshots(ec2_client, snapshot_list, region)
                if ami_list:
                    ec2_enumerate.header_star('   Sharing Amis   ')
                    share_only_available_amis(ec2_client, ami_list, region)
        else:
            print "No Instances in this Region"
