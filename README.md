# Transition EC2
I wrote this series of scripts to transition data instances from my AWS account to another account. There are many ways that ownership of the account couldn't happen, which would be by far the simplest method.  

The plan here is to first enumerate what we have across accounts (ec2-enumerate.py), then to create snapshots of the running instances, create AMIs, and share the AMIs with the new account.

Documentation is a WIP, apologies in advance for brevity.

# Installing

after cloning, cd into the directory then:
```
virtualenv ec2
. ec2/bin/activate

pip install -r requirements.txt
```

Then configure your aws credentials using ```aws configure```.

# Process 

Run ec2-enumerate.py 

```
python ec2-enumerate.py --show  # displays to screen
python ec2-enumerate.py --write # write information to a json file to be read later.
```

After getting a json file with  ```--write```, you can use snapshot_instances.py to share AMIS created from snapshots with the old account:

```
python snapshot_instances.py --region <specific region or 'all'> --source <old account> --target <new account to share with>
```

# TODO/Limitations

* No way to reset tracking of snapshots and images other than manual checking and deleting of the created text files. Will make a function to do that.
* Whether task was performed or not is rather primitively done by writing to a text file and checking it. Plan to check the actual AWS region for AMIs with instance name to avoid creation of duplicates, but be warned if you use that that making duplicates is pretty easy to do.

