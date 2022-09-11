CREATE MIGRATION m1gjlfzxdduqktilvijnsm7owlqp4gjnlro444lzpvaahzwwa3wzwq
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
  CREATE TYPE default::Admin EXTENDING default::CreatedUpdated;
  CREATE TYPE default::Class EXTENDING default::CreatedUpdated {
      CREATE REQUIRED PROPERTY name -> std::str;
      CREATE REQUIRED PROPERTY year -> std::int32;
  };
  CREATE TYPE default::Subject EXTENDING default::CreatedUpdated {
      CREATE REQUIRED PROPERTY name -> std::str {
          CREATE CONSTRAINT std::exclusive;
      };
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
      CREATE PROPERTY tg_id -> std::int64 {
          CREATE CONSTRAINT std::exclusive;
      };
  };
  ALTER TYPE default::Admin {
      CREATE REQUIRED LINK user -> default::User {
          ON TARGET DELETE DELETE SOURCE;
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE TYPE default::Parent EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK user -> default::User {
          ON TARGET DELETE DELETE SOURCE;
          CREATE CONSTRAINT std::exclusive;
      };
  };
  CREATE TYPE default::Student EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK user -> default::User {
          ON TARGET DELETE DELETE SOURCE;
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE LINK class -> default::Class {
          ON TARGET DELETE ALLOW;
      };
  };
  CREATE TYPE default::Teacher EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK user -> default::User {
          ON TARGET DELETE DELETE SOURCE;
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE MULTI LINK classes -> default::Class {
          ON TARGET DELETE ALLOW;
      };
      CREATE MULTI LINK subjects -> default::Subject {
          ON TARGET DELETE ALLOW;
      };
  };
  ALTER TYPE default::User {
      CREATE MULTI LINK roles := (.<user);
      CREATE PROPERTY is_admin := (EXISTS (.<user[IS default::Admin]));
      CREATE PROPERTY is_parent := (EXISTS (.<user[IS default::Parent]));
      CREATE PROPERTY is_student := (EXISTS (.<user[IS default::Student]));
      CREATE PROPERTY is_teacher := (EXISTS (.<user[IS default::Teacher]));
  };
  CREATE TYPE default::EntranceQRcode EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK parent -> default::Parent {
          ON TARGET DELETE DELETE SOURCE;
      };
      CREATE REQUIRED PROPERTY is_deleted -> std::bool {
          SET default := false;
      };
      CREATE INDEX ON ((.parent, .is_deleted)) EXCEPT ((.is_deleted = false));
      CREATE REQUIRED MULTI LINK students -> default::Student {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  CREATE TYPE default::ChildEntranceCheck EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK checked_by -> default::User;
      CREATE REQUIRED MULTI LINK qrcode -> default::EntranceQRcode;
      CREATE REQUIRED PROPERTY action -> std::str {
          CREATE CONSTRAINT std::one_of('entrance', 'exit');
      };
      CREATE REQUIRED PROPERTY check_time -> std::datetime {
          SET default := (std::datetime_current());
      };
  };
  CREATE TYPE default::Homework EXTENDING default::CreatedUpdated {
      CREATE REQUIRED LINK assigned_by -> default::Teacher;
      CREATE REQUIRED LINK assigned_to -> default::Student;
      CREATE REQUIRED LINK subject -> default::Subject;
      CREATE REQUIRED PROPERTY assignment -> std::str;
      CREATE REQUIRED PROPERTY deadline -> std::datetime;
      CREATE REQUIRED PROPERTY done_by_student -> std::bool {
          SET default := false;
      };
      CREATE PROPERTY grade -> std::int32 {
          CREATE CONSTRAINT std::min_value(0);
      };
  };
  ALTER TYPE default::Parent {
      CREATE MULTI LINK children -> default::Student {
          ON TARGET DELETE DELETE SOURCE;
      };
  };
  ALTER TYPE default::Student {
      CREATE MULTI LINK parents := (.<children[IS default::Parent]);
  };
};
