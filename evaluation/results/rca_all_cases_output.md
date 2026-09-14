# RCA: 24 Cases Diagnostics

## holdout_001 (Tags: txt, lexical-anchor-heavy, easy)
**Query:** Why is Trace considered heavy in terms of storage cost?
**Found 2 overlapping chunks:**

### Chunk ID: sha256:f2b17e4ecb4b0928
```text
==> Bằng việc hiển thị chi tiết đường đi và thời gian của **request (show path)**, ```Trace``` giúp phát hiện ngay lập tức **điểm nghẽn hệ thống (bottleneck identification)**, nhưng vì phải chứa quá nhiều **operation nhỏ (spans)** nên dữ liệu của nó rất **
```
- **Dense Score:** 0.4352 (Rank: 20)
- **BM25 Score:** 3.9494 (Rank: 116)

### Chunk ID: sha256:2dfe0bfd00f4510b
```text
nặng (heavy)** và gây tốn **chi phí lưu trữ**.
```
- **Dense Score:** 0.7235 (Rank: 1)
- **BM25 Score:** 8.2205 (Rank: 7)

---

## holdout_002 (Tags: txt, semantic-heavy, hard)
**Query:** Which observability component causes the highest infrastructure bill due to excessive data volume?
**Found 2 overlapping chunks:**

### Chunk ID: sha256:f2b17e4ecb4b0928
```text
==> Bằng việc hiển thị chi tiết đường đi và thời gian của **request (show path)**, ```Trace``` giúp phát hiện ngay lập tức **điểm nghẽn hệ thống (bottleneck identification)**, nhưng vì phải chứa quá nhiều **operation nhỏ (spans)** nên dữ liệu của nó rất **
```
- **Dense Score:** 0.4059 (Rank: 264)
- **BM25 Score:** 0.0000 (Rank: 1436)

### Chunk ID: sha256:2dfe0bfd00f4510b
```text
nặng (heavy)** và gây tốn **chi phí lưu trữ**.
```
- **Dense Score:** 0.5403 (Rank: 17)
- **BM25 Score:** 0.0000 (Rank: 1436)

---

## holdout_003 (Tags: txt, semantic-heavy, medium)
**Query:** How can we pinpoint the exact service causing a delay?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:dc0c04692d76e518
```text
**Đặc điểm**: 

	+ Show path: cho biết được nơi, thời gian request đi

	+ bottleneck identification: biết tốc độ của 1 trace --> cái nào chậm --> ra vấn đề

	+ heavy: 1 trace chứ càng nhiều spans thì giá storage càng cao
```
- **Dense Score:** 0.4956 (Rank: 21)
- **BM25 Score:** 0.0000 (Rank: 1418)

---

## holdout_004 (Tags: txt, lexical-anchor-heavy, easy)
**Query:** What is the limitation of trace sampling in large scale systems?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:01f2ef4571534ec9
```text
==> Theo vết request --> Tìm ra chỗ chậm --> Dữ liệu phình to --> Tốn tiền lưu trữ.

**Giới hạn**: khi request ở scale lớn %trace sẽ thấp --> cần sampling(1%/0.1%/tail-based). Sampled data --> có thể miss anomaly hiếm

**Tools**: 
```
- **Dense Score:** 0.6032 (Rank: 1)
- **BM25 Score:** 11.6572 (Rank: 1)

---

## holdout_005 (Tags: txt, context-dependent, medium)
**Query:** What happens when tail-based sampling misses rare issues?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:01f2ef4571534ec9
```text
==> Theo vết request --> Tìm ra chỗ chậm --> Dữ liệu phình to --> Tốn tiền lưu trữ.

**Giới hạn**: khi request ở scale lớn %trace sẽ thấp --> cần sampling(1%/0.1%/tail-based). Sampled data --> có thể miss anomaly hiếm

**Tools**: 
```
- **Dense Score:** 0.6174 (Rank: 1)
- **BM25 Score:** 13.9069 (Rank: 1)

---

## holdout_006 (Tags: txt, multi-block, medium)
**Query:** Is Loki cheaper than ELK for logs?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:beeeb62d8b0348ad
```text
**Giới hạn**: search trên TB data ==> chậm và đắt ==> không thể grep 1TB log/1 investigate

**Tools**: 

		+ ELK Stack (Elasticsearch + Logstash + Kibana — mạnh nhưng đắt)

		+ Loki (Grafana — chỉ index labels, rẻ hơn 10x)
```
- **Dense Score:** 0.5432 (Rank: 2)
- **BM25 Score:** 11.6070 (Rank: 1)

---

## holdout_007 (Tags: txt, lexical-anchor-heavy, easy)
**Query:** Which logging database is column-oriented and fast for aggregation?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:134ac7baa80af418
```text
		+ Splunk (enterprise — $150-200/GB ingested)

		+ ClickHouse (column-oriented, fast aggregation)
```
- **Dense Score:** 0.5320 (Rank: 14)
- **BM25 Score:** 32.4101 (Rank: 1)

---

## holdout_008 (Tags: txt, lexical-anchor-heavy, easy)
**Query:** Is VictoriaMetrics compatible with Prometheus?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:08084d501681c513
```text
**Tools production**: 

      + Prometheus (open-source, de-facto standard cho K8s)

      + CloudWatch (AWS)

      + Datadog (SaaS)

      + VictoriaMetrics (Prometheus-compatible nhưng scale hơn)
```
- **Dense Score:** 0.5214 (Rank: 2)
- **BM25 Score:** 23.8940 (Rank: 1)

---

## holdout_009 (Tags: txt, ambiguous, medium)
**Query:** Which tool is standard for Kubernetes?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:08084d501681c513
```text
**Tools production**: 

      + Prometheus (open-source, de-facto standard cho K8s)

      + CloudWatch (AWS)

      + Datadog (SaaS)

      + VictoriaMetrics (Prometheus-compatible nhưng scale hơn)
```
- **Dense Score:** 0.4566 (Rank: 2)
- **BM25 Score:** 5.9988 (Rank: 6)

---

## holdout_010 (Tags: txt, semantic-heavy, hard)
**Query:** Why can't we easily search through petabytes of text records?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:beeeb62d8b0348ad
```text
**Giới hạn**: search trên TB data ==> chậm và đắt ==> không thể grep 1TB log/1 investigate

**Tools**: 

		+ ELK Stack (Elasticsearch + Logstash + Kibana — mạnh nhưng đắt)

		+ Loki (Grafana — chỉ index labels, rẻ hơn 10x)
```
- **Dense Score:** 0.4480 (Rank: 3)
- **BM25 Score:** 5.1504 (Rank: 61)

---

## holdout_011 (Tags: txt, context-dependent, medium)
**Query:** Why does storing stack traces increase costs?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:cab3fa398b1192c4
```text
**vì chi tiết đầy đủ**(order ID, user ID, stack trace) --> **Log** trở nên nặng --> dẫn đến **chi phí lưu trữ** cao --> ngoài ra quá trình **query** sẽ phức tạp do tracing 

==> ```Nhiều chi tiết → Nặng → Tốn tiền lưu & Khó tìm kiếm```
```
- **Dense Score:** 0.6196 (Rank: 2)
- **BM25 Score:** 2.9200 (Rank: 120)

---

## holdout_012 (Tags: pdf, semantic-heavy, hard)
**Query:** How can I move a static IP address between virtual machines easily?
**Found 7 overlapping chunks:**

### Chunk ID: sha256:4bf37ab74f21f749
```text
The key pair once assigned to an instance cannot be changed. Make sure you store your private key securely.
```
- **Dense Score:** 0.1610 (Rank: 1178)
- **BM25 Score:** 0.0000 (Rank: 906)

### Chunk ID: sha256:e7ea7d796948b6f0
```text
11. Your EC2 instance will take some time to start. You cannot access it as it does not have a public IP associated with it yet. The EC2 instance is assigned an IP address from the VPC subnet, in this case it is 172.31.16.179. This EC2 instance can be used
```
- **Dense Score:** 0.4566 (Rank: 37)
- **BM25 Score:** 9.2226 (Rank: 14)

### Chunk ID: sha256:a3627bef293f2b1e
```text
 only for communication between the instances in your VPC. Next, create an elastic IP and assign it to the EC2 instance so that it can be accessed via the public internet. Let's have a look at the following screenshot:
```
- **Dense Score:** 0.5632 (Rank: 4)
- **BM25 Score:** 8.6013 (Rank: 19)

### Chunk ID: sha256:b3250120dd49d252
```text
Elastic IPs (EIP)
```
- **Dense Score:** 0.4309 (Rank: 60)
- **BM25 Score:** 0.0000 (Rank: 906)

### Chunk ID: sha256:be2800649feabfd5
```text
EIPs are dynamically remappable static public IP addresses that make it easier to manage EC2 instances. Each EIP can be reassigned to a different EC2 instance when needed. You control the EIP address until you choose to explicitly release it. An EIP is ass
```
- **Dense Score:** 0.5053 (Rank: 14)
- **BM25 Score:** 12.0711 (Rank: 8)

### Chunk ID: sha256:9d006dac83eaa3f8
```text
ociated with your account and not a particular EC2 instance. Since public IP addresses are a scarce resource, you are limited to 5. If you need more EIPs, then you have to apply for your limit to be raised. If you have a large deployment, then an elastic l
```
- **Dense Score:** 0.3724 (Rank: 134)
- **BM25 Score:** 4.1731 (Rank: 120)

### Chunk ID: sha256:e46c4cb47fef114d
```text
oad balancer (ELB part of AWS) is placed in front of all the instances; hence consuming a single EIP.
```
- **Dense Score:** 0.1585 (Rank: 1196)
- **BM25 Score:** 0.7785 (Rank: 659)

---

## holdout_013 (Tags: pdf, lexical-anchor-heavy, easy)
**Query:** What is the maximum number of Elastic IPs allowed per account by default?
**Found 7 overlapping chunks:**

### Chunk ID: sha256:4bf37ab74f21f749
```text
The key pair once assigned to an instance cannot be changed. Make sure you store your private key securely.
```
- **Dense Score:** 0.1734 (Rank: 1471)
- **BM25 Score:** 1.8611 (Rank: 1169)

### Chunk ID: sha256:e7ea7d796948b6f0
```text
11. Your EC2 instance will take some time to start. You cannot access it as it does not have a public IP associated with it yet. The EC2 instance is assigned an IP address from the VPC subnet, in this case it is 172.31.16.179. This EC2 instance can be used
```
- **Dense Score:** 0.4384 (Rank: 51)
- **BM25 Score:** 2.7644 (Rank: 817)

### Chunk ID: sha256:a3627bef293f2b1e
```text
 only for communication between the instances in your VPC. Next, create an elastic IP and assign it to the EC2 instance so that it can be accessed via the public internet. Let's have a look at the following screenshot:
```
- **Dense Score:** 0.4886 (Rank: 14)
- **BM25 Score:** 5.8781 (Rank: 183)

### Chunk ID: sha256:b3250120dd49d252
```text
Elastic IPs (EIP)
```
- **Dense Score:** 0.5890 (Rank: 2)
- **BM25 Score:** 15.7264 (Rank: 2)

### Chunk ID: sha256:be2800649feabfd5
```text
EIPs are dynamically remappable static public IP addresses that make it easier to manage EC2 instances. Each EIP can be reassigned to a different EC2 instance when needed. You control the EIP address until you choose to explicitly release it. An EIP is ass
```
- **Dense Score:** 0.4459 (Rank: 42)
- **BM25 Score:** 1.9807 (Rank: 1117)

### Chunk ID: sha256:9d006dac83eaa3f8
```text
ociated with your account and not a particular EC2 instance. Since public IP addresses are a scarce resource, you are limited to 5. If you need more EIPs, then you have to apply for your limit to be raised. If you have a large deployment, then an elastic l
```
- **Dense Score:** 0.7235 (Rank: 2)
- **BM25 Score:** 5.9002 (Rank: 179)

### Chunk ID: sha256:e46c4cb47fef114d
```text
oad balancer (ELB part of AWS) is placed in front of all the instances; hence consuming a single EIP.
```
- **Dense Score:** 0.3142 (Rank: 394)
- **BM25 Score:** 4.0677 (Rank: 403)

---

## holdout_014 (Tags: pdf, semantic-heavy, hard)
**Query:** Am I billed for reserved IP addresses if the server is turned off?
**Found 4 overlapping chunks:**

### Chunk ID: sha256:5cf06002860d803f
```text
You will be charged for all EIPs not associated with running EC2 instances. It is charged at 0.01$/hour for each EIP that is not associated.

To create an EIP, perform the following steps:
```
- **Dense Score:** 0.4531 (Rank: 56)
- **BM25 Score:** 3.6428 (Rank: 398)

### Chunk ID: sha256:f86d00d81e627a12
```text
1. From the EC2 dashboard, click on Elastic IPs in the navigation pane and then on Allocate New Address. This will assign a new EIP to your account.
```
- **Dense Score:** 0.4968 (Rank: 24)
- **BM25 Score:** 2.2743 (Rank: 983)

### Chunk ID: sha256:a4d31f99e387836e
```text
2. The next step is to associate the EIP to an instance. Click on Associate Address. Type the tag name of the EC2 instance you want to associate this EIP with on Instance. Select the instance, and click on Associate. Let's have a look at the following scre
```
- **Dense Score:** 0.2153 (Rank: 951)
- **BM25 Score:** 3.5343 (Rank: 426)

### Chunk ID: sha256:c1c4b30d8be2fa93
```text
enshot:
```
- **Dense Score:** 0.0366 (Rank: 1828)
- **BM25 Score:** 0.0000 (Rank: 1429)

---

## holdout_015 (Tags: pdf, lexical-anchor-heavy, easy)
**Query:** What is the default parameter group for MySQL 5.6?
**Found 14 overlapping chunks:**

### Chunk ID: sha256:6f2835feb841a574
```text
° Publicly Accessible: This is a good security practice to hide your databases from the Internet. However, access to the DB instance is only possible after remotely logging into the EC2 instances running within the same VPC or by setting up SSH tunnels. Du
```
- **Dense Score:** 0.1259 (Rank: 1328)
- **BM25 Score:** 3.7043 (Rank: 393)

### Chunk ID: sha256:7a53bdc5ef2ee7c6
```text
ring the development phase, this becomes very inconvenient and frustrating to manage database schema changes, viewing data, and debugging. So by keeping things simple, select Yes from the dropdown. For production DB instances, this should be set to No and 
```
- **Dense Score:** 0.3463 (Rank: 76)
- **BM25 Score:** 2.6473 (Rank: 802)

### Chunk ID: sha256:b73f381bbee64fad
```text
a VPC security group that allows access from within the VPC should be created and assigned.
```
- **Dense Score:** 0.2687 (Rank: 276)
- **BM25 Score:** 5.5308 (Rank: 183)

### Chunk ID: sha256:ef1965291660e8c7
```text
° Availability Zone: Select us-east-1a from the drop-down box, which is the same as where our EC2 instances are deployed. It assigns the correct subnet to the DB instance.
```
- **Dense Score:** 0.2012 (Rank: 668)
- **BM25 Score:** 3.6904 (Rank: 401)

### Chunk ID: sha256:5bc4fd4b077d0bfb
```text
° VPC Security Groups: Select sq-RDSSecurityGroup from the list box (created earlier in step 1).

° Database Name: This is the name of the database to which an application connects to. Name it a1ecommerceDb.Name.
```
- **Dense Score:** 0.4794 (Rank: 6)
- **BM25 Score:** 3.3383 (Rank: 510)

### Chunk ID: sha256:bcc48808951e7554
```text
° Database Port: This is the default MySQL port. Do not change the default port number, which is set to 3306.
```
- **Dense Score:** 0.3873 (Rank: 39)
- **BM25 Score:** 14.5718 (Rank: 6)

### Chunk ID: sha256:07f54e1e69239cc3
```text
° Parameter Group: Management of DB engine configuration is done via the parameter group. This allows you to change the default DB configuration. Since we have not created any parameter group, select the default default.mysql5.6.
```
- **Dense Score:** 0.6577 (Rank: 3)
- **BM25 Score:** 26.1708 (Rank: 1)

### Chunk ID: sha256:be7451a54119594a
```text
° Option Group: An option group allows us to set additional features provided by the DB engine to manage the data and the database and to provide additional security to your database. Since, we have not created any option group, select the default default.
```
- **Dense Score:** 0.5248 (Rank: 5)
- **BM25 Score:** 11.4205 (Rank: 10)

### Chunk ID: sha256:d19012f169610a73
```text
mysql.5.6.
```
- **Dense Score:** 0.6868 (Rank: 2)
- **BM25 Score:** 19.9350 (Rank: 2)

### Chunk ID: sha256:e378c4463d126384
```text
° Backup Retention Period: This is the number of days Amazon RDS keeps the automatic backup for the instance. The range is from 1 to 35 days. This helps enable one-click restoration of the data in case of disaster recovery. Selection of 0 days disables bac
```
- **Dense Score:** 0.0941 (Rank: 1557)
- **BM25 Score:** 4.4196 (Rank: 251)

### Chunk ID: sha256:a0e72ee1481ea1a6
```text
kup retention. Select 7 from the dropdown.
```
- **Dense Score:** 0.2471 (Rank: 375)
- **BM25 Score:** 2.4036 (Rank: 937)

### Chunk ID: sha256:888d60d25659e22b
```text
° Backup Window: This is the time slot during which the automatic backups take place. The selected time period should be such during which the database load is least. It is normally set when we deploy the database in production. During the development cycl
```
- **Dense Score:** 0.1858 (Rank: 796)
- **BM25 Score:** 4.2690 (Rank: 270)

### Chunk ID: sha256:89526abab569ac8a
```text
e, this can be set to No Preference.
```
- **Dense Score:** 0.3030 (Rank: 170)
- **BM25 Score:** 0.0000 (Rank: 1440)

### Chunk ID: sha256:5815fb39016af0c3
```text
° Auto Minor Version Upgrade: Amazon RDS will automatically update the DB instance only for minor updates. Select Yes from the dropdown.
```
- **Dense Score:** 0.2226 (Rank: 517)
- **BM25 Score:** 3.3453 (Rank: 507)

---

## holdout_016 (Tags: pdf, lexical-anchor-heavy, medium)
**Query:** Do EC2 instance tags have any semantic value?
**Found 5 overlapping chunks:**

### Chunk ID: sha256:d7e6fa890ac5647a
```text
7. Next, we tag the EC2 instance. Tags do not have any semantic value and are treated purely as strings in a key-value form. You can work using the tags with the AWS management console, EC2 API, and EC2 command line interface tools. Click on Next: Configur
```
- **Dense Score:** 0.7516 (Rank: 1)
- **BM25 Score:** 27.6161 (Rank: 1)

### Chunk ID: sha256:9eeefddbfce3a03e
```text
e Security Group. Let's have a look at the following screenshot:
```
- **Dense Score:** 0.1963 (Rank: 687)
- **BM25 Score:** 3.2438 (Rank: 221)

### Chunk ID: sha256:d3d1e28b45a90414
```text
8. Next, we assign the security group sq-EC2WebSecurityGroup we defined earlier in step 1. Click on the Select an existing security group radio button to view all the available predefined security groups. Select sq- EC2WebSecurityGroup from the list. Click
```
- **Dense Score:** 0.3200 (Rank: 189)
- **BM25 Score:** 0.0000 (Rank: 535)

### Chunk ID: sha256:f474b193d5cb10c8
```text
 on Review and Launch,
```
- **Dense Score:** 0.1245 (Rank: 1304)
- **BM25 Score:** 0.0000 (Rank: 535)

### Chunk ID: sha256:9e626a83a385a689
```text
as shown in the following screenshot:
```
- **Dense Score:** 0.0773 (Rank: 1651)
- **BM25 Score:** 0.0000 (Rank: 535)

---

## holdout_017 (Tags: pdf, context-dependent, medium)
**Query:** What character must the master login name start with?
**Found 11 overlapping chunks:**

### Chunk ID: sha256:1fdf0fafee402133
```text
4. The next step is to configure the RDS instance. The following are the properties:
```
- **Dense Score:** 0.2061 (Rank: 201)
- **BM25 Score:** 3.1993 (Rank: 278)

### Chunk ID: sha256:ca1c827e2eba393a
```text
° License Model: Since we chose MySQL Community Edition,

general-public-license is the only option available.
```
- **Dense Score:** 0.1360 (Rank: 447)
- **BM25 Score:** 1.9724 (Rank: 936)

### Chunk ID: sha256:0a519a9f9ffcf029
```text
° DB Engine Version: This option allows you to select a specific version of MySQL. Choose the latest, unless you have MySQL-specific code that runs for a specific version.
```
- **Dense Score:** 0.1106 (Rank: 577)
- **BM25 Score:** 1.5665 (Rank: 1094)

### Chunk ID: sha256:edc04d393649cb68
```text
° DB Instance Class: This is the same as choosing the EC2 instance type. This will select the virtual server that will run your MySQL database engine; faster DB instances can be chosen as per your database workload after profiling them, db.t2.micro is the 
```
- **Dense Score:** 0.1316 (Rank: 468)
- **BM25 Score:** 2.5749 (Rank: 559)

### Chunk ID: sha256:97d4ee129d012764
```text
only one that is available for the free tier.
```
- **Dense Score:** 0.1384 (Rank: 434)
- **BM25 Score:** 2.2922 (Rank: 769)

### Chunk ID: sha256:d483594ef797107e
```text
° Multi-AZ Deployment: This option is for high availability as discussed earlier. Select No from the drop-down list.
```
- **Dense Score:** 0.0755 (Rank: 811)
- **BM25 Score:** 1.8611 (Rank: 1008)

### Chunk ID: sha256:734c7500e22572b2
```text
° Storage Type: Select General Purpose (SSD): The other options are Provisioned IOPS, which kicks in only if your allocated storage is 100 GB or more, and Magnetic, which is slower.
```
- **Dense Score:** 0.0404 (Rank: 1073)
- **BM25 Score:** 1.5420 (Rank: 1105)

### Chunk ID: sha256:393f16e4b13c2051
```text
° Allocated Storage: You can use the default that is 5 GB. The free tier allows storage up to 20 GB.
```
- **Dense Score:** 0.0435 (Rank: 1059)
- **BM25 Score:** 2.5045 (Rank: 610)

### Chunk ID: sha256:28906c517f1ff16c
```text
° DB Instance Identifier: This is the identifier for the MySQL server database instance, and this identifier is used for defining the DNS entry for the DB instance. Type a1ecommerce in the text field.
```
- **Dense Score:** 0.3523 (Rank: 29)
- **BM25 Score:** 2.9703 (Rank: 330)

### Chunk ID: sha256:b294ce600c5f2a4b
```text
° Master Username: This is the master login name to access the DB instance; it needs to start with a letter. Enter a1dbroot for the master username.
```
- **Dense Score:** 0.7479 (Rank: 1)
- **BM25 Score:** 25.7306 (Rank: 1)

### Chunk ID: sha256:c4a5c634339c6fb5
```text
° Master Password: This is the password for the master username. ° Confirm Password: Type in the master password again.

5. Click on Next Step for advanced settings, as shown in the following screenshot:
```
- **Dense Score:** 0.6612 (Rank: 2)
- **BM25 Score:** 10.0643 (Rank: 7)

---

## holdout_018 (Tags: pdf, semantic-heavy, medium)
**Query:** How do I configure high availability for the relational database?
**Found 11 overlapping chunks:**

### Chunk ID: sha256:1fdf0fafee402133
```text
4. The next step is to configure the RDS instance. The following are the properties:
```
- **Dense Score:** 0.4038 (Rank: 237)
- **BM25 Score:** 8.1822 (Rank: 60)

### Chunk ID: sha256:ca1c827e2eba393a
```text
° License Model: Since we chose MySQL Community Edition,

general-public-license is the only option available.
```
- **Dense Score:** 0.4540 (Rank: 124)
- **BM25 Score:** 1.9724 (Rank: 1077)

### Chunk ID: sha256:0a519a9f9ffcf029
```text
° DB Engine Version: This option allows you to select a specific version of MySQL. Choose the latest, unless you have MySQL-specific code that runs for a specific version.
```
- **Dense Score:** 0.5068 (Rank: 67)
- **BM25 Score:** 2.3281 (Rank: 928)

### Chunk ID: sha256:edc04d393649cb68
```text
° DB Instance Class: This is the same as choosing the EC2 instance type. This will select the virtual server that will run your MySQL database engine; faster DB instances can be chosen as per your database workload after profiling them, db.t2.micro is the 
```
- **Dense Score:** 0.5410 (Rank: 41)
- **BM25 Score:** 6.1196 (Rank: 145)

### Chunk ID: sha256:97d4ee129d012764
```text
only one that is available for the free tier.
```
- **Dense Score:** 0.2605 (Rank: 1093)
- **BM25 Score:** 3.4068 (Rank: 418)

### Chunk ID: sha256:d483594ef797107e
```text
° Multi-AZ Deployment: This option is for high availability as discussed earlier. Select No from the drop-down list.
```
- **Dense Score:** 0.4272 (Rank: 173)
- **BM25 Score:** 9.2030 (Rank: 37)

### Chunk ID: sha256:734c7500e22572b2
```text
° Storage Type: Select General Purpose (SSD): The other options are Provisioned IOPS, which kicks in only if your allocated storage is 100 GB or more, and Magnetic, which is slower.
```
- **Dense Score:** 0.1921 (Rank: 1502)
- **BM25 Score:** 1.5420 (Rank: 1199)

### Chunk ID: sha256:393f16e4b13c2051
```text
° Allocated Storage: You can use the default that is 5 GB. The free tier allows storage up to 20 GB.
```
- **Dense Score:** 0.2714 (Rank: 1014)
- **BM25 Score:** 2.5045 (Rank: 819)

### Chunk ID: sha256:28906c517f1ff16c
```text
° DB Instance Identifier: This is the identifier for the MySQL server database instance, and this identifier is used for defining the DNS entry for the DB instance. Type a1ecommerce in the text field.
```
- **Dense Score:** 0.4376 (Rank: 154)
- **BM25 Score:** 6.9501 (Rank: 97)

### Chunk ID: sha256:b294ce600c5f2a4b
```text
° Master Username: This is the master login name to access the DB instance; it needs to start with a letter. Enter a1dbroot for the master username.
```
- **Dense Score:** 0.3197 (Rank: 667)
- **BM25 Score:** 3.5016 (Rank: 395)

### Chunk ID: sha256:c4a5c634339c6fb5
```text
° Master Password: This is the password for the master username. ° Confirm Password: Type in the master password again.

5. Click on Next Step for advanced settings, as shown in the following screenshot:
```
- **Dense Score:** 0.0562 (Rank: 1890)
- **BM25 Score:** 3.8700 (Rank: 341)

---

## holdout_019 (Tags: pdf, lexical-anchor-heavy, easy)
**Query:** Which security group should be selected for the RDS instance?
**Found 14 overlapping chunks:**

### Chunk ID: sha256:6f2835feb841a574
```text
° Publicly Accessible: This is a good security practice to hide your databases from the Internet. However, access to the DB instance is only possible after remotely logging into the EC2 instances running within the same VPC or by setting up SSH tunnels. Du
```
- **Dense Score:** 0.3999 (Rank: 243)
- **BM25 Score:** 6.3045 (Rank: 210)

### Chunk ID: sha256:7a53bdc5ef2ee7c6
```text
ring the development phase, this becomes very inconvenient and frustrating to manage database schema changes, viewing data, and debugging. So by keeping things simple, select Yes from the dropdown. For production DB instances, this should be set to No and 
```
- **Dense Score:** 0.3069 (Rank: 736)
- **BM25 Score:** 6.8604 (Rank: 172)

### Chunk ID: sha256:b73f381bbee64fad
```text
a VPC security group that allows access from within the VPC should be created and assigned.
```
- **Dense Score:** 0.5238 (Rank: 45)
- **BM25 Score:** 14.9208 (Rank: 2)

### Chunk ID: sha256:ef1965291660e8c7
```text
° Availability Zone: Select us-east-1a from the drop-down box, which is the same as where our EC2 instances are deployed. It assigns the correct subnet to the DB instance.
```
- **Dense Score:** 0.4146 (Rank: 194)
- **BM25 Score:** 8.0045 (Rank: 92)

### Chunk ID: sha256:5bc4fd4b077d0bfb
```text
° VPC Security Groups: Select sq-RDSSecurityGroup from the list box (created earlier in step 1).

° Database Name: This is the name of the database to which an application connects to. Name it a1ecommerceDb.Name.
```
- **Dense Score:** 0.7161 (Rank: 2)
- **BM25 Score:** 7.9322 (Rank: 98)

### Chunk ID: sha256:bcc48808951e7554
```text
° Database Port: This is the default MySQL port. Do not change the default port number, which is set to 3306.
```
- **Dense Score:** 0.2675 (Rank: 1039)
- **BM25 Score:** 6.3894 (Rank: 206)

### Chunk ID: sha256:07f54e1e69239cc3
```text
° Parameter Group: Management of DB engine configuration is done via the parameter group. This allows you to change the default DB configuration. Since we have not created any parameter group, select the default default.mysql5.6.
```
- **Dense Score:** 0.3745 (Rank: 343)
- **BM25 Score:** 6.9445 (Rank: 170)

### Chunk ID: sha256:be7451a54119594a
```text
° Option Group: An option group allows us to set additional features provided by the DB engine to manage the data and the database and to provide additional security to your database. Since, we have not created any option group, select the default default.
```
- **Dense Score:** 0.4535 (Rank: 117)
- **BM25 Score:** 8.8855 (Rank: 54)

### Chunk ID: sha256:d19012f169610a73
```text
mysql.5.6.
```
- **Dense Score:** 0.2169 (Rank: 1410)
- **BM25 Score:** 0.0000 (Rank: 1462)

### Chunk ID: sha256:e378c4463d126384
```text
° Backup Retention Period: This is the number of days Amazon RDS keeps the automatic backup for the instance. The range is from 1 to 35 days. This helps enable one-click restoration of the data in case of disaster recovery. Selection of 0 days disables bac
```
- **Dense Score:** 0.3391 (Rank: 529)
- **BM25 Score:** 7.4880 (Rank: 124)

### Chunk ID: sha256:a0e72ee1481ea1a6
```text
kup retention. Select 7 from the dropdown.
```
- **Dense Score:** 0.2077 (Rank: 1485)
- **BM25 Score:** 2.4036 (Rank: 1016)

### Chunk ID: sha256:888d60d25659e22b
```text
° Backup Window: This is the time slot during which the automatic backups take place. The selected time period should be such during which the database load is least. It is normally set when we deploy the database in production. During the development cycl
```
- **Dense Score:** 0.3216 (Rank: 639)
- **BM25 Score:** 14.8740 (Rank: 3)

### Chunk ID: sha256:89526abab569ac8a
```text
e, this can be set to No Preference.
```
- **Dense Score:** 0.3623 (Rank: 412)
- **BM25 Score:** 2.4663 (Rank: 984)

### Chunk ID: sha256:5815fb39016af0c3
```text
° Auto Minor Version Upgrade: Amazon RDS will automatically update the DB instance only for minor updates. Select Yes from the dropdown.
```
- **Dense Score:** 0.3387 (Rank: 533)
- **BM25 Score:** 9.3507 (Rank: 43)

---

## holdout_020 (Tags: markdown, ambiguous, hard)
**Query:** What are the core features?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:57d9ec5ae0af2744
```text
## Core Features

- High durability

- High availability

- Infinite scaling
```
- **Dense Score:** 0.4988 (Rank: 3)
- **BM25 Score:** 15.5206 (Rank: 1)

---

## holdout_021 (Tags: markdown, lexical-anchor-heavy, easy)
**Query:** What is the GB price for Glacier?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:5abe5420c3c6f49e
```text
### Pricing Model

| Storage Class | Price per GB |

| Standard      | $0.023       |

| Glacier       | $0.004       |
```
- **Dense Score:** 0.7599 (Rank: 1)
- **BM25 Score:** 20.6138 (Rank: 1)

---

## holdout_022 (Tags: markdown, context-dependent, medium)
**Query:** How do I list buckets using Python?
**Found 1 overlapping chunks:**

### Chunk ID: sha256:6f989fabeb734b00
```text
## Usage Example

Below is a Python snippet to access S3:

```python
import boto3

s3 = boto3.client('s3')
response = s3.list_buckets()
```

> Note: Always secure your AWS credentials.
```
- **Dense Score:** 0.3950 (Rank: 2)
- **BM25 Score:** 8.8869 (Rank: 4)

---

## holdout_023 (Tags: markdown, lexical-anchor-heavy, easy)
**Query:** Always secure your AWS credentials.
**Found 1 overlapping chunks:**

### Chunk ID: sha256:6f989fabeb734b00
```text
## Usage Example

Below is a Python snippet to access S3:

```python
import boto3

s3 = boto3.client('s3')
response = s3.list_buckets()
```

> Note: Always secure your AWS credentials.
```
- **Dense Score:** 0.4025 (Rank: 135)
- **BM25 Score:** 16.4860 (Rank: 1)

---

## holdout_024 (Tags: txt, distractor-heavy, hard)
**Query:** Find the total time for the /checkout API call.
**Found 2 overlapping chunks:**

### Chunk ID: sha256:b3179de5ebba987c
```text
```
Trace ID: abc-123
├─ [api-gateway] /checkout                        250ms total
│  ├─ [auth-service] validateToken                 12ms
│  ├─ [cart-service] getCart                       45ms
│  ├─ [payment-service] processPayment             180ms ← S
```
- **Dense Score:** 0.4765 (Rank: 17)
- **BM25 Score:** 17.6347 (Rank: 1)

### Chunk ID: sha256:cb2071f53fc28438
```text
LOW
│  │  ├─ [db-primary] SELECT ... FROM accounts     5ms
│  │  └─ [external-api] stripe.createCharge        170ms ← BOTTLENECK
│  └─ [notification-service] sendEmail             8ms
```
```
- **Dense Score:** 0.4144 (Rank: 60)
- **BM25 Score:** 5.2166 (Rank: 481)

---
