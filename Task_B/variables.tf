# # variable "region" {
# #     description = "AWS region"
# #     default = "us-west-2"
# # }
# variable "db_password" {
#   description = "Password used to connect to PosgtreSQL database"
#   nullable = false
#   default = "testpass123!"
#   sensitive = true
# }
#
# variable "db_username" {
#   description = "Username used to connect to PosgtreSQL database"
#   nullable = false
#   default = "postgres"
#   sensitive = true
# }
#
# # RDS-DB Variables
# variable "deployment_name" {
#   description = "The name of the database deployment."
#   type = string
#   default = "adsum-app-postgres-dev"
# }