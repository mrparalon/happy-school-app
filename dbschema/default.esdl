using extension auth;
module default {
    abstract type CreatedUpdated{
        required property created_at -> datetime {
            default := datetime_current()
        }
        required property updated_at -> datetime {
            default := datetime_current()
        }

    }
    global current_user := (
        assert_single((
          select User { id }
          filter .identity = global ext::auth::ClientTokenIdentity
        ))
    );
    type User extending CreatedUpdated {
        identity: ext::auth::Identity;
        required property first_name -> str;
        required property last_name -> str;
        required email -> str {
            constraint exclusive;
        };
        required property status -> str;
        property tg_id -> int64 {
            constraint exclusive;
        };
        property is_parent := exists (.<user[is Parent]);
        property is_teacher := exists (.<user[is Teacher]);
        property is_student := exists (.<user[is Student]);
        property is_admin := exists (.<user[is Admin]);
        multi link roles := .<user;
    }
    type Admin extending CreatedUpdated {
        required link user -> User {
            constraint exclusive;
            on target delete delete source;
        };
    }
    type Class extending CreatedUpdated  {
        required property year -> int32;
        required property name -> str;
    }
    type Parent extending CreatedUpdated {
        required link user -> User {
            constraint exclusive;
            on target delete delete source;
        };
        multi link children -> Student {
            on target delete delete source;
        };
    }
    type Student extending CreatedUpdated {
        required link user -> User {
            constraint exclusive;
            on target delete delete source;
        };
        link class_ -> Class {
            on target delete allow;
        };
        multi link parents := .<children[is Parent];
    }
    type Subject extending CreatedUpdated {
        required property name -> str {
            constraint exclusive;
        };
    }
    type Teacher extending CreatedUpdated {
        required link user -> User {
            constraint exclusive;
            on target delete delete source;
        };
        multi link classes -> Class {
            on target delete allow;
        };
        multi link subjects -> Subject{
            on target delete allow;
        };
    }
    type Homework extending CreatedUpdated {
        required property assignment -> str;
        required link assigned_by -> Teacher;
        required link assigned_to -> Student;
        required link subject -> Subject;
        required property done_by_student -> bool {
            default := false;
        };
        property grade -> int32 {
            constraint min_value(0);
        };
        required property deadline -> datetime;
    }
    type Review extending CreatedUpdated {
        required link reviewed_by -> Teacher;
        required link reviewed_to -> Student;
        required property review -> str;
        required engagement -> int32 {
            constraint min_value(1);
            constraint max_value(5);
        };
        required focus -> int32 {
            constraint min_value(1);
            constraint max_value(5);
        };
    }
    type EntranceQRcode extending CreatedUpdated {
        required multi link students -> Student {
            on target delete delete source;
        };
        required link parent -> Parent {
            on target delete delete source;
        };
        required property is_deleted -> bool {
            default := false;
        }
        index on ((.parent, .is_deleted)) except (.is_deleted = false)
    }
    type ChildEntranceCheck extending CreatedUpdated {
        required multi link qrcode -> EntranceQRcode;
        required property check_time -> datetime {
            default := datetime_current() 
        };
        required property action -> str {
            constraint one_of('entrance', 'exit')
        }
        required link checked_by -> User;
    }
}
