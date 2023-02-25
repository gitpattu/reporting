import boto3
import pprint
import sys
import json
from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB


# run as follows
# python3 list_applb.py <region> <aws_profile>
# python3 list_applb.py us-east-1 default

# get the Target Group ARNs for given load balancer ARN
def getTGARNs(lbarn):
  # lets get the description of all TGs
  tgs=elb.describe_target_groups(LoadBalancerArn=lbarn)
  # define TGARNs and append from the previous output
  tgarns=[]
  for tg in tgs['TargetGroups']:
    tgarns.append(tg['TargetGroupArn'])
  return tgarns


# get the instance name for given instance id  
def getInstanceName(instanceid):
  instances_detail = ec2.describe_instances(Filters=[{'Name': 'instance-id','Values': [instanceid]},],)
  #print("debug - 4 - instances", instancedetail)
  for instances in instances_detail["Reservations"]:
    for instance in instances["Instances"]:
      for tag in instance["Tags"]:
        if tag['Key'] == 'Name':
          return (tag['Value'])

# lets get the health of TG defined by ARN
def getTGHealth(tgarn):
  health  = []
  targets = elb.describe_target_health(TargetGroupArn=tgarn)
  
  # process the output to get health
  for target in targets["TargetHealthDescriptions"]:
    #print("debug - 3 target =>", target)
    target["Name"] = getInstanceName(target['Target']['Id'])
    health.append(target)
  #print("debug 4 - health =>", health)
  return health

# lets get ELB information
def describelbs():
  # define variables
  lbsinfo = {}
  lbsinfo['lbs'] = []
  
  # get details of all lbs
  lbs_temp = elb.describe_load_balancers(PageSize=400)
  
  # process each lb, associated TG, and nodes
  for lb in lbs_temp['LoadBalancers']:
    lbinfo = {}
    lbinfo['name'] = lb['LoadBalancerName']
    lbinfo['type'] = lb['Type']
    lbinfo['tgs']  = []
    #print("debug 1 - lbs => ",lbs['name'], lbs['type'])
  
    # get ARNs for all TGs in this load balancer
    tgarns = []
    tgarns = getTGARNs(lb['LoadBalancerArn'])
    #print("debug 2 - TG ARNs => ",tgarns)

    if len(tgarns) > 0:
      for tgarn in tgarns:      
        tginfo = {}

        # get name of TG
        tginfo['name'] = tgarn.split("/")[1]
        #print("debug 3 - tg name =>", tginfo_temp['name'])
        
        # get health of TG members
        tghealth = getTGHealth(tgarn)
        #print("debug 4 - tg health", tghealth)
        if len(tghealth) > 0:
          tginfo['instances'] = tghealth
        else:
          tginfo['instances'] = ""
        
        # append the tg info into lbs
        lbinfo['tgs'].append(tginfo)
    
    # append the processed lb info into main variable    
    lbsinfo['lbs'].append(lbinfo)

  print("\n",json.dumps(lbsinfo, indent=2, sort_keys=True))

    #with Diagram(profile+"_ABL_"+lbsinfo['name'],show=False):
      #lb = ELB(lbs['public-batrasio-shared-pro-ap2'])
      #print("\n", json.dumps(lb, indent=2))
      #instances_group=[]
      #for instance in lbs['TGinfo']
      
if __name__ == "__main__":
  if len(sys.argv) < 3:
    print(" RUN IT AS: python3 list_applb.py <region> <aws_profile> ")
    exit()
  region      = sys.argv[1]
  profile     = sys.argv[2]
  aws_session = boto3.session.Session(profile_name=profile,region_name=region)
  elb         = aws_session.client('elbv2')
  ec2         = aws_session.client('ec2')
  describelbs()