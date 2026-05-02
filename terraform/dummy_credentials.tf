# The OCI and Google providers validate credentials at provider Configure()
# even when no resources of that kind exist — without these fallbacks, every
# benchmark run would need OCI and Google secrets set. The PEM below is a
# throwaway 1024-bit RSA key generated for this purpose only.
locals {
  _dummy_pem = <<EOT
-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAMZix/vhzC6c5GSK
iljLDC6Iwk91hRdJ0zCDc2gJxe0NdnCkFIZPBgkkcvAmCI+d9OxEH6emL800iULa
kwEu7sZQqj8IKnf4IdTFp+s/JpBigFbvOtsnapvbmnn4ogypk51XQHTbzwiSynF6
MEMJ0tJIe8em40YYef8h9nsnjvh/AgMBAAECgYBvIuN5nfLuogHouRvrxkQaxY5l
SSa39ymSYfGC9QamWAZj7+d3nkl5Uav6ELR3EDwnJ7q8BoN859OFWkFERnCIN3ph
lfF/3u9Qlqp5qPDv3FpiFs/CbI+y22UCR8l6eDwYVANx3rWul62RyF9eb7yPMoIr
YVHp7NH7LG26nDAz8QJBAPJVqyz+SsuljtLoxNKhuX/A2pG92s9dgM998O7e/1jU
iKIRy/2nH1BkzyUyUrZqegdRuzt7TJheUMfrqi02x8sCQQDRkquIl8hCmE6qFR9m
PTym59PS6V0/XddKs03HD8dzJXc/MJlRPQecCdVxcmvHX18GUW6H2KH49i5pYEu6
WzOdAkBHFJfD98bKmwIcnQf2XFeDwHab3xtKTbvVoLRF7ITrclOtbhjuitGljBwy
ZeNa/DpU4UVQ+iaKXsfFDDv7TSEnAkEAsKRmbqg4hGEqFNPe9mbxI2FNun02On3X
REBjc0CKhTR0EU/eOootSslDHe8qhw6M4p9qgZgH1fdyYSFoUvgiRQJAedERaXEA
RlJwtWWs+iVibMHc7kId2iD/HFhn9FHku2nbyZaFTB24jxm1sBNLInRlhtVABlr3
DqBrMQ5gOYM2fg==
-----END PRIVATE KEY-----
EOT

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
