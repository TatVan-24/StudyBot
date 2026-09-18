# RCA: M5 Step 1 (test-v3.jsonl) Diagnostics

Analyzing failures using Frozen Baseline (minmax_0.4)
---

## eval_test_v3_001 (Tags: pdf, semantic-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Will hosting my web app on Amazon automatically make it resilient to failures?
**Target Blocks:** 10

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9857 (Dense: 0.5895 | BM25: 11.7398)
```text
onstructs such as availability zones, elastic IP addresses, and snapshots to design high availability and fault tolerant applications. Remember hosting an application on the cloud does not make it fault-tolerant or highly available.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8658 (Dense: 0.5363 | BM25: 9.9825)
```text
In such environments, it is important that tasks and processes be highly repeatable, resilient, flexible, and robust. Amazon provides numerous tools, APIs, and services to enable you to create highly automated DevOps pipelines. These pipelines can help you
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8027 (Dense: 0.4967 | BM25: 9.1862)
```text
ese would include DNS or domain services, load balancers, web and application servers, database servers, application services-related failures, and data center-related failures. You will need to ensure you have a mitigation strategy for each of these types
```

---

## eval_test_v3_002 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 10
**Query:** Where can I find the steps to set up a new Amazon Web Services profile?
**Target Blocks:** 5

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9686 (Dense: 0.5666 | BM25: 14.1519)
```text
1. Get to grips with Amazon Web Services from a Microsoft Enterprise .NET viewpoint.

2. Fully understand all of the AWS products including EC2, EBS, and S3.

3. Quickly set up your account and manage application security.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9377 (Dense: 0.5957 | BM25: 13.0776)
```text
• Shortcuts for Amazon Web Services: On the console management screen, you can create shortcuts of frequently accessed services via the Edit option, as shown in the following screenshot:
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.9074 (Dense: 0.6254 | BM25: 12.0120)
```text
You will need to create an account on Amazon before you can use the Amazon Web Services (AWS). Amazon provides a 12 month limited fully functional free account that can be used to learn the different components of AWS. With this account, you get access to 
```

### First Target Chunk (Found at Rank 10)
Score: 0.8305 (Dense: 0.4727 | BM25: 12.0075)
```text
• Amazon regions: This option allows you to access the AWS in a specific region. In the following screenshot, all the Amazon Web Services are located in the US East (N. Virginia) region:

• Support: You can navigate to the Help, Forums, and support pages:
```

---

## eval_test_v3_003 (Tags: pdf, semantic-heavy, ambiguous)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 14
**Query:** Which chapter covers architecture for applications that need to grow?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8480 (Dense: 0.5019 | BM25: 9.7895)
```text
Chapter 2: Designing Cloud Applications – An Architect's Perspective 11

Multi-tier architecture 12 Designing for multi-tenancy 14

Data security 16 Data extensibility 18 Application multi-tenancy 22
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8431 (Dense: 0.5881 | BM25: 8.9403)
```text
Chapter 2, Designing Cloud Applications – An Architect's Perspective, describes familiar and not-so familiar architectural best practices in the cloud context. These include designing a multi-tier architecture and designing for multi-tenancy, scalability, 
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8218 (Dense: 0.3276 | BM25: 10.8559)
```text
What this book covers
```

### First Target Chunk (Found at Rank 14)
Score: 0.6539 (Dense: 0.6592 | BM25: 4.8887)
```text
Chapter 4: Designing for and Implementing Scalability 83 Defining scalability objectives 84 Designing scalable application architectures 84
```

---

## eval_test_v3_004 (Tags: pdf, lexical-anchor-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** What should I enter for the SSL certificate label?
**Target Blocks:** 9

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9860 (Dense: 0.6489 | BM25: 20.1998)
```text
3. The next step is to associate the SSL certificate with the ELB. Click on Change under SSL Certificate. The following are the properties:

° Certificate Type: Make sure the radio button Upload a new SSL

Certificate is selected.
```

#### Rank 2: ✅ TARGET
Score: 0.9657 (Dense: 0.5872 | BM25: 20.6830)
```text
° Certificate Name: Enter the name of the certificate for your reference;
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7573 (Dense: 0.4750 | BM25: 15.6515)
```text
----You are about to be asked to enter information that will be incorporated into your certificate request. What you are about to enter is what is called a Distinguished Name or a DN. There are quite a few fields but you can leave some blank For some field
```

---

## eval_test_v3_005 (Tags: pdf, semantic-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** How can I verify if a group of small servers matches the performance of a single xlarge machine?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.8658 (Dense: 0.7139 | BM25: 13.4830)
```text
At this stage, you should provision multiple smaller instances (from the same families) that match the xlarge instance's compute power and conduct the same load tests. This is done to check whether we can achieve the same performance,
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8389 (Dense: 0.5721 | BM25: 14.6964)
```text
that run inside the auto scaling group. This number typically depends on the load the application is expecting and how many requests a single instance can serve with accepted latencies. Before deploying to production, it is good practice to benchmark the a
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8162 (Dense: 0.4860 | BM25: 15.2471)
```text
caling group starts, it starts with the minimum number of instances. To verify that the auto scaling group is working as configured, copy the DNS name of the elastic load balancer as described in step 9 in Creating Elastic Load Balancer. In this case, it i
```

---

## eval_test_v3_006 (Tags: pdf, lexical-anchor-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** What protocol is used to access files stored in S3 containers from a browser?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9430 (Dense: 0.5781 | BM25: 17.5549)
```text
Amazon S3

Amazon S3 is a highly durable and distributed data store. Using a web services interface, you can store and retrieve large amounts of data as objects in buckets (containers). The stored objects are also accessible from the web via HTTP.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7435 (Dense: 0.5741 | BM25: 11.7772)
```text
Static content or files include CSS, HTML, images, and so on that are stored in Amazon S3 (and not on your web server instance). This can reduce the load on your web servers and improve the efficiency of maintaining content (by storing at one S3 location) 
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7252 (Dense: 0.6554 | BM25: 10.0656)
```text
The easiest way to secure data on S3 is via the S3 console. Select the bucket where the file is to be uploaded, click on the Upload button; this presents a pop up window to upload files, as shown in the following screenshot:
```

---

## eval_test_v3_007 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 3
**Query:** Where do I download the version control CLI?
**Target Blocks:** 13

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9791 (Dense: 0.5507 | BM25: 10.1913)
```text
4. To install the Amazon command line interface (CLI), use the following command: sudo pip install awscli

5. To upgrade the CLI, use the following command: sudo pip install --upgrade awscli
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9014 (Dense: 0.3796 | BM25: 10.5586)
```text
7. The last step is to set up the credentials of your AWS account and the settings to be used by the CLI. If you do not have the access keys you can create it via the IAM management console:
```

#### Rank 3: ✅ TARGET
Score: 0.8949 (Dense: 0.5147 | BM25: 9.0741)
```text
• Git command line tools: For download the link is http://git-scm.com/ downloads.
```

---

## eval_test_v3_008 (Tags: pdf, semantic-heavy, context-dependent)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** What is the best way to allow SaaS users to add custom fields without altering the core database structure?
**Target Blocks:** 2

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9698 (Dense: 0.5395 | BM25: 16.6796)
```text
for all the extra fields in the table. Alternatively, you can introduce an additional column for the table name, to have a common table describing all custom fields (for each tenant) across all the tables in the schema.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8933 (Dense: 0.5514 | BM25: 14.3725)
```text
 you don't change your schema for a tenant so much that your product no longer fits into the SaaS model. But you do want to bake in sufficient flexibility and extensibility to handle custom data requirements of your customers (without impacting subsequent 
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8606 (Dense: 0.5610 | BM25: 13.3156)
```text
We can define a separate database schema for each of the tenants (within the same database server instance) for applications having a limited number of database tables. This approach is relatively simple to implement, and offers flexibility for custom tabl
```

---

## eval_test_v3_009 (Tags: pdf, lexical-anchor-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** What port number needs to be configured when setting up the secure load balancer protocol?
**Target Blocks:** 6

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 1.0000 (Dense: 0.7288 | BM25: 26.0199)
```text
° From Load Balancer Protocol, select the HTTPS protocol ° Set Load Balancer Port to 8443; this is the port we added to our

security group in our previous step

° From Instance Protocol, select HTTP; this is the protocol between
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8502 (Dense: 0.6122 | BM25: 22.1126)
```text
the ELB and the EC2 instances ° Set Instance Port to 8080; this is the port that the Tomcat is listening on ° From Load Balancer Protocol, delete the HTTP protocol as it is not

needed anymore
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8420 (Dense: 0.7120 | BM25: 19.5428)
```text
3 and between 1024-65535. Select HTTP as the protocol on both Load Balancer Protocol and Instance Protocol.
```

---

## eval_test_v3_010 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 9
**Query:** Can I use the free tier plan for my live production application?
**Target Blocks:** 5

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8527 (Dense: 0.6630 | BM25: 13.3495)
```text
Planning for production go-live activities
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8446 (Dense: 0.4581 | BM25: 16.5350)
```text
only one that is available for the free tier.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7926 (Dense: 0.6287 | BM25: 12.1517)
```text
Deploying to Production and Going Live
```

### First Target Chunk (Found at Rank 9)
Score: 0.7184 (Dense: 0.5269 | BM25: 11.6635)
```text
° Support Plan: You can subscribe to one from the following, Basic, Developer, Business, or Enterprise. We recommend subscribing to the Basic plan to start with.
```

---

## eval_test_v3_011 (Tags: pdf, lexical-anchor-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Which AWS service is used to create users and assign permissions?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9550 (Dense: 0.6675 | BM25: 18.0925)
```text
The AWS IAM service is central to implementing security for your applications on the AWS cloud. Some of the main activities and best practices for AWS IAM are listed as follows:

• Use IAM to create users, groups, and roles and assign permissions.
```

#### Rank 2: ✅ TARGET
Score: 0.8667 (Dense: 0.7079 | BM25: 14.8081)
```text
• Manage permissions using groups. You assign permissions to groups and then assign individuals to them. While assigning permissions to groups, always follow the principle of granting least privilege. AWS provides several policy templates for each of their
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8157 (Dense: 0.7022 | BM25: 13.3568)
```text
AWS Identity and Access Management (IAM) is a web service that enables you to manage users, groups, and user permissions within the AWS infrastructure. This allows for central control of users, groups, user access, and security credentials. As there are a 
```

---

## eval_test_v3_012 (Tags: pdf, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 43
**Query:** Which option do I select to add a brand new secure socket layer cert?
**Target Blocks:** 9

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8355 (Dense: 0.2898 | BM25: 15.5352)
```text
2. After creating a new account or using your existing retail Amazon account, select the I am a returning user and my password is: option and click on Sign in using our secure server. A set of intuitive screens will guide you through multiple screens in or
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7391 (Dense: 0.2060 | BM25: 14.5214)
```text
r our purposes, you do not need to select this option.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7170 (Dense: 0.4609 | BM25: 9.4406)
```text
° Enable advanced VPC configuration: The advanced VPC configuration option allows you to specify your own subnets. Select this option if you want to route traffic to EC2 instances running in specific availability zones. Select this option as we want to rou
```

### First Target Chunk (Found at Rank 43)
Score: 0.5110 (Dense: 0.4914 | BM25: 3.5663)
```text
3. The next step is to associate the SSL certificate with the ELB. Click on Change under SSL Certificate. The following are the properties:

° Certificate Type: Make sure the radio button Upload a new SSL

Certificate is selected.
```

---

## eval_test_v3_013 (Tags: pdf, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 5
**Query:** How do I check the web server access logs for my EC2 instances deployed via CloudFormation?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9052 (Dense: 0.5915 | BM25: 16.0723)
```text
aws cloudformation create-stack --stack-name a1ecommerce --template-body file://a1ecommerceaws.json --region=us-east-1

The progress of the CloudFormation stack can be monitored via the CloudFormation dashboard via the Amazon web console.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8872 (Dense: 0.4418 | BM25: 17.7290)
```text
Via the Amazon web console

There is another option to create the CloudFormation stack via the CloudFormation dashboard. Navigate to the CloudFormation dashboard from the Amazon web console and click on Create Stack.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8081 (Dense: 0.5559 | BM25: 13.7243)
```text
The public IP address of the instance is available from Instances in the EC2 dashboard navigation pane:

1. Log in to the instance via ssh, using the following command: ssh –i ~/.ssh/ec2AccessKey.pem ubuntu@54.172.48.64
```

### First Target Chunk (Found at Rank 5)
Score: 0.7817 (Dense: 0.6020 | BM25: 12.2703)
```text
° From the CloudFormation web console, navigate to Logs; there will be an entry for /var/log/tomcat7/access_log.log, which implies the log agent has been installed and configured correctly. Drill down by clicking on the Log Groups entry, a list of all the 
```

---

## eval_test_v3_014 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 4
**Query:** What identifier does the system give back that I need to save for the launch config?
**Target Blocks:** 14

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8193 (Dense: 0.4081 | BM25: 17.2747)
```text
° DB Instance Identifier: This is the identifier for the MySQL server database instance, and this identifier is used for defining the DNS entry for the DB instance. Type a1ecommerce in the text field.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7993 (Dense: 0.2843 | BM25: 19.0536)
```text
° Identity Verification: Amazon does a call back via an automated system to verify your telephone number.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7402 (Dense: 0.5011 | BM25: 12.9459)
```text
• Launch Configuration: The ImageId is your base AMI instance that the auto scaling group will launch. Replace the image ID with your own AMI:
```

### First Target Chunk (Found at Rank 4)
Score: 0.7292 (Dense: 0.5214 | BM25: 12.2006)
```text
"Key": "Name"

} ],

Instance ID is available in the JSON response (at the same level as Tags):

"InstanceId": "i-3f7e0ed3",

Make a note of the instance ID as it will be used in creating a launch configuration.

2. To create the AMI, use the following command:
```

---

## eval_test_v3_015 (Tags: pdf, semantic-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Which cloud service model requires the customer to handle the most administration overhead for virtual servers?
**Target Blocks:** 7

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9259 (Dense: 0.7721 | BM25: 14.8328)
```text
onal in-premise models and the virtual server provisioning models (typically offered by data center outsourcers). The onus of administering these resources rests largely with the customer.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8750 (Dense: 0.7122 | BM25: 14.1382)
```text
Most cloud providers maintain a distributed set of servers in multiple data centers around the globe. These servers are used as a Content Delivery Network (CDN) to serve content to end users from locations closest to them. This service is made available to
```

#### Rank 3: ✅ TARGET
Score: 0.8709 (Dense: 0.6227 | BM25: 15.1317)
```text
From an infrastructure perspective, the customer does not manage or control the underlying cloud infrastructure in all three service models.
```

---

## eval_test_v3_016 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 35
**Query:** Do I have to deploy an Elastic Load Balancer for my disaster recovery location?
**Target Blocks:** 9

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9426 (Dense: 0.5192 | BM25: 19.4249)
```text
° Load Balancing: An auto scaling group can be associated with an elastic load balancer. Select the elastic load balancer we created earlier in this chapter under Creating Elastic Load Balancer section, that is, a1electronicsecommerce-elb. If you are using
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9411 (Dense: 0.6224 | BM25: 17.5183)
```text
Creating Elastic Load Balancer
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8150 (Dense: 0.5765 | BM25: 14.2605)
```text
Using AWS for disaster recovery
```

### First Target Chunk (Found at Rank 35)
Score: 0.5873 (Dense: 0.3620 | BM25: 10.7516)
```text
 load is shared by all the instances behind the load balancer.
```

---

## eval_test_v3_017 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 39
**Query:** Does the book cover strategies to reduce my monthly cloud expenses?
**Target Blocks:** 3

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9021 (Dense: 0.5324 | BM25: 12.2890)
```text
This chapter will describe the main AWS components and services. We will also cover strategies to lower your cloud infrastructure costs, and how they influence your architectural decisions. Furthermore, this chapter will discuss the typical characteristics
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8509 (Dense: 0.5040 | BM25: 11.5305)
```text
ations. Finally, we also cover running packaged applications on the AWS cloud.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8226 (Dense: 0.4881 | BM25: 11.1120)
```text
There should be a strong preference to minimize human or manual intervention. Hence, it is preferred to implement strategies using services made available by the cloud platform to reduce the chances of failures or automate recovery from such failures. For 
```

### First Target Chunk (Found at Rank 39)
Score: 0.5778 (Dense: 0.6254 | BM25: 4.6960)
```text
 we described some techniques for lowering your cloud infrastructure bills. We also explained the purpose and characteristics of environments that are typically provisioned for cloud development. Finally, we walked you through the process of provisioning t
```

---

## eval_test_v3_018 (Tags: pdf, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 661
**Query:** Is there a section about making databases highly available?
**Target Blocks:** 9

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8879 (Dense: 0.5011 | BM25: 10.9334)
```text
he master database is synchronously replicated to the slave. Overall, the architecture represents a simple way to achieve a highly scalable and highly available application in a cloud environment.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8723 (Dense: 0.4329 | BM25: 11.3697)
```text
Elastic load balancing and Amazon Route 53 are critical infrastructure components for scalable and highly available applications; we discuss these services in the next section.
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7956 (Dense: 0.6464 | BM25: 7.6254)
```text
In this section, we have primarily covered multi-tenant approaches for relational databases. Depending on your particular application requirements, for instance, type and volume of data, and types of database operations, a NoSQL database can be a good data
```

### First Target Chunk (Found at Rank 661)
Score: 0.2517 (Dense: 0.3966 | BM25: 0.0000)
```text
Setting up high availability 135 The AWS high availability architecture 135 HA support for auto scaling groups 138 HA support for ELB 139 HA support for RDS 140

Summary 142
```

---

## eval_test_v3_019 (Tags: pdf, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 5
**Query:** What is the Pilot Light approach?
**Target Blocks:** 8

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 1.0000 (Dense: 0.7570 | BM25: 17.4926)
```text
Using a Pilot Light architecture for DR
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7378 (Dense: 0.5742 | BM25: 12.4351)
```text
This option is similar to the Pilot Light architecture; however, in this case, we run a scaled down version of the production environment. In the event of a disaster, we simply divert the traffic to this site and rapidly scale up to the full-blown producti
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6324 (Dense: 0.3754 | BM25: 12.1710)
```text
P

Payment Card Industry (PCI) 145 Pilot Light architecture

using, for disaster recovery 133

Platform as a Service (PaaS) 1, 4 principle of least privileges
```

### First Target Chunk (Found at Rank 5)
Score: 0.5239 (Dense: 0.3610 | BM25: 9.2126)
```text
Using AWS for disaster recovery 132 Using a backup and restore DR strategy 133 Using a Pilot Light architecture for DR 133

Using a warm standby architecture for DR 133 Using a multi-site architecture for DR 134 Testing a disaster recovery strategy 134
```

---

## eval_test_v3_020 (Tags: pdf, context-dependent)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** What does the section right before getting started with the AWS interface cover?
**Target Blocks:** 4

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9576 (Dense: 0.6436 | BM25: 21.6780)
```text
We would like to conclude our introduction to cloud computing by getting you started on AWS, right away. The next two sections will help you set up your AWS account and familiarize you with the AWS management console.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7204 (Dense: 0.7205 | BM25: 11.5771)
```text
This section introduces you to provisioning the AWS infrastructure in order to deploy and run the A1Electronics e-commerce application securely on AWS. You will also see the code changes required at the application level. By the end of this section, you wi
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6811 (Dense: 0.6188 | BM25: 12.1842)
```text
To help you get started on Amazon Web Services (AWS), we will end the chapter by walking you through the step-by-step process of creating an AWS account, and describing some of the salient features of the AWS dashboard.
```

---

## eval_test_v3_021 (Tags: txt, semantic-heavy, cross_lingual)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 5
**Query:** Tại sao việc theo dõi hệ thống lại khó khăn khi dùng nhiều sản phẩm khác nhau?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9066 (Dense: 0.4760 | BM25: 26.5139)
```text
**Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8060 (Dense: 0.3922 | BM25: 24.3112)
```text
Khi nào viết ADR:

	+ Quyết định affect > 1 team

	+ Reversal cost cao (> 1 tháng work để undo)

	+ Decision sẽ bị question lại trong 6-12 tháng tới (“tại sao mình dùng X?”)

Khi không cần:

	+ Minor changes (tool version bump, refactor)

	+ Spike/POC

---
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7253 (Dense: 0.3828 | BM25: 20.9989)
```text
#### Table of Contents

- **I. Data Layer Architecture + Observability Pipeline**

  - **1. Three Pillars of Observability**

    - Metric — “Cái gì đang sai?”

    - Log — “Tại sao sai?”

    - Trace — “Ở đâu trong hệ thống?”

    - So sánh nhanh
```

### First Target Chunk (Found at Rank 5)
Score: 0.6568 (Dense: 0.4827 | BM25: 15.2986)
```text
### 2.1. **Collection**- Lấy data từ service

**Vấn đề**: mỗi service product có các cách ```log/metric/trace``` khác nhau
```

---

## eval_test_v3_022 (Tags: txt, semantic-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Đoạn code nào chịu trách nhiệm đẩy dữ liệu telemetry từ bên trong ứng dụng ra ngoài?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.9838 (Dense: 0.5567 | BM25: 19.3340)
```text
--> **Giải pháp**: ```OpenTelemetry(OTel)``` gom tất cả vào 1 bộ SDK duy nhất --> output đi đến bất kì backend nào.
Components của OTel: 

	+ SDK: thư viện embedded trong service, code emit telemetry qua SDK
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9333 (Dense: 0.4600 | BM25: 19.8690)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7467 (Dense: 0.4312 | BM25: 14.3489)
```text
| **Khái niệm (Data Contract)** | **Cam kết giữa các team** | Là concept rộng hơn Schema. Producer cam kết chuẩn dữ liệu (vd: field X là string, không null, max 256 chars). Consumer tin tưởng và dựa vào đó để sử dụng. |
```

---

## eval_test_v3_023 (Tags: txt, semantic-heavy, multi-block)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 61
**Query:** Phương án lưu trữ log nào rẻ nhất cho dữ liệu hơn 1 năm mà chỉ dùng để kiểm toán?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8756 (Dense: 0.4372 | BM25: 41.1760)
```text
==> **Giải pháp**: Dùng Feature Store làm kho trung tâm. Dữ liệu (features) chỉ cần tính toán và lưu đúng 1 lần, sau đó phân phối nhất quán cho cả quá trình Training lẫn Inference.

**Architecture**:
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7870 (Dense: 0.5361 | BM25: 31.4745)
```text
==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7097 (Dense: 0.4549 | BM25: 29.1438)
```text
| | **Parquet on S3** | Columnar format, cho phép query thông qua Athena/Spark/DuckDB. | |

| | **S3 Glacier** | Siêu rẻ ($0.004/GB/tháng). | Lấy dữ liệu ra (retrieve) mất hàng giờ, chỉ dùng cho compliance archive. |

</div>

**Hot/Warm/Cold**:
```

### First Target Chunk (Found at Rank 61)
Score: 0.3366 (Dense: 0.3162 | BM25: 8.6329)
```text
 chỉ compliance, retrieve mất giờ
```
```

---

## eval_test_v3_024 (Tags: txt, ambiguous)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Bảng phân loại các tùy chọn lưu trữ nằm ở đâu?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.8284 (Dense: 0.2981 | BM25: 37.1926)
```text
<div style="overflow: auto; max-height: 400px; width: 100%;">

| Phân loại | Tùy chọn / Khái niệm | Đặc điểm & Lưu ý |

| :--- | :--- | :--- |
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.6447 (Dense: 0.4939 | BM25: 18.0903)
```text
  - **2. Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**

    - 2.1 Collection — Lấy Data Từ Service

    - 2.2 Transport — Buffer Giữa Producer và Consumer

    - 2.3 Processing — Transform & Enrich

    - 2.4 Storage — Lưu Ở Đâu?
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6411 (Dense: 0.4941 | BM25: 17.8561)
```text
### 2.4 **Storage**- Lưu ở đâu?

<div style="overflow: auto; max-height: 400px; width: 100%;">

| Nhóm Storage (Mục đích) | Công cụ | Đặc điểm nổi bật | Hạn chế / Lưu ý |

| :--- | :--- | :--- | :--- |
```

---

## eval_test_v3_025 (Tags: txt, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 3
**Query:** Cấu trúc của một điểm dữ liệu metric bao gồm những trường nào?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9143 (Dense: 0.5020 | BM25: 22.9644)
```text
==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8684 (Dense: 0.3160 | BM25: 26.2276)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

#### Rank 3: ✅ TARGET
Score: 0.7754 (Dense: 0.3421 | BM25: 21.4237)
```text
	**Định nghĩa**: number by time, cấu trúc data point gồm: ```timestamp, name (cpu_usage), value (75.2), labels (host=server-1, service=payment)```
ví dụ: ```2024-01-15T10:23:45Z  latency_p99  234  {service="payment", endpoint="/checkout"}```

	**Đặc điểm**:
```

---

## eval_test_v3_026 (Tags: txt, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 3
**Query:** Khi nào việc dùng Feature Store bị coi là làm quá mức cần thiết?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9549 (Dense: 0.5188 | BM25: 27.8970)
```text
==> **Giải pháp**: Dùng Feature Store làm kho trung tâm. Dữ liệu (features) chỉ cần tính toán và lưu đúng 1 lần, sau đó phân phối nhất quán cho cả quá trình Training lẫn Inference.

**Architecture**:
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9514 (Dense: 0.4943 | BM25: 28.4960)
```text
## 3.  **Feature Store** — Khi Cần ML
```

#### Rank 3: ✅ TARGET
Score: 0.9476 (Dense: 0.4357 | BM25: 30.1648)
```text
	+ Tecton (managed, expensive) — production-grade

	+ Hopsworks (open-source + managed) — full ML platform

| Tiêu chí | Khi NÀO CẦN Feature Store | Khi KHÔNG CẦN (Overkill) |

| :--- | :--- | :--- |
```

---

## eval_test_v3_027 (Tags: txt, semantic-heavy)
**Status:** Near Failure (Rank 2)
**First Hit Rank:** 2
**Query:** Phần nào mô tả đường đi của luồng dữ liệu observability?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9256 (Dense: 0.5166 | BM25: 24.5330)
```text
==> Bằng việc hiển thị chi tiết đường đi và thời gian của **request (show path)**, ```Trace``` giúp phát hiện ngay lập tức **điểm nghẽn hệ thống (bottleneck identification)**, nhưng vì phải chứa quá nhiều **operation nhỏ (spans)** nên dữ liệu của nó rất **
```

#### Rank 2: ✅ TARGET
Score: 0.7342 (Dense: 0.5903 | BM25: 15.0431)
```text
## 2. **Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**

data observability đi qua 5 stages: 

```
[Service] → [Collection] → [Transport] → [Processing] → [Storage] → [Query/AI]
```
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6708 (Dense: 0.3956 | BM25: 16.8454)
```text
**Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế.
```

---

## eval_test_v3_028 (Tags: txt, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 30
**Query:** Làm thế nào để tiết kiệm chi phí chuyển dữ liệu giữa các vùng (AZ)?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8461 (Dense: 0.3429 | BM25: 22.7702)
```text
| **Khái niệm (Data Contract)** | **Cam kết giữa các team** | Là concept rộng hơn Schema. Producer cam kết chuẩn dữ liệu (vd: field X là string, không null, max 256 chars). Consumer tin tưởng và dựa vào đó để sử dụng. |
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.7783 (Dense: 0.3440 | BM25: 20.1724)
```text
| **Đánh đổi (Trade-off)** | **Strict contract (Chặt chẽ)** | Hạn chế tối đa bug chéo giữa các team (cross-team) nhưng làm chậm tốc độ phát triển (bất kỳ thay đổi schema nào cũng cần review). |
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7760 (Dense: 0.3364 | BM25: 20.2488)
```text
**Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế.
```

### First Target Chunk (Found at Rank 30)
Score: 0.4457 (Dense: 0.4755 | BM25: 4.7188)
```text
| **Ingest** | Events/sec or GB/day | Filter at source; sampling; reduce log verbosity |

| **Egress** | GB transferred cross-AZ/region | Co-locate; cache at edge |
```

---

## eval_test_v3_029 (Tags: txt, semantic-heavy)
**Status:** Near Failure (Rank 2)
**First Hit Rank:** 2
**Query:** Rủi ro của việc thiết kế hệ thống với hợp đồng dữ liệu lỏng lẻo là gì?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9315 (Dense: 0.5867 | BM25: 35.8568)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

#### Rank 2: ✅ TARGET
Score: 0.8688 (Dense: 0.6304 | BM25: 30.7010)
```text
| | **Loose contract (Lỏng lẻo)** | Cho phép phát triển siêu tốc (fast iteration) nhưng dễ dẫn đến thảm họa tích hợp (integration hell) khi hệ thống phình to (scale). |

</div>
----
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6961 (Dense: 0.2443 | BM25: 32.7985)
```text
### 1.3. **Trace**- trả lời câu hỏi **ở đâu trong hệ thống?**

**Định nghĩa**: record của 1 request đi qua hệ thống. 1 trace là tập hợp của spances, 1 span là 1 operation tại 1 service.
```

---

## eval_test_v3_030 (Tags: txt, semantic-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Cách tối ưu chi phí cho dữ liệu giám sát cũ là gì?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 0.8529 (Dense: 0.4485 | BM25: 24.7329)
```text
### 1. Các yếu tố ảnh hưởng chi phí (Cost Drivers)

| Component | Cost driver | Tối ưu cost |

| :--- | :--- | :--- |

| **Storage** | GB stored × retention days | Tier: hot/warm/cold; downsample old data |
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8139 (Dense: 0.4738 | BM25: 22.5969)
```text
==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7389 (Dense: 0.4070 | BM25: 20.8952)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

---

## eval_test_v3_031 (Tags: txt, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 7
**Query:** Dữ liệu feature từ Redis đi đâu tiếp theo trong pipeline?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9956 (Dense: 0.5590 | BM25: 28.2845)
```text
## 2. **Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**

data observability đi qua 5 stages: 

```
[Service] → [Collection] → [Transport] → [Processing] → [Storage] → [Query/AI]
```
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.9287 (Dense: 0.5553 | BM25: 25.2496)
```text
  - **2. Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**

    - 2.1 Collection — Lấy Data Từ Service

    - 2.2 Transport — Buffer Giữa Producer và Consumer

    - 2.3 Processing — Transform & Enrich

    - 2.4 Storage — Lưu Ở Đâu?
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.6874 (Dense: 0.5427 | BM25: 14.2873)
```text
#### Table of Contents

- **I. Data Layer Architecture + Observability Pipeline**

  - **1. Three Pillars of Observability**

    - Metric — “Cái gì đang sai?”

    - Log — “Tại sao sai?”

    - Trace — “Ở đâu trong hệ thống?”

    - So sánh nhanh
```

### First Target Chunk (Found at Rank 7)
Score: 0.5726 (Dense: 0.5309 | BM25: 9.2549)
```text
```
Stream → Compute features → Online store (Redis) → Inference
                          → Offline store (S3) → Training
```

**Tools**:

	+ Feast (open-source, CNCF) — popular, dễ deploy, support Redis/DynamoDB online + S3/BigQuery offline
```

---

## eval_test_v3_032 (Tags: txt, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 12
**Query:** Cơ sở dữ liệu dạng chuỗi thời gian nào có ngôn ngữ truy vấn nội tại mạnh mẽ?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.8738 (Dense: 0.4496 | BM25: 22.1015)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8195 (Dense: 0.5446 | BM25: 18.1780)
```text
==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.8044 (Dense: 0.3835 | BM25: 20.8842)
```text
| | **VictoriaMetrics** | Tương thích Prometheus, scale tốt hơn 10x, retention nhiều tháng/năm. | |

| | **InfluxDB** | Purpose-built TSDB, xử lý mạnh ở high cardinality (dữ liệu có độ phân mảnh nhãn cao). | |
```

### First Target Chunk (Found at Rank 12)
Score: 0.4930 (Dense: 0.5485 | BM25: 6.0709)
```text
| **Time-series Database (Metric)** | **Prometheus** | Local TSDB, query language PromQL mạnh, retention mặc định 15 ngày. | Single-node, không High Availability (HA) tốt cho long retention. |
```

---

## eval_test_v3_033 (Tags: txt, lexical-anchor-heavy)
**Status:** Success (Rank 1)
**First Hit Rank:** 1
**Query:** Công cụ nào giúp thống nhất các SDK để gửi dữ liệu observability đến mọi backend?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ✅ TARGET
Score: 1.0000 (Dense: 0.6912 | BM25: 29.3346)
```text
--> **Giải pháp**: ```OpenTelemetry(OTel)``` gom tất cả vào 1 bộ SDK duy nhất --> output đi đến bất kì backend nào.
Components của OTel: 

	+ SDK: thư viện embedded trong service, code emit telemetry qua SDK
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8073 (Dense: 0.5323 | BM25: 23.9847)
```text
Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống 
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7146 (Dense: 0.6028 | BM25: 17.6467)
```text
	+ Collector: standalone process nhận data từ SDK, làm transform, và sau đó forward tới backend

**Architecture choice — Agent layer:**

| Tool | Đặc điểm | Khi nào dùng |

| :--- | :--- | :--- |
```

---

## eval_test_v3_034 (Tags: txt, lexical-anchor-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 8
**Query:** Hệ thống lưu trữ log nào có tốc độ tìm kiếm văn bản cực mạnh nhưng tốn nhiều RAM?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9277 (Dense: 0.5556 | BM25: 34.3485)
```text
**vì chi tiết đầy đủ**(order ID, user ID, stack trace) --> **Log** trở nên nặng --> dẫn đến **chi phí lưu trữ** cao --> ngoài ra quá trình **query** sẽ phức tạp do tracing 

==> ```Nhiều chi tiết → Nặng → Tốn tiền lưu & Khó tìm kiếm```
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8852 (Dense: 0.5702 | BM25: 31.4740)
```text
==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng
```

#### Rank 3: ❌ DISTRACTOR
Score: 0.7223 (Dense: 0.5208 | BM25: 23.6390)
```text
nặng (heavy)** và gây tốn **chi phí lưu trữ**.
```

### First Target Chunk (Found at Rank 8)
Score: 0.5659 (Dense: 0.5074 | BM25: 15.0866)
```text
| | **TimescaleDB** | PostgreSQL extension, SQL-friendly. | Chậm hơn các TSDB chuyên dụng (purpose-built). |

| **Document/Search Store (Log)** | **Elasticsearch** | Full-text search mạnh, query linh hoạt. | Chi phí đắt đỏ (RAM-heavy). |
```

---

## eval_test_v3_035 (Tags: txt, semantic-heavy)
**Status:** Critical Failure (Zero-Hit / Rank >= 3)
**First Hit Rank:** 3
**Query:** Điều gì xảy ra với pipeline khi một dịch vụ bất ngờ đổi định dạng log?
**Target Blocks:** 1

### Top 3 Retrieved Chunks (Distractors vs Targets)
#### Rank 1: ❌ DISTRACTOR
Score: 0.9415 (Dense: 0.5087 | BM25: 24.1259)
```text
### 1.2. **Log**- trả lời câu hỏi **vì sao sai?**

**Định nghĩa**: text record, mỗi record là 1 event xảy ra trong system.
```

#### Rank 2: ❌ DISTRACTOR
Score: 0.8171 (Dense: 0.5602 | BM25: 17.8607)
```text
tự động thích ứng với các thay đổi mà không làm gãy đổ (**break**) pipeline của các bên liên quan.
```

#### Rank 3: ✅ TARGET
Score: 0.8143 (Dense: 0.6044 | BM25: 16.6597)
```text
## 4. **Schema registry & Data contract**

**Vấn đề real-world**: 1 service X được deploy version mới --> log format của X thay đổi, và pipeline Y đang parse log mới của X --> đẫn đến break. mãi tới khi anomaly detection bắt đầu false alarm
```

---
