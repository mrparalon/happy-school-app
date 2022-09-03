CREATE MIGRATION m1jrx44l5xl7xaws3pcnr6opjpjzlqmcwauakozwhbzb5g7dzgg2yq
    ONTO initial
{
  CREATE ABSTRACT TYPE default::CreatedUpdated {
      CREATE REQUIRED PROPERTY created_at -> std::datetime {
          SET default := (std::datetime_current());
      };
      CREATE REQUIRED PROPERTY updated_at -> std::datetime {
          SET default := (std::datetime_current());
      };
  };
  CREATE TYPE default::Class EXTENDING default::CreatedUpdated {
      CREATE REQUIRED PROPERTY name -> std::str;
      CREATE REQUIRED PROPERTY year -> std::int16;
  };
  CREATE TYPE default::User EXTENDING default::CreatedUpdated {
      CREATE REQUIRED PROPERTY username -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE INDEX ON (.username);
      CREATE PROPERTY email -> std::str;
      CREATE REQUIRED PROPERTY first_name -> std::str;
      CREATE REQUIRED PROPERTY hashed_password -> std::str;
      CREATE REQUIRED PROPERTY last_name -> std::str;
      CREATE REQUIRED PROPERTY status -> std::str;
  };
  CREATE TYPE default::Student EXTENDING default::CreatedUpdated {
      CREATE LINK grade -> default::Class;
      CREATE LINK person -> default::User;
  };
  CREATE TYPE default::Subject EXTENDING default::CreatedUpdated {
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  CREATE TYPE default::Teacher EXTENDING default::CreatedUpdated {
      CREATE MULTI LINK grades -> default::Class;
      CREATE MULTI LINK subjects -> default::Subject;
      CREATE LINK person -> default::User;
  };
  CREATE TYPE default::Homeworks EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK assigned_by -> default::Teacher;
      CREATE REQUIRED LINK assigned_to -> default::Student;
      CREATE REQUIRED PROPERTY assignment -> std::str;
  };
};
