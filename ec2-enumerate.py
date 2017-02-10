# Enumerates ec2 instances in a region.
import boto3
import sys
import os
import json
import argparse
from prettytable import PrettyTable

# I had to take time to format the output because it was bothering me plus I want other folks to be able to read it. :)
def stty_columns_size():
    rows, columns = os.popen('stty size', 'r').read().split()
    return columns


def print_header(header_text, character):
    print (str(header_text).center(int(stty_columns_size()), character))


def header_pound(header_text):
    print_header(header_text, '#')


def header_star(header_text):
    print_header(header_text, '*')


def header_line(header_text):
    print_header(header_text, '-')

def launch():
    parser = argparse.ArgumentParser()
    if len(sys.argv) == 0:
        print "Must specify --display and/or --write"
        return False
    else:    
        parser.add_argument("--display", action='store_true', help="Displays your ec2 instances per region to screen.")
        parser.add_argument("--write", action='store_true', help="Writes your ec2 instances per region to a json file (ec2.json)")
        return parser.parse_args()

def init_ec2(region):
    return boto3.resource('ec2', region_name=region)


def init_regions():
    client = boto3.client('ec2')
    return [region['RegionName'] for region in client.describe_regions()['Regions']]

def display_regions(regions):
    # Now iterate through instances in each region.
    region_table = PrettyTable(['REGION'])
    for print_region in regions:
        region_table.add_row([print_region])
    print region_table

def get_instance_name(instance):
    for search in instance.tags:
        if search['Key'] == 'Name':
            return search['Value']
        else:
            return "__not_defined__"

def fetch_instance_data(region):
    instance_data = []
    ec2 = init_ec2(region)
    instances = ec2.instances.all()
    if len(list(instances)) > 0:
        for instance in instances:
            instance_data.append({
                            'Name': get_instance_name(instance),
                            'ID': instance.id,
                            'Type': instance.instance_type,
                            'Volumes': get_instance_volumes(instance)
                        })
    else:
        instance_data.append('NID')
    return instance_data

def get_instance_volumes(instance):
    return str([vol.id for vol in instance.volumes.all()])

def display_all_instances():
    # First get all regions
    print "Acquiring list of regions"
    regions = init_regions()
    display_regions(regions)
    for region in regions:
        header_pound(' REGION: {} '.format(region.upper()))
        instances = fetch_instance_data(region)
        header_line(' {}  INSTANCES '.format(len(list(instances))))
        instances_table = PrettyTable(['NAME','ID','TYPE','VOLUMES'])
        for instance in instances:
            if instance == 'NID':
                instances_table.add_row(['NO INSTANCES IN THIS REGION',' ',' ',' '])
            else:
                instances_table.add_row([instance['Name'],instance['ID'],instance['Type'],instance['Volumes']])
        print instances_table

def region_to_dict():
    ec2_regions_instances = []
    regions = init_regions()
    for region in regions:
        ec2_regions_instances.append({
                            'Region': region,
                            'Instances': fetch_instance_data(region)
                        })
    return ec2_regions_instances

def write_to_json():
    data = region_to_dict()
    with open('ec2.json', 'w') as f:
        json.dump(data, f)


if __name__ == "__main__":
    app = launch()
    if app:
        if app.display:
            display_all_instances()
        if app.write:
            write_to_json()
