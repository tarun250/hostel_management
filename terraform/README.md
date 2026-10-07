# Terraform: VPC + EKS for HostelHub

Creates a VPC (2 public + 2 private subnets in 2 AZs, IGW, optional single NAT) and an EKS cluster with one managed node group. Uses the official `terraform-aws-modules/vpc` and `terraform-aws-modules/eks` modules.

## Use

```bash
aws configure                 # or export AWS_PROFILE=...  (no keys in this repo)
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out tfplan
terraform apply tfplan
aws eks update-kubeconfig --region ap-south-1 --name hostelhub-eks
```

Tear down when done (EKS + NAT cost money by the hour):

```bash
terraform destroy
```

## Notes

- `enable_nat_gateway = false` skips the NAT gateway and puts nodes in public subnets. Cheaper for a demo.
- Narrow `cluster_endpoint_public_access_cidrs` to your own IP.
- State is local by default. An S3 backend block is in `versions.tf`, commented out.
