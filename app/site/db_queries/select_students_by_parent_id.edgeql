select Student {
    id,
    updated_at,
    created_at,
    user: {
        id,
        first_name,
        last_name,
        status
    },
    class_: {
        id,
        updated_at,
        created_at,
        name,
        year
    }
} filter .parents.user.id = <uuid>$parent_user_id
