# Transition EC2
I wrote this series of scripts to transition data instances from my AWS account to another account. There are many ways that ownership of the account couldn't happen, which would be by far the simplest method.  

The plan here is to first enumerate what we have across accounts (ec2-enumerate.py), then to create snapshots of the running instances (snapshot_instances.py), create AMIs out of each snapshot (ami_snapshots.py), then provide permissions to share all the AMIs with another account so they can make instances from them (share_amis.py).

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


