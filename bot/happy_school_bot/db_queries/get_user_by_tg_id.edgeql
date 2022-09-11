select User {first_name, last_name, status, id, is_teacher, is_student, is_admin, is_parent, tg_id}
filter User.tg_id = <int64>$tg_id
