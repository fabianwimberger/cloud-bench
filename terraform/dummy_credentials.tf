# The OCI and Google providers validate credentials at provider Configure()
# even when no resources of that kind exist — without these fallbacks, every
# benchmark run would need OCI and Google secrets set. The PEM is generated
# fresh per plan via openssl so no static key lives in the repo.
data "external" "dummy_pem" {
  program = ["sh", "-c", "openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:1024 2>/dev/null | jq -Rs '{pem: .}'"]
}

locals {
  _dummy_pem = data.external.dummy_pem.result.pem

  _dummy_gcp_credentials = jsonencode({
    type                        = "service_account"
    project_id                  = "dummy"
    private_key_id              = "0000000000000000000000000000000000000000"
    private_key                 = local._dummy_pem
    client_email                = "dummy@dummy.iam.gserviceaccount.com"
    client_id                   = "0"
    auth_uri                    = "https://accounts.google.com/o/oauth2/auth"
    token_uri                   = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url        = "https://www.googleapis.com/robot/v1/metadata/x509/dummy"
  })
}
