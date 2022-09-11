WITH
email_factor := (assert_single((select ext::auth::EmailFactor {identity} filter .email = <str>$email))),
new_parent := (INSERT Parent{
    user := (INSERT User {
    first_name := <str>$first_name,
    last_name := <str>$last_name,
    email := <str>$email,
    status := "active",
    identity := email_factor.identity,
    })
} )
SELECT new_parent {
    id,
    updated_at,
    created_at,
    user: {
        id,
        first_name,
        last_name,
        status
    }
};
