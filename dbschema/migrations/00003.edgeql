CREATE MIGRATION m1cifb5rdmxonibqz74mos773uouxfrysm4d2jf4k3sumsdtbladla
    ONTO m15ozy7f2ao3porthf2wpr5srjur4kcdcektv5le6tcl4aoqxwta7a
{
  ALTER TYPE default::User {
      CREATE REQUIRED LINK identity: ext::auth::Identity {
          SET REQUIRED USING (<ext::auth::Identity>{});
      };
      DROP INDEX ON (.username);
  };
  CREATE GLOBAL default::current_user := (std::assert_single((SELECT
      default::User {
          id
      }
  FILTER
      (.identity = GLOBAL ext::auth::ClientTokenIdentity)
  )));
  ALTER TYPE default::User {
      DROP PROPERTY email;
      DROP PROPERTY hashed_password;
      DROP PROPERTY username;
  };
};
