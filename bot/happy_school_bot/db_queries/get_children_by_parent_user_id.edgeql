select Student {
    id,
    updated_at,
    created_at,
    user: {
        id,
        first_name,
        last_name,
        status
    }
}
filter .parents.user.id = <uuid>$parent_user_id
