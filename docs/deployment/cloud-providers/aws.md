# Deploying on AWS

## EC2 Instance Setup

1. Launch an Instance.
2. Choose **Debian 12 (Bookworm)** AMI.
3. Select instance type (t3.small minimum recommended).
4. Configure Security Group:
    * Allow SSH (port 22 initially).
    * Allow specific application ports (e.g., 80, 443).

## Post-Launch

1. SSH into your instance:

    ```bash
    ssh admin@your-instance-ip
    ```

2. Run the Quick Install script.
