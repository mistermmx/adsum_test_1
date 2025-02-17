
# Adsum Take-Home Assessment

A quick guide on how to deploy this project.




## Installation

Before you will be able to use this project, you will need to:

### 1. Set up AWS CLI
This is to set your AWS Access key and AWS Secret key.
Download an install AWS CLI.

You can find the installation file for your OS here:
https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html


Once installed, run the following in your terminal
```bash
  aws configure
```

This will show the following:
```bash
  AWS Access Key ID [None]:  <Paste your Access Key ID here>
  AWS Secret Access Key [None]: <Paste your Secret Access Key here>
  Default region name [None]: <paste your AWS region here. I used 'us-west-2'>               
  Default output format [None]: <Leave blank>
```
Paste your AWS credentials as required.

Now your AWS credentials are set up. This will allow Terraform to access AWS and create the necessary infrastructure.

### 2. Install Terraform
Download Terraform from https://developer.hashicorp.com/terraform/install?product_intent=terraform.

Install Terraform using this guide for your OS: https://spacelift.io/blog/how-to-install-terraform


Verify that your Terraform installation is working by running this command in your terminal:
```bash
  terraform -version
 ```

If your installation was successful, you should see something like this:
```bash
  Terraform v1.105
  on windows_amd64 
 ```

### 3. Create AWS resources using Terraform
```Note: You can also watch  "Task_C/Demo Video.mkv" for a demonstration of the below.```


Open the ```Task_B``` directory of the project in your terminal.

Run the following command:
```bash
terraform init
```

If successful, run the next command:
```bash
terraform plan
```

If the planning was successful, we can now go ahead and create the AWS infrastructure for real.
Run the following command:
```bash
terraform apply
```

It could take up to 10 minutes for everything to be created on AWS.
Once complete, log onto the AWS console and verify that your new S3 Bucket, Secret, and RDS database have been created.

### 4. Create an Airflow container in Docker
Download and install Docker Desktop from https://www.docker.com/.

Once installed, we can now create our Airflow container.

Open the ```Task_A ``` directory of the project in your terminal.

Run the following in your terminal:

```bash
docker compose up
```

This will now create and run the Airflow container.

After a minute or so, you can access Airflow in your browser using this link:

http://localhost:8081/


It will ask you for a username and password.

The username is ```admin```

The password can be found in ```Task_A\airflow\standalone_admin_password.txt``` (Created after we ran the 'docker compose up' command)

### Done! 

You can now run the Airflow DAG in your browser from http://localhost:8081/.