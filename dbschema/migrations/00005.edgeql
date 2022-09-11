CREATE MIGRATION m1cdwjtvvka2o3qvmffhfrsvqjstgug4cpc7uksjld6rgjztjbdqyq
    ONTO m1zudhxixvrblvcqtczcsizb662lwfscdr3pzbl2asso2y3edt34hq
{
  ALTER TYPE default::User {
      CREATE REQUIRED PROPERTY email: std::str {
          SET REQUIRED USING (<std::str>{'test@example.com'});
          CREATE CONSTRAINT std::exclusive;
      };
  };
};
