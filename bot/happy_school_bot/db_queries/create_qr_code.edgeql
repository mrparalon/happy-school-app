insert EntranceQRcode {
    students := (
        select Student filter .id in array_unpack(<array<uuid>>$student_ids)
    ),
    parent := (
        select Parent filter .user.id = <uuid>$parent_user_id
    )
} 
