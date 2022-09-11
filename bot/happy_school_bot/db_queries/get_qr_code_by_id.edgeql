select EntranceQRcode{
    students: {
        id,
        updated_at,
        created_at,
        user: {
            id,
            first_name,
            last_name,
            status
        },
        parents: {
            user: {
               tg_id 
            }
        }
    },
    parent: {
        id,
        updated_at,
        created_at,
        user: {
            id,
            first_name,
            last_name,
            status,
            tg_id
        }
    }
}
filter .id = <uuid>$qr_code_id and .is_deleted = false

