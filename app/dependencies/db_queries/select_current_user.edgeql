select User 
    {
         first_name,
         last_name,
         status,
         id,
         is_teacher,
         is_student,
         is_admin,
         is_parent,
     }
filter User.id = global current_user.id
limit 1
