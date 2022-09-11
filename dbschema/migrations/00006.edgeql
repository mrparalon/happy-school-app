CREATE MIGRATION m14rqksyvduxayjbrqr2rc5he666eklp2aiznukhp5yotjwb2dw3oq
    ONTO m1cdwjtvvka2o3qvmffhfrsvqjstgug4cpc7uksjld6rgjztjbdqyq
{
  ALTER TYPE default::Student {
      ALTER LINK class {
          RENAME TO class_;
      };
  };
};
