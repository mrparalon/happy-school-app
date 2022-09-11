select assert_single(
(
     select User 
        {
             first_name,
             last_name,
             status,
             id,
             is_teacher,
             is_student,
             is_admin,
         }
    filter User.email = <str>$email
)
)
