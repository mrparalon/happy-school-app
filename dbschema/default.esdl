module default {
    abstract type CreatedUpdated{
        required property created_at -> datetime {
            default := datetime_current()
        }
        required property updated_at -> datetime {
            default := datetime_current()
        }

    }
    type User extending CreatedUpdated {
        required property first_name -> str;
        required property last_name -> str;
        required property username -> str {
            constraint exclusive;
        };
        required property hashed_password -> str;
        required property status -> str;
        property email -> str;
        index on (.username);
    }
    type Class extending CreatedUpdated  {
        required property year -> int16;
        required property name -> str;
    }
    type Student extending CreatedUpdated {
        link person -> User;
        link grade -> Class;
    }
    type Subject extending CreatedUpdated {
        required property name -> str;
    }
    type Teacher extending CreatedUpdated {
        link person -> User;
        multi link grades -> Class;
        multi link subjects -> Subject;
    }
    type Homeworks extending CreatedUpdated {
        required property assignment -> str;
        required link assigned_by -> Teacher;
        required link assigned_to -> Student
    }

}
