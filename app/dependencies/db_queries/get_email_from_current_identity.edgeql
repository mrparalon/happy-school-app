select ext::auth::EmailFactor {
  email,
} filter .identity = global ext::auth::ClientTokenIdentity
