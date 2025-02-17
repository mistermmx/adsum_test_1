
# Description

My evaluation and discussion of my Adsum take-home assessment project.



## FAQ

 

### How it scales (e.g., auto-scaling, load balancing).

Due to the time constraints for this assessment, these considerations were not implemented.

However, given more time, I would approach scaling this project as follows:

○ Use AWS's **Managed Workflows for Apache Airflow (MWAA)**. Instead of manually managing infrastructure, MWAA provides a scalable, secure, and fully managed Airflow service.

○ Alternatively, deploy Airflow to a Kubernetes (KES) cluster, where different Airflow workers handle different groups of DAGs.

○ Instead of passing data between DAG tasks using X-COM, make use of S3 to store intermediate data and only pass the S3 object reference via X-COM.

○ Implement a message queue like RabbitMQ or Celery to trigger on-demand DAGs.
This can be behind a load balancer to ensure that resources are split as required.

○ Use **KubernetesExecutor** or **CeleryExecutor** for scaling.
- With **KubernetesExecutor**, each task runs in its own dedicated Kubernetes pod, providing elastic scalability.
    
- Or, if using, **CeleryExecutor**: Use AWS **SQS** queues or RabbitMQ to handle large-scale task scheduling.


○ Use an **AWS S3 bucket** for storing DAGs. This will allow for centralized DAG management and easy scaling of worker nodes. Leverage S3 bucket versioning for tracking changes in DAGs.

○ Run Airflow components (Scheduler, Webserver, Workers) as highly available services (e.g. multiple schedulers) within an **Auto Scaling Group (ASG)** in EC2 or via **EKS**.  Utilize an **Elastic Load Balancer (ELB)** to distribute requests to the Airflow UI across webserver nodes.

○ Use an **Application Load Balancer (ALB)** to distribute Airflow web UI traffic across multiple Airflow web servers. This ensures high availability during peak loads




### Security best practices (IAM roles, encryption, logging).

○ Random credentials for the database are created by Terraform at runtime and stored on AWS Secrets Manager.
Thus there are no hardcoded credentials anywhere in the code, and the only way to get access to those credentials would be to access the AWS Secrets manager.

○ The Postgres database is created with audit logging enabled, so we can see who connected, from which IP, and what commands were run.

○ In Airflow, Whenever passing data from one Task to another, the data is encrypted. This ensures that no unencrypted data is accidentally logged or viewable in Airflow's X-COM logger.

○ Enable **SSO (Single Sign-On)** using AWS Cognito, Okta, or any enterprise identity provider via **OAuth** or **LDAP**.

○ Use **RBAC (Role-Based Access Control)** features provided by Apache Airflow to restrict permissions based on user roles (e.g., Admin, Viewer)

○ Use SSL/TLS for secure communication between components (e.g., Webserver, Scheduler, and Workers).
    
○ Enable S3 bucket server-side encryption for DAG file storage (`AES-256` or `KMS keys`).

○ Run all Airflow-related components in a **VPC** to avoid public exposure:
- Use private subnets for Airflow Workers, Scheduler, and RDS.
- Configure S3 Gateway endpoints for secure access.




### How errors & failures are handled

I admittedly did not spend a lot of time on error handling for this project.
What I did implement:

○ The SQL operations are all run in transactions, so any failure would result in the entire operation being rolled back to prevent partial data loads.

○ When commiting DAG changes to Github, the custom Github Action will lint the changes and throw an error if the DAG does not pass pep-8 standards.




## Related

I found this resource rather insightful. It details Shopify's lessons learned while upscaling their Airflow system. 
- https://shopify.engineering/lessons-learned-apache-airflow-scale