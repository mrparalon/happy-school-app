select EntranceQRcode {
    students: {
        user: {
            first_name,
            last_name
        }
    }
}
filter .parent.user.id = <uuid>$parent_user_id and
.is_deleted = false

