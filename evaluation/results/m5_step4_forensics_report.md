# M5 Step 4: Strong Anchor Forensics Report

This report investigates 13 Strong Anchor cases where the Baseline correctly ranked the target at #1, but the Cross-Encoder (BGE) may have altered the ranking.

**Extraction Logic:** Union(Target chunks, Baseline Top-10, BGE Top-10).

### Case: eval_test_v3_001
**Query**: Will hosting my web app on Amazon automatically make it resilient to failures?

**Candidate Pool:** 35 chunks
**Target chunks:** 2
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:98041... | YES | 1 | 1 | 0.5895 | 11.7398 | 0.9800 | 0.1534 | onstructs such as availability zones, elastic IP addresses, and snapshots to design high availability and fault tolerant applications. Remember hosting an application on the cloud does not make it fault-tolerant or highly available. |
| sha256:7c471... | YES | 31 | 2 | 0.5879 | 2.1764 | 0.4126 | 0.0162 | This section introduces configuring AWS infrastructure to support high availability for our application. Most of Amazon's high-level services are designed for high availability and fault tolerance such as Elastic Load Balancer (ELB), Simple Storage Service |
| sha256:7bdb3... | NO | 2 | 3 | 0.5363 | 9.9825 | 0.8340 | 0.0154 | In such environments, it is important that tasks and processes be highly repeatable, resilient, flexible, and robust. Amazon provides numerous tools, APIs, and services to enable you to create highly automated DevOps pipelines. These pipelines can help you |
| sha256:327e1... | NO | 34 | 4 | 0.5211 | 2.0072 | 0.3497 | 0.0132 | only for the resources that are healthy and reachable from the outside world, the end users can be routed away from a failed application. Amazon Route 53 health checks are conducted from within each AWS region to check whether your application is reachable |
| sha256:a71ea... | NO | 15 | 5 | 0.6147 | 4.8697 | 0.5933 | 0.0123 | • Fault tolerant: The application should be coded to handle cloud services' related failures to the extent possible. |
| sha256:d6fa6... | NO | 16 | 6 | 0.5836 | 5.1789 | 0.5869 | 0.0101 | toring. Other guidelines might recommend building stateless services and storing all data on Amazon S3 and leveraging services such as SQS based on assuming that all instances are temporary or will fail sooner or later. You might also want to take snapshot |
| sha256:d242f... | NO | 25 | 7 | 0.5784 | 3.6650 | 0.4932 | 0.0025 |  rebooted by the cloud platform. There can also be unexpected application failures. In all cases, the design goal should be to handle such error conditions gracefully and minimize any impact to the user experience. |
| sha256:6c903... | NO | 3 | 8 | 0.4967 | 9.1862 | 0.7555 | 0.0015 | ese would include DNS or domain services, load balancers, web and application servers, database servers, application services-related failures, and data center-related failures. You will need to ensure you have a mitigation strategy for each of these types |
| sha256:0c050... | NO | 30 | 9 | 0.5674 | 2.7793 | 0.4321 | 0.0014 | web application backups 35 design for failure 35 disaster recovery 35 fault tolerant 35 high availability 35 operational cost 34 replication 35 scalability application 35 scalability cloud infrastructure 35 security application 35 security cloud infrastruc |
| sha256:1f806... | NO | 35 | 10 | 0.5280 | 1.6049 | 0.3314 | 0.0008 | • Avoid single points of failure. Plan to distribute your services across multiple regions and zones (that is, different data centers in the same region), and also implement a robust failover strategy. This will minimize the chances of an application outag |
| sha256:5815f... | NO | 8 | 12 | 0.3574 | 10.0118 | 0.6942 | 0.0005 | ° Auto Minor Version Upgrade: Amazon RDS will automatically update the DB instance only for minor updates. Select Yes from the dropdown. |
| sha256:4d204... | NO | 4 | 15 | 0.5382 | 8.5860 | 0.7527 | 0.0003 | web application on EC2 instances behind ELBs and use Amazon CloudFront to deliver your entire site. |
| sha256:1f7a1... | NO | 9 | 16 | 0.5045 | 7.5623 | 0.6655 | 0.0002 | backups. If your data volumes are on a terabyte scale, then Amazon also provides a facility where you can ship your data on portable storage media, and Amazon will use their high-speed internal network to load it on S3 for you. This is often a more economi |
| sha256:01e40... | NO | 7 | 17 | 0.5667 | 7.4259 | 0.7066 | 0.0002 | Amazon Web Services: Migrating your .NET Enterprise Application<br><br>ISBN: 978-1-84968-194-0 Paperback: 336 pages Evaluate your Cloud requirements and successfully migrate your .NET Enterprise application to the Amazon Web Services Platform |
| sha256:55807... | NO | 6 | 19 | 0.5677 | 7.5612 | 0.7154 | 0.0001 | Amazon Simple Queue Service (Amazon SQS) 46 Amazon Virtual Private Cloud (Amazon VPC) 46<br><br>Amazon Web Services (AWS) about 1, 8 components 43 URL 6 using, for disaster recovery 132 |
| sha256:42377... | NO | 5 | 25 | 0.4567 | 9.0701 | 0.7170 | 0.0000 | 1. Apply your current ASP.NET knowledge to make your Web APIs more secure and comply to the global standard in order to make your service RESTful. |
| sha256:af1f0... | NO | 10 | 28 | 0.3813 | 8.7897 | 0.6407 | 0.0000 | Via the Amazon web console<br><br>There is another option to create the CloudFormation stack via the CloudFormation dashboard. Navigate to the CloudFormation dashboard from the Amazon web console and click on Create Stack. |

---

### Case: eval_test_v3_004
**Query**: What should I enter for the SSL certificate label?

**Candidate Pool:** 32 chunks
**Target chunks:** 2
**Baseline Target Rank:** 1
**BGE Target Rank:** 2

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:f8034... | NO | 3 | 1 | 0.4750 | 15.6515 | 0.7327 | 0.1475 | ----You are about to be asked to enter information that will be incorporated into your certificate request. What you are about to enter is what is called a Distinguished Name or a DN. There are quite a few fields but you can leave some blank For some field |
| sha256:a7638... | YES | 1 | 2 | 0.6489 | 20.1998 | 0.9860 | 0.0183 | 3. The next step is to associate the SSL certificate with the ELB. Click on Change under SSL Certificate. The following are the properties:<br><br>° Certificate Type: Make sure the radio button Upload a new SSL<br><br>Certificate is selected. |
| sha256:ab688... | YES | 2 | 3 | 0.5872 | 20.6830 | 0.9569 | 0.0112 | ° Certificate Name: Enter the name of the certificate for your reference; |
| sha256:7f8bc... | NO | 14 | 4 | 0.3554 | 11.0411 | 0.5153 | 0.0104 | ° Description: The description can be up to 256 characters long and should tell users what the key will be used to encrypt. |
| sha256:3ee16... | NO | 6 | 5 | 0.6092 | 9.5466 | 0.6492 | 0.0047 | While transporting data over HTTP, security is provided by an SSL. SSL is widely used on the Internet to authenticate a service to a client, and then to provide encryption to the transport channel. Configuring the ELB to accept SSL certificates will secure |
| sha256:57c33... | NO | 4 | 6 | 0.5254 | 13.6111 | 0.7086 | 0.0037 | • SSL Termination: ELB provides SSL termination that saves precious CPU cycles encoding and decoding SSL within your EC2 instances attached to the ELB. All it requires is a X.509 certificate to be configured within the ELB. It is optional; you still have a |
| sha256:e89e3... | NO | 8 | 7 | 0.3866 | 12.5872 | 0.5820 | 0.0034 | t layer (TCP/SSL) and the application layer (HTTP/HTTPS). Our Apache Tomcat server listens on port 8080; we enter port 8080 both on the Load Balancer Port and the Instance Port. The acceptable ports for both HTTPS/SSL and HTTP/TCP connections are 80 and 44 |
| sha256:1e430... | NO | 16 | 8 | 0.4093 | 8.5305 | 0.4802 | 0.0020 | • Application security: The application should use an encrypted channel for communications. All the confidential data should be stored in an encrypted format. All the files at rest should be stored in an encrypted format. |
| sha256:c41ab... | NO | 13 | 9 | 0.5190 | 7.1765 | 0.5175 | 0.0015 | re transport channel is created between the browser and the ELB. If you own a domain then you can access www.startssl.com to obtain free SSL certificates. |
| sha256:02c70... | NO | 18 | 10 | 0.5847 | 3.2578 | 0.4497 | 0.0013 | Generating self-signed certificates<br><br>OpenSSL is used to create the keys and certificates and to make sure you have it installed on your development machine. The example shown here is for a Linux machine. From the command line, execute the following command: |
| sha256:7edcd... | NO | 7 | 11 | 0.5824 | 9.2454 | 0.6218 | 0.0011 | Configure ELB for SSL |
| sha256:76791... | NO | 5 | 16 | 0.5796 | 10.8360 | 0.6660 | 0.0006 |  use a commercial CA to sign a certificate but instead use a self-signed certificate. As a result, the browser will not be able to verify the self-signed digital certificate or the authenticity of the website and will generate an exception. However, a secu |
| sha256:0dd1c... | NO | 10 | 17 | 0.6311 | 6.3964 | 0.5731 | 0.0006 | third-party security solutions<br><br>using 147<br><br>transport security about 158 ELB, configuring for SSL 160, 161 self-signed certificates, generating 159 |
| sha256:db651... | NO | 9 | 20 | 0.5292 | 8.9586 | 0.5763 | 0.0003 | about 44, 88 configuring, for SSL 160, 161 Control Service 91 Load Balancer 91 SSL Termination 91 |

---

### Case: eval_test_v3_005
**Query**: How can I verify if a group of small servers matches the performance of a single xlarge machine?

**Candidate Pool:** 36 chunks
**Target chunks:** 6
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:fb49a... | YES | 1 | 1 | 0.7139 | 13.4830 | 0.8503 | 0.8799 | At this stage, you should provision multiple smaller instances (from the same families) that match the xlarge instance's compute power and conduct the same load tests. This is done to check whether we can achieve the same performance, |
| sha256:83bb4... | NO | 4 | 2 | 0.5574 | 13.4122 | 0.6997 | 0.0272 | In the same way, we can verify the scaling in by the auto scaling group, that is, removal of an EC2 instance when the average CPU utilization of the EC2 instances falls below 30 percent for a period of 20 minutes. This can be achieved by ending the bc task |
| sha256:e0e3a... | YES | 5 | 3 | 0.4296 | 15.5793 | 0.6624 | 0.0105 | list two instance type—a CPU optimized (say, c3.xlarge) and a general purpose (m3.xlarge) instance type. Typically, you should choose a general purpose and a special purpose instance type for comparison purposes. In order to conduct the performance analysi |
| sha256:48fb6... | NO | 21 | 4 | 0.5673 | 6.8716 | 0.4571 | 0.0047 | The next step is to test the auto scaling group. It should add an instance to when the CPU Utilization is greater than 60 percent for 5 minutes and remove an EC2 instance if the CPU Utilization falls in less than 30 percent for 20 minutes. The easiest way  |
| sha256:dff15... | NO | 36 | 5 | 0.5359 | 1.7936 | 0.2318 | 0.0029 | to test this is to load the CPU for more than 5 minutes and check whether an EC2 instance is added. |
| sha256:5afe5... | NO | 3 | 6 | 0.4860 | 15.2471 | 0.7029 | 0.0026 | caling group starts, it starts with the minimum number of instances. To verify that the auto scaling group is working as configured, copy the DNS name of the elastic load balancer as described in step 9 in Creating Elastic Load Balancer. In this case, it i |
| sha256:eec05... | YES | 6 | 7 | 0.5971 | 11.3283 | 0.6569 | 0.0020 | You should then do a few tests to analyze the performance of the shortlisted instances against increasing loads. It is a good idea to understand the upper limit of these instances in terms of number of users or throughput they can support. |
| sha256:1627a... | NO | 2 | 8 | 0.5721 | 14.6964 | 0.7631 | 0.0014 | that run inside the auto scaling group. This number typically depends on the load the application is expecting and how many requests a single instance can serve with accepted latencies. Before deploying to production, it is good practice to benchmark the a |
| sha256:6f0a4... | YES | 29 | 9 | 0.5451 | 5.1874 | 0.3713 | 0.0010 | s, create a set of test cases to test a few scenarios in your application. Monitor the CPU utilization for these instances at different loads, say 1000, 2000, and 3000 users. Increase the load to a point where you max out on the CPU. It is very likely that |
| sha256:0a1de... | NO | 12 | 10 | 0.5100 | 10.5993 | 0.5465 | 0.0009 | The simplest guideline here is to never run a single instance in a production environment. The simplest approach to improving greatly from a single server scenario is to spin up multiple EC2 instances and stick an ELB in front of them. The incoming request |
| sha256:a8821... | NO | 10 | 13 | 0.4955 | 11.5801 | 0.5706 | 0.0003 | me as you auto scale the number of servers or even replace a fleet of servers behind it. This can also help you systematically rollout new versions of your application behind the ELB with no service interruption to your customers. You can also deploy your  |
| sha256:aebe5... | YES | 34 | 19 | 0.5292 | 3.8462 | 0.3045 | 0.0001 |  you will hit max CPU utilization at different loads for each of the chosen instances. |
| sha256:e2b07... | NO | 9 | 21 | 0.5961 | 9.8118 | 0.5976 | 0.0001 | Sometimes running multiple instances is cost prohibitive for smaller organizations (very common for start ups new to the cloud). If you want to run a single instance, then ensure you still configure for auto scaling. Set the minimum and maximum number of s |
| sha256:6991c... | NO | 7 | 22 | 0.3166 | 17.3687 | 0.6245 | 0.0001 | es. The decision on how many availability zones to host the application zone depends on how critical the application is and the economics of hosting. This removes the SPOF if using a single AZ. |
| sha256:d3ec0... | YES | 24 | 23 | 0.5459 | 7.1162 | 0.4463 | 0.0001 | For example, let's assume you want to select EC2 instances for your web servers. These web servers proxy API calls to the application servers, that is, handle CPUintensive traffic and support heavy payloads. Based on these requirements, let's say you short |
| sha256:d986c... | NO | 8 | 35 | 0.4619 | 13.3955 | 0.6088 | 0.0000 | n in the cloud world. After a data update, if your application can tolerate a few seconds delay before the update is reflected across all replicas of the data, then eventual consistency can lead to better scalability and performance. |

---

### Case: eval_test_v3_006
**Query**: What protocol is used to access files stored in S3 containers from a browser?

**Candidate Pool:** 33 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:d5105... | YES | 1 | 1 | 0.5781 | 17.5549 | 0.8996 | 0.9385 | Amazon S3<br><br>Amazon S3 is a highly durable and distributed data store. Using a web services interface, you can store and retrieve large amounts of data as objects in buckets (containers). The stored objects are also accessible from the web via HTTP. |
| sha256:24149... | NO | 7 | 2 | 0.5961 | 8.9192 | 0.5471 | 0.4087 | be stored in S3. Even if the EC2 instances fails, the uploaded file is not lost and another EC2 instance can process if required. It is good practice to store all the static assets such as images/scripts of the application into S3 as it takes the load off  |
| sha256:6f989... | NO | 8 | 3 | 0.4818 | 11.2447 | 0.5468 | 0.3110 | ## Usage Example<br><br>Below is a Python snippet to access S3:<br><br>```python<br>import boto3<br><br>s3 = boto3.client('s3')<br>response = s3.list_buckets()<br>```<br><br>> Note: Always secure your AWS credentials. |
| sha256:ccd31... | NO | 31 | 4 | 0.5013 | 4.0492 | 0.2569 | 0.1376 | s HIPPA, PCI DSS,SOC1, 2, 3, and so on. In this section, walkthroughs to secure the data-at-rest for RDS and S3 are presented. |
| sha256:40d46... | NO | 2 | 5 | 0.5741 | 11.7772 | 0.6498 | 0.0991 | Static content or files include CSS, HTML, images, and so on that are stored in Amazon S3 (and not on your web server instance). This can reduce the load on your web servers and improve the efficiency of maintaining content (by storing at one S3 location)  |
| sha256:267c0... | NO | 32 | 6 | 0.5266 | 3.4842 | 0.2548 | 0.0756 |  (S3), Simple Queue Service (SQS), Simple Notification Service (SNS), Relation Database Service (RDS), Route 53 a dynamic DNS service, and CloudWatch. The infrastructure services such as Elastic Cloud Compute (EC2) and Elastic Block Storage (EBS) provide c |
| sha256:e2f58... | NO | 25 | 7 | 0.5399 | 4.7551 | 0.3206 | 0.0413 | Here, we show you two ways by which you can achieve server-side encryptionone, by using the S3 console and the other by uploading a file to S3 via Java AWS SDK. We will not go through the client-side encryption. |
| sha256:4db67... | NO | 20 | 8 | 0.5551 | 5.3507 | 0.3592 | 0.0342 | • Server-Side Encryption: Amazon S3 encrypts your object before saving, and decrypt's it when you download the objects. The encryption and decryption process is totally transparent and seamless. Amazon S3 can be configured in multiple ways for the encrypti |
| sha256:e45ea... | NO | 4 | 9 | 0.5722 | 10.8171 | 0.6072 | 0.0222 | • Simple Storage Service (S3): S3 is a highly available service for storing static assets. Amazon S3 is designed for 99.99 percent availability and 99.999999999 percent of durability of objects over a year. All the files uploaded to the application should  |
| sha256:80a86... | NO | 29 | 10 | 0.5140 | 3.9886 | 0.2654 | 0.0170 | • Client-Side Encryption: The client is responsible for the encryption of the object before uploading it to Amazon S3, and for decrypting the object after it has been downloaded. The client is responsible for the encryption/ decryption process and manageme |
| sha256:c8198... | NO | 9 | 11 | 0.3998 | 12.5687 | 0.5319 | 0.0094 | ° Click on the Save button. This will configure ELB to support the SSL protocol. Test the URL on the browser using the HTTPS protocol. Let's take a look at the following screenshot: |
| sha256:eb737... | NO | 6 | 14 | 0.6935 | 7.2806 | 0.5619 | 0.0074 | Here is a code snippet that will upload code from your application and instruct S3 to encrypt the file; this is not the same as a client encrypting the file and uploading it to S3, since the code only passes the location of the encryption key within the KM |
| sha256:f7e59... | NO | 3 | 24 | 0.6554 | 10.0656 | 0.6475 | 0.0024 | The easiest way to secure data on S3 is via the S3 console. Select the bucket where the file is to be uploaded, click on the Upload button; this presents a pop up window to upload files, as shown in the following screenshot: |
| sha256:6025c... | NO | 5 | 25 | 0.5456 | 11.3373 | 0.6063 | 0.0022 | sh these reports as CSV files and store them in your S3 bucket. |
| sha256:1e430... | NO | 10 | 31 | 0.4523 | 11.4928 | 0.5317 | 0.0001 | • Application security: The application should use an encrypted channel for communications. All the confidential data should be stored in an encrypted format. All the files at rest should be stored in an encrypted format. |

---

### Case: eval_test_v3_008
**Query**: What is the best way to allow SaaS users to add custom fields without altering the core database structure?

**Candidate Pool:** 36 chunks
**Target chunks:** 3
**Baseline Target Rank:** 1
**BGE Target Rank:** 3

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:233aa... | NO | 2 | 1 | 0.5514 | 14.3725 | 0.8869 | 0.1591 |  you don't change your schema for a tenant so much that your product no longer fits into the SaaS model. But you do want to bake in sufficient flexibility and extensibility to handle custom data requirements of your customers (without impacting subsequent  |
| sha256:4bf4c... | NO | 5 | 2 | 0.5206 | 11.9682 | 0.7790 | 0.0270 | You will need to design your database schema carefully for providing custom extensions to your tenants, as this can have a ripple effect on the application code and the user interface. |
| sha256:103c7... | YES | 1 | 3 | 0.5395 | 16.6796 | 0.9616 | 0.0172 | for all the extra fields in the table. Alternatively, you can introduce an additional column for the table name, to have a common table describing all custom fields (for each tenant) across all the tables in the schema. |
| sha256:2c230... | NO | 3 | 4 | 0.5610 | 13.3156 | 0.8556 | 0.0114 | We can define a separate database schema for each of the tenants (within the same database server instance) for applications having a limited number of database tables. This approach is relatively simple to implement, and offers flexibility for custom tabl |
| sha256:79472... | NO | 22 | 5 | 0.5435 | 6.6160 | 0.6024 | 0.0071 | Having a rigid database schema will not work for you across all your customers. Customers have their specific business rules and supporting data requirements. They will want to introduce their own customizations to the database schema. You must ensure that |
| sha256:cee84... | YES | 4 | 6 | 0.5947 | 12.1738 | 0.8379 | 0.0069 | One approach to achieve extensibility in the database schema is to preallocate a bunch of extra fields in your tables, which can then be used by your customers to implement their own business requirements. All these fields can be defined as string or varch |
| sha256:4eb2d... | NO | 14 | 7 | 0.4887 | 9.2955 | 0.6606 | 0.0032 | A variation on the preceding two approaches is to define an extra field per table, and store all custom name-value pairs per tenant in an XML or JSON format, as shown in the following figure: |
| sha256:dda0f... | NO | 8 | 8 | 0.4200 | 12.1665 | 0.7161 | 0.0027 | ° During the development phase, we need to have direct access to databases from our development environment. This makes it is easy to change, monitor the database without logging in to the EC2 instance, or setting up complex SSH tunnels. In addition, there |
| sha256:b7892... | NO | 15 | 9 | 0.2781 | 13.0862 | 0.6505 | 0.0015 | Regardless of the approach, it is a good practice to encrypt sensitive data fields in your cloud database and storage. Encryption ensures that the data remains secure, even if a nonauthorized user accesses it. This is more critical for shared database/ sch |
| sha256:9f86f... | NO | 13 | 10 | 0.4990 | 9.2112 | 0.6648 | 0.0015 | • In the Software as a Service(SaaS) model, typically, third-party providers using a subscription model provide end-user applications to their customers. The customers might have some administrative capability at the application level, for example, to crea |
| sha256:c94a5... | YES | 18 | 15 | 0.5934 | 6.2800 | 0.6250 | 0.0005 | ar fields. You also create an additional metadata table to further define a field label, data type, field length, and so on for each of these fields on a per tenant basis. You can choose to create a metadata table per field or have a single metadata table  |
| sha256:504fe... | NO | 7 | 17 | 0.3288 | 14.0427 | 0.7202 | 0.0005 |  stored in the database rows is in plain text; the application doesn't need the encryption key to decrypt the data. If an unauthorized user gets a hold of the database volume, it will be of no real value to him, since it is encrypted, and without the encry |
| sha256:0adf3... | NO | 10 | 18 | 0.3479 | 13.0331 | 0.6971 | 0.0004 | he master database is synchronously replicated to the slave. Overall, the architecture represents a simple way to achieve a highly scalable and highly available application in a cloud environment. |
| sha256:3d441... | NO | 9 | 19 | 0.3385 | 13.3698 | 0.7027 | 0.0003 |  is the added advantage of not having to install a local MySQL server on your development machine. For production environments, it is recommended to allow database access only from within the VPC. Select Anywhere from Source and 0.0.0.0/0 to allow access f |
| sha256:93be3... | NO | 6 | 35 | 0.3750 | 13.3039 | 0.7257 | 0.0000 | The template JSON file includes the following sections; only the Resources section is mandatory while the rest are all optional.<br><br>The structure of a CloudFormation script consists of the following:<br><br>{<br><br>} |

---

### Case: eval_test_v3_009
**Query**: What port number needs to be configured when setting up the secure load balancer protocol?

**Candidate Pool:** 33 chunks
**Target chunks:** 6
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:8b687... | YES | 1 | 1 | 0.7288 | 26.0199 | 1.0000 | 0.9746 | ° From Load Balancer Protocol, select the HTTPS protocol ° Set Load Balancer Port to 8443; this is the port we added to our<br><br>security group in our previous step<br><br>° From Instance Protocol, select HTTP; this is the protocol between |
| sha256:15656... | YES | 7 | 2 | 0.5434 | 15.7721 | 0.5963 | 0.9434 | The next step is to configure the ELB to support SSL. Here, the SSL connection will be terminated at the load balancer. The connection between the ELB and your EC2 instance will be unsecured. The standard HTTPS port is 443; instead, we use port 8443, as us |
| sha256:584a1... | YES | 5 | 3 | 0.5394 | 17.7479 | 0.6421 | 0.9082 | 2. The next step is to add load balancer protocol (HTTPS) and listener port and configure the private and the public key on the ELB. From the EC2 dashboard, navigate to Load Balancers, click on the Listeners tab, and then click on Edit: |
| sha256:37345... | YES | 19 | 4 | 0.6019 | 8.5942 | 0.4651 | 0.8984 | 1. The first step is to configure the security group to add a custom TCP rule to accept data on port 8443. From the EC2 dashboard, navigate to Load Balancers, click on the Security tab, and then click on Security Group ID associated with the ELB. In our ex |
| sha256:dc4aa... | NO | 13 | 5 | 0.6554 | 8.2906 | 0.5006 | 0.8774 | "LoadBalancerPort":"8080", "InstancePort":"8080", "Protocol":"HTTP" }, {<br><br>"LoadBalancerPort":"8443", "InstancePort":"8443", "Protocol":"TCP"<br><br>}<br><br>], "ConnectionDrainingPolicy":{<br><br>"Enabled":"true","Timeout":"60"<br><br>}, "SecurityGroups":[{ |
| sha256:16ee4... | NO | 3 | 6 | 0.6122 | 22.1126 | 0.8091 | 0.8428 | the ELB and the EC2 instances ° Set Instance Port to 8080; this is the port that the Tomcat is listening on ° From Load Balancer Protocol, delete the HTTP protocol as it is not<br><br>needed anymore |
| sha256:1afc4... | NO | 2 | 7 | 0.7120 | 19.5428 | 0.8256 | 0.7563 | 3 and between 1024-65535. Select HTTP as the protocol on both Load Balancer Protocol and Instance Protocol. |
| sha256:e89e3... | NO | 6 | 8 | 0.5829 | 15.1920 | 0.6137 | 0.6772 | t layer (TCP/SSL) and the application layer (HTTP/HTTPS). Our Apache Tomcat server listens on port 8080; we enter port 8080 both on the Load Balancer Port and the Instance Port. The acceptable ports for both HTTPS/SSL and HTTP/TCP connections are 80 and 44 |
| sha256:db651... | NO | 16 | 9 | 0.6374 | 8.4049 | 0.4890 | 0.3745 | about 44, 88 configuring, for SSL 160, 161 Control Service 91 Load Balancer 91 SSL Termination 91 |
| sha256:92783... | NO | 25 | 10 | 0.5401 | 8.0384 | 0.4016 | 0.0646 | • Public subnets at 172.31.16.0/20 and 172.31.48.0/20 hosting the EC2 instances in the auto scaling group for the application. It accepts HTTP and HTTPS connections from the load balancer security group. The two subnets are in two different availability zo |
| sha256:39a0f... | YES | 20 | 13 | 0.5840 | 9.1337 | 0.4641 | 0.0129 | 443 port, as shown in the following screenshot: |
| sha256:56ed1... | YES | 21 | 14 | 0.6098 | 8.1118 | 0.4595 | 0.0105 | ample, this is sq-EC2WebSecurityGroup. The click action will navigate to the Security Groups pane. Click on Edit in the Inbound tab to add the TCP rule and accept data on port 8443. Delete Custom TCP Rule on Port Range 8080 as it is being replaced by the 8 |
| sha256:f316a... | NO | 8 | 15 | 0.5578 | 14.7977 | 0.5837 | 0.0058 | ° Load Balancer name: This is a name that uniquely identifies a load balancer. This name will be a part of the public DNS name of your load balancer. |
| sha256:5afe5... | NO | 9 | 16 | 0.4417 | 16.6694 | 0.5367 | 0.0053 | caling group starts, it starts with the minimum number of instances. To verify that the auto scaling group is working as configured, copy the DNS name of the elastic load balancer as described in step 9 in Creating Elastic Load Balancer. In this case, it i |
| sha256:bcc48... | NO | 4 | 20 | 0.6720 | 14.9792 | 0.6801 | 0.0045 | ° Database Port: This is the default MySQL port. Do not change the default port number, which is set to 3306. |
| sha256:36f15... | NO | 10 | 25 | 0.5917 | 10.8454 | 0.5128 | 0.0026 | ° Ping Port: This is the port to connect to with the instance. Enter 8080, which is the default port of our Apache Tomcat server. |

---

### Case: eval_test_v3_011
**Query**: Which AWS service is used to create users and assign permissions?

**Candidate Pool:** 33 chunks
**Target chunks:** 3
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:1d904... | YES | 1 | 1 | 0.6675 | 18.0925 | 0.9325 | 0.9976 | The AWS IAM service is central to implementing security for your applications on the AWS cloud. Some of the main activities and best practices for AWS IAM are listed as follows:<br><br>• Use IAM to create users, groups, and roles and assign permissions. |
| sha256:1c822... | NO | 4 | 2 | 0.7095 | 12.7164 | 0.7650 | 0.9004 | AWS Identity and Access Management (IAM) enables you to you to control access to AWS services and resources. You can create users and groups with unique security credentials and manage permissions for each of these users. You can also define IAM roles so t |
| sha256:fce3c... | NO | 3 | 3 | 0.7022 | 13.3568 | 0.7832 | 0.8667 | AWS Identity and Access Management (IAM) is a web service that enables you to manage users, groups, and user permissions within the AWS infrastructure. This allows for central control of users, groups, user access, and security credentials. As there are a  |
| sha256:d641e... | NO | 5 | 4 | 0.7370 | 11.8140 | 0.7525 | 0.5498 | 4. Next, we will assign permissions for the selected role. Select the Power User Access option. For now, we do not have any credential scoping. Read and write permissions for all AWS services are granted to the selected role. Permissions to the role can be |
| sha256:e1572... | NO | 7 | 5 | 0.6358 | 10.1942 | 0.6148 | 0.5200 | A role is a set of permissions that grant access to AWS resources. Roles are not associated with any user or group but instead are assumed by a trusted entity which can be an IAM user, application, or AWS service such as EC2. The difference between an IAM  |
| sha256:6724f... | NO | 11 | 6 | 0.6729 | 7.3538 | 0.5377 | 0.3979 | 3. The next step is to grant permissions to the selected AWS services. Click on the Amazon EC2 role type, as shown in the following screenshot: |
| sha256:dbfb9... | NO | 6 | 7 | 0.6386 | 12.0029 | 0.6841 | 0.2932 | Role is a set of permissions that grant access to AWS services. Roles are independent of users or groups. You will need a strategy to distribute and rotate the credentials to your EC2 instances; especially, the ones which AWS creates on your behalf, for ex |
| sha256:565d8... | NO | 26 | 8 | 0.7483 | 2.3070 | 0.4080 | 0.2625 | Using AWS services |
| sha256:e6628... | YES | 2 | 9 | 0.7079 | 14.8081 | 0.8415 | 0.2186 | • Manage permissions using groups. You assign permissions to groups and then assign individuals to them. While assigning permissions to groups, always follow the principle of granting least privilege. AWS provides several policy templates for each of their |
| sha256:eb38a... | YES | 8 | 10 | 0.7555 | 7.3049 | 0.5993 | 0.2175 |  services. Use these policy templates as they are a great starting point for setting up the permissions for AWS services. For example, you can quickly set up permissions for groups that have read-only access to S3 buckets. |
| sha256:df6a4... | NO | 9 | 18 | 0.6371 | 8.8944 | 0.5675 | 0.0396 | • Managing Access for Federated Users: Federated users are users that are managed outside IAM. Typically, these are users in your corporate directory. IAM allows for granting access to the AWS resources to the federated users; this is achieved by granting  |
| sha256:7da9c... | NO | 10 | 24 | 0.5246 | 11.1124 | 0.5637 | 0.0063 | 4. The next step is to assign rights to the IAM users/roles. Usage rights in this context means to encrypt and decrypt data using this key. It is a good practice to assign rights to roles instead of users, as it helps to centralize user management around r |

---

### Case: eval_test_v3_015
**Query**: Which cloud service model requires the customer to handle the most administration overhead for virtual servers?

**Candidate Pool:** 36 chunks
**Target chunks:** 4
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:b3e80... | YES | 1 | 1 | 0.7721 | 14.8328 | 0.9127 | 0.2810 | onal in-premise models and the virtual server provisioning models (typically offered by data center outsourcers). The onus of administering these resources rests largely with the customer. |
| sha256:d4c52... | NO | 7 | 2 | 0.6676 | 12.9432 | 0.7687 | 0.1415 | A private cloud provides many of the same benefits of a public cloud but the services and data are managed by the organization or a third-party, solely for the customer's organization. Usually, private cloud places increase administrative overheads on the  |
| sha256:2a285... | NO | 5 | 3 | 0.7289 | 12.7516 | 0.7989 | 0.0291 | • Cloud service providers should enable a pay-as-you-go model, where customers are charged based on the type and quantum of resources they consume<br><br>Some of the implications of choosing to use the cloud for your computing needs are as follows: |
| sha256:46d3e... | NO | 10 | 4 | 0.5630 | 14.0746 | 0.7509 | 0.0086 | In this chapter, we described the main AWS services that are most commonly used for AWS cloud applications development. These included compute, storage and content delivery, databases, networking, application, administration, and deployment services. Next, |
| sha256:48b4a... | YES | 3 | 5 | 0.6227 | 15.1317 | 0.8322 | 0.0071 | From an infrastructure perspective, the customer does not manage or control the underlying cloud infrastructure in all three service models. |
| sha256:04234... | NO | 21 | 6 | 0.3837 | 13.3869 | 0.6106 | 0.0065 | An Amazon Machine Image (AMI) is a master image for the creation of virtual servers on the Amazon cloud. An AMI contains instruction to launch an EC2 instance; this includes an operating system, machine architecture 32 bit or 64 bit, software stack for you |
| sha256:553db... | NO | 26 | 7 | 0.6889 | 7.6874 | 0.5623 | 0.0063 | In recent times there has been a huge shift in the way organizations manage their cloud environments and applications. This is in response to the ease of operating in the cloud, availability of infrastructure on-demand, and cloud-based PaaS services that c |
| sha256:f5f98... | NO | 23 | 8 | 0.7367 | 7.2011 | 0.5717 | 0.0053 |  handle your infrastructure requirements including provisioning your technology stack, performing deployments dynamically with zero downtime, and supporting your end customers at scale. Some of the major AWS services in these areas are AWS CloudFormation,  |
| sha256:8899c... | YES | 4 | 9 | 0.4886 | 16.3532 | 0.7999 | 0.0032 |  mode. In contrast, the provider provisions the application for the customer for more specialized applications. The provider also hands over certain application administrative tasks to the customer's application administrator (in most cases, this is limite |
| sha256:7853b... | NO | 22 | 10 | 0.6682 | 9.0694 | 0.6072 | 0.0029 | "Cloud computing is a model for enabling convenient, on-demand network access to a shared pool of configurable computing resources (e.g., networks, servers, storage, applications, and services) that can be rapidly provisioned and released with minimal mana |
| sha256:6363c... | YES | 6 | 14 | 0.4370 | 16.9215 | 0.7915 | 0.0015 | • In Platform as a Service(PaaS), the service provider makes certain core components, such as databases, queues, workflow engines, e-mails, and so on, which are available as services to the customer. The customer then leverages these components for buildin |
| sha256:f194c... | NO | 2 | 16 | 0.7122 | 14.1382 | 0.8464 | 0.0009 | Most cloud providers maintain a distributed set of servers in multiple data centers around the globe. These servers are used as a Content Delivery Network (CDN) to serve content to end users from locations closest to them. This service is made available to |
| sha256:9ae1c... | NO | 8 | 17 | 0.6992 | 12.4264 | 0.7668 | 0.0006 | This tiered architecture on the cloud supports auto scaling and load balancing of web servers and application servers. Further, it also implements a master-slave database model across two different zones or data centers (connected with high speed links). T |
| sha256:6a1c0... | NO | 9 | 24 | 0.6059 | 13.7825 | 0.7654 | 0.0004 | o handle full production loads. In this configuration, you would deploy the web servers and application servers across multiple AZs in your primary region while the standby servers need not be launched in your secondary region until you actually need them. |

---

### Case: eval_test_v3_020
**Query**: What does the section right before getting started with the AWS interface cover?

**Candidate Pool:** 36 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:9e881... | YES | 1 | 1 | 0.6436 | 21.6780 | 0.9490 | 0.3523 | We would like to conclude our introduction to cloud computing by getting you started on AWS, right away. The next two sections will help you set up your AWS account and familiarize you with the AWS management console. |
| sha256:1c824... | NO | 6 | 2 | 0.6142 | 10.9471 | 0.6163 | 0.1724 | • Resources: This is the section where you define your AWS resources and wire them together. This section is mandatory. |
| sha256:20796... | NO | 9 | 3 | 0.5733 | 10.1006 | 0.5645 | 0.0920 | This section looks at securing AWS infrastructure and the application. As the AWS security model is a shared one where Amazon is responsible for the security of the infrastructure such as facilities, hardware, network and some software like virtualization, |
| sha256:6bfed... | NO | 5 | 4 | 0.6546 | 10.0823 | 0.6178 | 0.0845 | This is it! The final section where AWS will be configured to host the application for production deployment. The key issues in the production setup include health monitoring of the application, disaster recovery, security, costs, configuration management, |
| sha256:76cf7... | NO | 2 | 5 | 0.7205 | 11.5771 | 0.7051 | 0.0708 | This section introduces you to provisioning the AWS infrastructure in order to deploy and run the A1Electronics e-commerce application securely on AWS. You will also see the code changes required at the application level. By the end of this section, you wi |
| sha256:47705... | NO | 3 | 6 | 0.6188 | 12.1842 | 0.6554 | 0.0635 | To help you get started on Amazon Web Services (AWS), we will end the chapter by walking you through the step-by-step process of creating an AWS account, and describing some of the salient features of the AWS dashboard. |
| sha256:4cdfd... | NO | 17 | 7 | 0.5916 | 6.7153 | 0.4778 | 0.0435 | 3. The next step is to configure the AMI. Apart from filling in the usual suspect's values such as name, most of the other parameters are already discussed in Chapter 3, AWS Components, Cost Model, and Application Development Environments under the Creatin |
| sha256:bb6ac... | NO | 7 | 8 | 0.6077 | 9.7946 | 0.5783 | 0.0380 | This chapter will describe the main AWS components and services. We will also cover strategies to lower your cloud infrastructure costs, and how they influence your architectural decisions. Furthermore, this chapter will discuss the typical characteristics |
| sha256:ad677... | NO | 22 | 9 | 0.5784 | 5.9082 | 0.4455 | 0.0371 | Learning AWS covers basic, intermediate, and advanced features and concepts as they relate to designing, developing, and deploying scalable, highly available, and secure applications on the AWS platform. By sequentially working through the steps in each ch |
| sha256:b2a6b... | NO | 15 | 10 | 0.5990 | 7.2418 | 0.4980 | 0.0299 | Setting up the AWS infrastructure |
| sha256:92763... | NO | 10 | 12 | 0.3944 | 13.7916 | 0.5537 | 0.0170 | mand line script. For the purpose of automation, Amazon provides a command line interface using your favorite language to manage your AWS services. We will now create the complete auto scaling group right from creating an AMI, elastic load balancer and the |
| sha256:7d287... | NO | 8 | 15 | 0.4613 | 12.6810 | 0.5656 | 0.0115 | 2. Reduce the development time and billing cost using the AWS billing and management console.<br><br>3. This is a fast-paced tutorial that will cover application deployment using various tools along with best practices for working with AWS services. |
| sha256:9d665... | NO | 4 | 17 | 0.5404 | 12.8419 | 0.6227 | 0.0109 | ations. Finally, we also cover running packaged applications on the AWS cloud. |

---

### Case: eval_test_v3_022
**Query**: Đoạn code nào chịu trách nhiệm đẩy dữ liệu telemetry từ bên trong ứng dụng ra ngoài?

**Candidate Pool:** 38 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 1

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:16b68... | YES | 1 | 1 | 0.5567 | 19.3340 | 0.9838 | 0.3474 | --> **Giải pháp**: ```OpenTelemetry(OTel)``` gom tất cả vào 1 bộ SDK duy nhất --> output đi đến bất kì backend nào.<br>Components của OTel: <br><br>	+ SDK: thư viện embedded trong service, code emit telemetry qua SDK |
| sha256:c23df... | NO | 7 | 2 | 0.5218 | 5.9904 | 0.5396 | 0.1567 | ### 2.2 **Transport — Buffer Giữa Producer và Consumer**<br><br>**Vấn đề**: nhiều service push telemetry data thẳng vào storage --> ```DB không kịp xử lí --> crash/drop data.``<br>==> **Giải pháp**: Message Queue giữa collection và processing layer |
| sha256:96b44... | NO | 4 | 3 | 0.4341 | 11.8443 | 0.6125 | 0.0024 | 	+ Collector: standalone process nhận data từ SDK, làm transform, và sau đó forward tới backend<br><br>**Architecture choice — Agent layer:**<br><br>&#124; Tool &#124; Đặc điểm &#124; Khi nào dùng &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124; |
| sha256:11837... | NO | 2 | 4 | 0.4600 | 19.8690 | 0.8856 | 0.0016 | Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống  |
| sha256:cc866... | NO | 32 | 5 | 0.4561 | 0.0000 | 0.2809 | 0.0016 | ers, output, and so on. |
| sha256:c7156... | NO | 12 | 6 | 0.2477 | 14.6295 | 0.4760 | 0.0013 | ``` <br>==> Nhờ khả năng xử lý độc lập giữa bên phát và bên nhận (decouple), Kafka đạt throughput cực cao và cho phép nhiều hệ thống cùng khai thác một dòng dữ liệu (multi-consumer) mà không sợ mất mát nhờ cơ chế lưu trữ bền vững (persist data) để sẵn sàng re |
| sha256:f2b17... | NO | 13 | 7 | 0.3939 | 8.4217 | 0.4616 | 0.0010 | ==> Bằng việc hiển thị chi tiết đường đi và thời gian của **request (show path)**, ```Trace``` giúp phát hiện ngay lập tức **điểm nghẽn hệ thống (bottleneck identification)**, nhưng vì phải chứa quá nhiều **operation nhỏ (spans)** nên dữ liệu của nó rất ** |
| sha256:63f8f... | NO | 6 | 8 | 0.3818 | 11.9226 | 0.5530 | 0.0008 | **Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế. |
| sha256:28808... | NO | 11 | 9 | 0.4176 | 8.3139 | 0.4864 | 0.0007 | ==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng |
| sha256:c50d8... | NO | 9 | 10 | 0.4840 | 6.5511 | 0.5117 | 0.0007 | ### 2.1. **Collection**- Lấy data từ service<br><br>**Vấn đề**: mỗi service product có các cách ```log/metric/trace``` khác nhau |
| sha256:44b76... | NO | 10 | 28 | 0.4886 | 6.2616 | 0.5085 | 0.0002 | Infrastructure as code |
| sha256:01f2e... | NO | 8 | 29 | 0.3129 | 13.5469 | 0.5205 | 0.0001 | ==> Theo vết request --> Tìm ra chỗ chậm --> Dữ liệu phình to --> Tốn tiền lưu trữ.<br><br>**Giới hạn**: khi request ở scale lớn %trace sẽ thấp --> cần sampling(1%/0.1%/tail-based). Sampled data --> có thể miss anomaly hiếm<br><br>**Tools**:  |
| sha256:a0cba... | NO | 5 | 31 | 0.2954 | 15.4986 | 0.5587 | 0.0001 | tự động thích ứng với các thay đổi mà không làm gãy đổ (**break**) pipeline của các bên liên quan. |
| sha256:c5838... | NO | 3 | 34 | 0.4312 | 14.3489 | 0.6848 | 0.0001 | &#124; **Khái niệm (Data Contract)** &#124; **Cam kết giữa các team** &#124; Là concept rộng hơn Schema. Producer cam kết chuẩn dữ liệu (vd: field X là string, không null, max 256 chars). Consumer tin tưởng và dựa vào đó để sử dụng. &#124; |

---

### Case: eval_test_v3_024
**Query**: Bảng phân loại các tùy chọn lưu trữ nằm ở đâu?

**Candidate Pool:** 37 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 4

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:9aa9c... | NO | 3 | 1 | 0.4941 | 17.8561 | 0.6080 | 0.0403 | ### 2.4 **Storage**- Lưu ở đâu?<br><br><div style="overflow: auto; max-height: 400px; width: 100%;"><br><br>&#124; Nhóm Storage (Mục đích) &#124; Công cụ &#124; Đặc điểm nổi bật &#124; Hạn chế / Lưu ý &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124; :--- &#124; |
| sha256:734c7... | NO | 15 | 2 | 0.5065 | 0.0000 | 0.3334 | 0.0155 | ° Storage Type: Select General Purpose (SSD): The other options are Provisioned IOPS, which kicks in only if your allocated storage is 100 GB or more, and Magnetic, which is slower. |
| sha256:82ed2... | NO | 19 | 3 | 0.5032 | 0.0000 | 0.3298 | 0.0141 | ata, data that can be aggregated and then kept in a summarized form, data related to online collaboration applications, and so on. This classification can help you choose appropriate solutions for their storage and backup. AWS provides different storage cl |
| sha256:a70bb... | YES | 1 | 4 | 0.2981 | 37.1926 | 0.7076 | 0.0035 | <div style="overflow: auto; max-height: 400px; width: 100%;"><br><br>&#124; Phân loại &#124; Tùy chọn / Khái niệm &#124; Đặc điểm & Lưu ý &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124; |
| sha256:2f525... | NO | 16 | 5 | 0.5059 | 0.0000 | 0.3327 | 0.0033 | Table of Contents |
| sha256:ff75f... | NO | 30 | 6 | 0.3060 | 8.4902 | 0.2531 | 0.0021 | ```<br>Kafka là gì? được hiểu thì kafka như một trạm lưu trữ data, thay vì push data trực tiếp vào storage, thì sẽ thì data sẽ push vào kafka trước khi đi vào storage.<br>	kiến trúc: data ---> kafka ---> storage thay vì data ---> storage<br>``` |
| sha256:a0e72... | NO | 28 | 7 | 0.4698 | 0.0000 | 0.2936 | 0.0019 | kup retention. Select 7 from the dropdown. |
| sha256:95cc4... | NO | 2 | 8 | 0.4939 | 18.0903 | 0.6115 | 0.0016 |   - **2. Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**<br><br>    - 2.1 Collection — Lấy Data Từ Service<br><br>    - 2.2 Transport — Buffer Giữa Producer và Consumer<br><br>    - 2.3 Processing — Transform & Enrich<br><br>    - 2.4 Storage — Lưu Ở Đâu? |
| sha256:25ff2... | NO | 5 | 9 | 0.4716 | 10.1586 | 0.4595 | 0.0015 | ==> **Giải pháp**: Dùng Feature Store làm kho trung tâm. Dữ liệu (features) chỉ cần tính toán và lưu đúng 1 lần, sau đó phân phối nhất quán cho cả quá trình Training lẫn Inference.<br><br>**Architecture**: |
| sha256:28808... | NO | 11 | 10 | 0.4079 | 8.3816 | 0.3617 | 0.0009 | ==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng |
| sha256:8ea81... | NO | 8 | 12 | 0.4809 | 5.4390 | 0.3934 | 0.0006 | ### 1. Các yếu tố ảnh hưởng chi phí (Cost Drivers)<br><br>&#124; Component &#124; Cost driver &#124; Tối ưu cost &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124;<br><br>&#124; **Storage** &#124; GB stored × retention days &#124; Tier: hot/warm/cold; downsample old data &#124; |
| sha256:cc047... | NO | 7 | 18 | 0.5680 | 0.0000 | 0.4000 | 0.0002 | 5. Click on Next: Add Storage to provision persistent storage, as shown in the following screenshot: |
| sha256:b93ee... | NO | 6 | 22 | 0.4297 | 10.3384 | 0.4169 | 0.0001 | #### Table of Contents<br><br>- **I. Data Layer Architecture + Observability Pipeline**<br><br>  - **1. Three Pillars of Observability**<br><br>    - Metric — “Cái gì đang sai?”<br><br>    - Log — “Tại sao sai?”<br><br>    - Trace — “Ở đâu trong hệ thống?”<br><br>    - So sánh nhanh |
| sha256:f8db8... | NO | 9 | 25 | 0.3722 | 11.4005 | 0.3718 | 0.0001 | &#124; &#124; **VictoriaMetrics** &#124; Tương thích Prometheus, scale tốt hơn 10x, retention nhiều tháng/năm. &#124; &#124;<br><br>&#124; &#124; **InfluxDB** &#124; Purpose-built TSDB, xử lý mạnh ở high cardinality (dữ liệu có độ phân mảnh nhãn cao). &#124; &#124; |
| sha256:c50d8... | NO | 10 | 30 | 0.4489 | 6.2423 | 0.3717 | 0.0001 | ### 2.1. **Collection**- Lấy data từ service<br><br>**Vấn đề**: mỗi service product có các cách ```log/metric/trace``` khác nhau |
| sha256:2dfe0... | NO | 4 | 33 | 0.4190 | 15.1774 | 0.4834 | 0.0000 | nặng (heavy)** và gây tốn **chi phí lưu trữ**. |

---

### Case: eval_test_v3_030
**Query**: Cách tối ưu chi phí cho dữ liệu giám sát cũ là gì?

**Candidate Pool:** 38 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 2

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:ee857... | NO | 19 | 1 | 0.6600 | 0.0000 | 0.3526 | 0.2286 | Reducing database costs |
| sha256:8ea81... | YES | 1 | 2 | 0.4485 | 24.7329 | 0.8277 | 0.0133 | ### 1. Các yếu tố ảnh hưởng chi phí (Cost Drivers)<br><br>&#124; Component &#124; Cost driver &#124; Tối ưu cost &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124;<br><br>&#124; **Storage** &#124; GB stored × retention days &#124; Tier: hot/warm/cold; downsample old data &#124; |
| sha256:f1b52... | NO | 22 | 3 | 0.5833 | 0.0000 | 0.3073 | 0.0014 | In a shared database, with a shared schema approach, the costs are minimized, but the complexity of the application is much higher. This model works well for cost conscious customers. However, restoring a customer's data is complicated, as you will be rest |
| sha256:28808... | NO | 2 | 4 | 0.4738 | 22.5969 | 0.7909 | 0.0012 | ==>Nhờ **cấu trúc dữ liệu rất nhẹ** và có thể **dễ dàng tính toán (aggregatable)**, **Metric** cho phép **lưu trữ lâu dài** với **chi phí thấp** và thực hiện **truy xuất (query)** với tốc độ **cực nhanh**. **Nhưng**  ```metric``` chỉ cho biết được ```trạng |
| sha256:88a02... | NO | 17 | 5 | 0.7402 | 0.0000 | 0.4000 | 0.0008 | Cost monitoring and analysis |
| sha256:01f2e... | NO | 14 | 6 | 0.4942 | 8.7623 | 0.4673 | 0.0005 | ==> Theo vết request --> Tìm ra chỗ chậm --> Dữ liệu phình to --> Tốn tiền lưu trữ.<br><br>**Giới hạn**: khi request ở scale lớn %trace sẽ thấp --> cần sampling(1%/0.1%/tail-based). Sampled data --> có thể miss anomaly hiếm<br><br>**Tools**:  |
| sha256:30b0a... | NO | 24 | 7 | 0.5602 | 0.0000 | 0.2937 | 0.0005 | the minimum and maximum number of instances. This helps automate the process of saving money, by turning off unused instances during scale down. |
| sha256:9d8db... | NO | 6 | 8 | 0.4611 | 14.9732 | 0.5984 | 0.0004 | &#124; &#124; **Parquet on S3** &#124; Columnar format, cho phép query thông qua Athena/Spark/DuckDB. &#124; &#124;<br><br>&#124; &#124; **S3 Glacier** &#124; Siêu rẻ ($0.004/GB/tháng). &#124; Lấy dữ liệu ra (retrieve) mất hàng giờ, chỉ dùng cho compliance archive. &#124;<br><br></div><br><br>**Hot/Warm/Cold**: |
| sha256:cab3f... | NO | 11 | 9 | 0.4094 | 12.4357 | 0.5063 | 0.0004 | **vì chi tiết đầy đủ**(order ID, user ID, stack trace) --> **Log** trở nên nặng --> dẫn đến **chi phí lưu trữ** cao --> ngoài ra quá trình **query** sẽ phức tạp do tracing <br><br>==> ```Nhiều chi tiết → Nặng → Tốn tiền lưu & Khó tìm kiếm``` |
| sha256:ae921... | NO | 23 | 10 | 0.5818 | 0.0000 | 0.3065 | 0.0004 |  and database services well, then you would have largely accounted for a big chunk of your expected bill. Using an 80:20 principle can help get you to ballpark cost estimates quickly. |
| sha256:25ff2... | NO | 10 | 11 | 0.3696 | 13.5812 | 0.5106 | 0.0003 | ==> **Giải pháp**: Dùng Feature Store làm kho trung tâm. Dữ liệu (features) chỉ cần tính toán và lưu đúng 1 lần, sau đó phân phối nhất quán cho cả quá trình Training lẫn Inference.<br><br>**Architecture**: |
| sha256:ff84f... | NO | 7 | 12 | 0.5371 | 12.5776 | 0.5852 | 0.0003 | > **Lưu ý:** Nếu dùng SaaS (như Datadog) với cùng workload thì chi phí rơi vào khoảng ~$30-50K/month, nhưng team không tốn thời gian vận hành stack → Đây là bài toán đánh đổi giữa tiền bạc (cost) và thời gian của nhân sự (people time).<br><br>--- |
| sha256:4863c... | NO | 4 | 15 | 0.5492 | 14.3913 | 0.6363 | 0.0002 | ### 2. Chi phí tham khảo cho hệ thống 100 service (Sample Cost)<br><br>&#124; Item &#124; Volume &#124; Cost/month &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124;<br><br>&#124; **Metric** (Prometheus + VictoriaMetrics) &#124; 1M datapoints/sec, 30d retention &#124; $2,000 &#124;<br><br>&#124; **Log** (Loki + S3) &#124; 500GB/day &#124; $4,500 &#124; |
| sha256:11837... | NO | 3 | 18 | 0.4070 | 20.8952 | 0.7101 | 0.0001 | Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống  |
| sha256:63f8f... | NO | 5 | 19 | 0.3764 | 17.2337 | 0.6032 | 0.0001 | **Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế. |
| sha256:2dfe0... | NO | 8 | 31 | 0.3764 | 15.6860 | 0.5657 | 0.0000 | nặng (heavy)** và gây tốn **chi phí lưu trữ**. |
| sha256:c5838... | NO | 9 | 34 | 0.3592 | 15.4519 | 0.5499 | 0.0000 | &#124; **Khái niệm (Data Contract)** &#124; **Cam kết giữa các team** &#124; Là concept rộng hơn Schema. Producer cam kết chuẩn dữ liệu (vd: field X là string, không null, max 256 chars). Consumer tin tưởng và dựa vào đó để sử dụng. &#124; |

---

### Case: eval_test_v3_033
**Query**: Công cụ nào giúp thống nhất các SDK để gửi dữ liệu observability đến mọi backend?

**Candidate Pool:** 38 chunks
**Target chunks:** 1
**Baseline Target Rank:** 1
**BGE Target Rank:** 2

| Chunk ID | Target? | Base Rank | BGE Rank | Dense | BM25 | MinMax | BGE Score | Text |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sha256:96b44... | NO | 3 | 1 | 0.6028 | 17.6467 | 0.6901 | 0.6431 | 	+ Collector: standalone process nhận data từ SDK, làm transform, và sau đó forward tới backend<br><br>**Architecture choice — Agent layer:**<br><br>&#124; Tool &#124; Đặc điểm &#124; Khi nào dùng &#124;<br><br>&#124; :--- &#124; :--- &#124; :--- &#124; |
| sha256:16b68... | YES | 1 | 2 | 0.6912 | 29.3346 | 1.0000 | 0.5488 | --> **Giải pháp**: ```OpenTelemetry(OTel)``` gom tất cả vào 1 bộ SDK duy nhất --> output đi đến bất kì backend nào.<br>Components của OTel: <br><br>	+ SDK: thư viện embedded trong service, code emit telemetry qua SDK |
| sha256:c7d87... | NO | 7 | 3 | 0.5150 | 12.5232 | 0.5148 | 0.0081 | ## 2. **Pipeline Architecture — Data Đi Từ Đâu Đến Đâu**<br><br>data observability đi qua 5 stages: <br><br>```<br>[Service] → [Collection] → [Transport] → [Processing] → [Storage] → [Query/AI]<br>``` |
| sha256:2d5fe... | NO | 9 | 4 | 0.5684 | 8.8727 | 0.4830 | 0.0034 | # **W1-D3: Data Layer Architecture + Observability Pipeline<br><br>--- |
| sha256:25ff2... | NO | 5 | 5 | 0.5006 | 15.0835 | 0.5556 | 0.0030 | ==> **Giải pháp**: Dùng Feature Store làm kho trung tâm. Dữ liệu (features) chỉ cần tính toán và lưu đúng 1 lần, sau đó phân phối nhất quán cho cả quá trình Training lẫn Inference.<br><br>**Architecture**: |
| sha256:b93ee... | NO | 12 | 6 | 0.4055 | 13.1366 | 0.4396 | 0.0024 | #### Table of Contents<br><br>- **I. Data Layer Architecture + Observability Pipeline**<br><br>  - **1. Three Pillars of Observability**<br><br>    - Metric — “Cái gì đang sai?”<br><br>    - Log — “Tại sao sai?”<br><br>    - Trace — “Ở đâu trong hệ thống?”<br><br>    - So sánh nhanh |
| sha256:76971... | NO | 13 | 7 | 0.4127 | 12.0182 | 0.4224 | 0.0016 | &#124; **Công cụ (Tools)** &#124; **Confluent Schema Registry** &#124; Hệ sinh thái Kafka (Hỗ trợ Avro / Protobuf / JSON Schema). &#124;<br><br>&#124; &#124; **AWS Glue Schema Registry** &#124; Giải pháp Native của AWS. &#124;<br><br>&#124; &#124; **Apicurio** &#124; Nền tảng Open-source. &#124; |
| sha256:c7156... | NO | 10 | 8 | 0.3963 | 15.5844 | 0.4822 | 0.0013 | ``` <br>==> Nhờ khả năng xử lý độc lập giữa bên phát và bên nhận (decouple), Kafka đạt throughput cực cao và cho phép nhiều hệ thống cùng khai thác một dòng dữ liệu (multi-consumer) mà không sợ mất mát nhờ cơ chế lưu trữ bền vững (persist data) để sẵn sàng re |
| sha256:11837... | NO | 2 | 9 | 0.5323 | 23.9847 | 0.7632 | 0.0009 | Bằng cách bắt buộc bên phát (**Producer phải register schema**), hệ thống thiết lập một chuẩn cấu trúc cố định cho dòng dữ liệu; nhờ đó bên nhận (**Consumer**) luôn **validate** được dữ liệu chính xác khi đọc, đồng thời cơ chế **versioning** giúp hệ thống  |
| sha256:8210b... | NO | 30 | 10 | 0.5507 | 0.0000 | 0.2873 | 0.0007 | re, using caching, and placing your application and data closer to your end users. |
| sha256:f2b17... | NO | 8 | 18 | 0.3691 | 18.1729 | 0.5133 | 0.0003 | ==> Bằng việc hiển thị chi tiết đường đi và thời gian của **request (show path)**, ```Trace``` giúp phát hiện ngay lập tức **điểm nghẽn hệ thống (bottleneck identification)**, nhưng vì phải chứa quá nhiều **operation nhỏ (spans)** nên dữ liệu của nó rất ** |
| sha256:63f8f... | NO | 4 | 20 | 0.3285 | 24.1734 | 0.6035 | 0.0003 | **Vấn đề**: Việc phải dùng hai hệ thống/đường dẫn khác nhau để tính toán cùng một loại dữ liệu (Batch chậm cho Training và Real-time nhanh cho Inference) sẽ dễ dẫn đến tình trạng lệch pha dữ liệu (Drift) giữa lúc huấn luyện và lúc chạy thực tế. |
| sha256:c5838... | NO | 6 | 26 | 0.4088 | 18.1059 | 0.5438 | 0.0001 | &#124; **Khái niệm (Data Contract)** &#124; **Cam kết giữa các team** &#124; Là concept rộng hơn Schema. Producer cam kết chuẩn dữ liệu (vd: field X là string, không null, max 256 chars). Consumer tin tưởng và dựa vào đó để sử dụng. &#124; |

---
